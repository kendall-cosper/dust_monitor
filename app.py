from flask import Flask, render_template, jsonify
from sense_hat import SenseHat
import serial
from datetime import datetime, timedelta

app = Flask(__name__)
sense = SenseHat()

# Global storage for 24h data (1 reading every 2s = 43,200 points per day)
# For efficiency, we'll just store the last 1000 points or use a timed buffer
history = []
warning_threshold = 35
warning_count_24h = 0

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
    except: return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    global warning_count_24h
    t = round(sense.get_temperature(), 1)
    h = round(sense.get_humidity(), 1)
    d = get_pms_data()
    now = datetime.now()

    # Log data
    history.append({"time": now, "temp": t, "hum": h, "dust": d})
    
    # Check for warning trigger
    if d > warning_threshold:
        warning_count_24h += 1

    # Keep only the last 24 hours of data
    one_day_ago = now - timedelta(hours=24)
    while history and history[0]["time"] < one_day_ago:
        history.pop(0)

    # Calculate Max Stats
    max_t = max([x["temp"] for x in history]) if history else 0
    max_h = max([x["hum"] for x in history]) if history else 0
    max_d = max([x["dust"] for x in history]) if history else 0

    return jsonify(
        time=now.strftime("%H:%M:%S"),
        temp=t, humidity=h, dust=d,
        max_temp=max_t, max_hum=max_h, max_dust=max_d,
        alerts=warning_count_24h
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
