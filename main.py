from flask import Flask, request, send_from_directory
from geopy.distance import geodesic
from twilio.rest import Client
import os

app = Flask(__name__)

# ✅ Your real home coordinates (converted from DMS)
home_coords = (-23.4175, 29.474083)
geofence_radius = 50  # in meters

# 🟢 Twilio setup (environment variables)
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TO_NUMBER = os.getenv("TO_NUMBER")

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# Internal flag to avoid duplicate alerts
inside = False

# ✅ Serve the HTML form at root
@app.route('/')
def index():
    return send_from_directory('.', 'send_location.html')

# 📍 Endpoint to receive and process location
@app.route('/location', methods=['POST'])
def location():
    global inside
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")

    if lat is None or lon is None:
        return {"status": "error", "message": "Missing coordinates"}, 400

    distance = geodesic(home_coords, (lat, lon)).meters
    print(f"📍 Received location: {lat}, {lon} | Distance: {distance:.2f} meters")

    if distance <= geofence_radius and not inside:
        inside = True
        print("🚨 Someone entered the geofence!")
        send_alert()
    elif distance > geofence_radius:
        inside = False

    return {"status": "ok", "distance": distance}

# 📤 Send a WhatsApp alert
def send_alert():
    message = twilio_client.messages.create(
        body="🚨 Alert: Someone has entered your geofence at home!",
        from_=TWILIO_FROM,
        to=TO_NUMBER
    )
    print("✅ WhatsApp alert sent:", message.sid)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
