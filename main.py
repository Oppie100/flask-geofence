from flask import Flask, request, render_template_string
from geopy.distance import geodesic
from twilio.rest import Client
import os

app = Flask(__name__)

# Your home location
home_coords = (-23.4175, 29.474083)
geofence_radius = 10  # meters

# Twilio
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TO_NUMBER = os.getenv("TO_NUMBER")
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# Internal state
inside = False

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head><title>Geofence Test</title></head>
<body>
  <h2>Send Your Location</h2>
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
    global inside
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    tag = data.get("tag", "Unknown")

    if lat is None or lon is None:
        return {"status": "error", "message": "Missing coordinates"}, 400

    distance = geodesic(home_coords, (lat, lon)).meters
    print(f"📍 {tag} at {lat}, {lon} | Distance: {distance:.2f}m")

    if distance <= geofence_radius and not inside:
        inside = True
        send_alert(tag)
    elif distance > geofence_radius:
        inside = False

    return {"status": "ok", "distance": distance}

def send_alert(tag):
    message = twilio_client.messages.create(
        body=f"🚨 Alert: {tag} entered your geofence!",
        from_=TWILIO_FROM,
        to=TO_NUMBER
    )
    print("✅ WhatsApp alert sent:", message.sid)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
