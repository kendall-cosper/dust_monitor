from flask import Flask, render_template, jsonify
from sense_hat import SenseHat
import serial
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt  # --- NEW IMPORT ---

app = Flask(__name__)
sense = SenseHat()

# --- MQTT SETUP ---
MQTT_BROKER = "mqtt.eclipseprojects.io" # You can change this to your local Pi IP if using Mosquitto
MQTT_TOPIC = "pi/sensors/alerts"
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# --- GLOBAL STORAGE ---
history = []
last_t = 0
last_h = 0
warning_count_24h = 0
warning_threshold_dust = 9
mqtt_triggered = False # Flag to prevent message spam

# Setup Serial for PMS7003M
try:
    ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1.5)
except:
    ser = None

def get_pms_data():
    if not ser: return 0
    try:
        data = ser.read(32)
        if len(data) == 32 and data[0] == 0x42:
            return data[12] * 256 + data[13]
        return 0
    except:
        return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    global last_t, last_h, warning_count_24h, mqtt_triggered
    
    now = datetime.now()
    t = round(sense.get_temperature(), 1)
    h = round(sense.get_humidity(), 1)
    d = get_pms_data()

    history.append({"time": now, "temp": t, "hum": h, "dust": d})
    
    one_day_ago = now - timedelta(hours=24)
    while history and history[0]["time"] < one_day_ago:
        history.pop(0)

    # --- ALERT LOGIC ---
    is_alert = (20 <= t <= 28) or (75 <= h <= 80) or (d > warning_threshold_dust)
    
    if is_alert:
        warning_count_24h += 1
        # --- NEW MQTT PUBLISH LOGIC ---
        if not mqtt_triggered:
            message = f"ALERT: High likelihood of dust detected! Dust: {d}ug, Temp: {t}C, Hum: {h}%"
            mqtt_client.publish(MQTT_TOPIC, message)
            mqtt_triggered = True # Lock until cleared
    else:
        if mqtt_triggered:
            mqtt_client.publish(MQTT_TOPIC, "STATUS: Environment levels have returned to normal.")
            mqtt_triggered = False # Reset lock

    # Prediction Logic
    temp_rising = t > last_t and t < 20
    hum_rising = h > last_h and h < 75
    predict_mites = temp_rising and hum_rising

    max_t = max([x["temp"] for x in history]) if history else t
    max_h = max([x["hum"] for x in history]) if history else h
    max_d = max([x["dust"] for x in history]) if history else d

    last_t = t
    last_h = h

    return jsonify(
        time=now.strftime("%H:%M:%S"),
        temp=t,
        humidity=h,
        dust=d,
        max_temp=max_t,
        max_hum=max_h,
        max_dust=max_d,
        alerts=warning_count_24h,
        predict_mites=predict_mites
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
