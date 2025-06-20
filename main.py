from flask import Flask, request, render_template_string
from geopy.distance import geodesic
from twilio.rest import Client
import os

app = Flask(__name__)

# 📍 Home coordinates
home_coords = (-23.4175, 29.474083)
geofence_radius = 10  # meters

# 🔐 Known authorized users
authorized_tags = {"Oppie", "Mom", "Dad", "John"}

# Twilio setup
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TO_NUMBER = os.getenv("TO_NUMBER")
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# Track who's inside
inside_users = set()

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head><title>Geofence Monitor</title></head>
<body>
  <h2>Enter Your Name and Send Location</h2>
  <form id="form">
    <input type="text" id="tag" placeholder="Your name or tag" required><br><br>
    <button type="submit">Send Location</button>
  </form>
  <p id="status"></p>
  <script>
    document.getElementById("form").addEventListener("submit", async function (e) {
      e.preventDefault();
      const status = document.getElementById("status");
      const tag = document.getElementById("tag").value;

      if (!navigator.geolocation) {
        status.textContent = "Geolocation not supported.";
        return;
      }

      navigator.geolocation.getCurrentPosition(async (pos) => {
        const data = {
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          tag: tag
        };

        const res = await fetch("/location", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });
        const result = await res.json();
        status.textContent = "📍 Distance: " + result.distance.toFixed(2) + " meters";
      }, () => {
        status.textContent = "Location denied or error.";
      });
    });
  </script>
</body>
</html>
    """)

@app.route('/location', methods=['POST'])
def location():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    tag = data.get("tag", "Unknown")

    if lat is None or lon is None:
        return {"status": "error", "message": "Missing coordinates"}, 400

    distance = geodesic(home_coords, (lat, lon)).meters
    print(f"📍 {tag} at {lat}, {lon} | Distance: {distance:.2f}m")

    if distance <= geofence_radius and tag not in inside_users:
        inside_users.add(tag)

        if tag not in authorized_tags:
            send_alert(f"🚨 UNAUTHORIZED: {tag} entered your geofence!")
        else:
            send_alert(f"✅ {tag} entered your geofence.")

    elif distance > geofence_radius and tag in inside_users:
        inside_users.remove(tag)

    return {"status": "ok", "distance": distance}

def send_alert(message_text):
    message = twilio_client.messages.create(
        body=message_text,
        from_=TWILIO_FROM,
        to=TO_NUMBER
    )
    print("✅ WhatsApp alert sent:", message.sid)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
