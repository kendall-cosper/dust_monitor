from flask import Flask, render_template, jsonify
from sense_hat import SenseHat
import serial
from datetime import datetime, timedelta

app = Flask(__name__)
sense = SenseHat()

# --- GLOBAL STORAGE ---
history = []
last_t = 0
last_h = 0
warning_count_24h = 0
warning_threshold_dust = 9

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
    # Adding 'global' tells Python to use the variables defined at the top
    global last_t, last_h, warning_count_24h
    
    # 1. Capture current time and data
    now = datetime.now()
    t = round(sense.get_temperature(), 1)
    h = round(sense.get_humidity(), 1)
    d = get_pms_data()

    # 2. Update 24h History
    history.append({"time": now, "temp": t, "hum": h, "dust": d})
    
    # Keep only last 24 hours
    one_day_ago = now - timedelta(hours=24)
    while history and history[0]["time"] < one_day_ago:
        history.pop(0)

    # 3. Warning Logic (Temp 20-28 OR Hum 75-80 OR Dust > 9)
    is_alert = (20 <= t <= 28) or (75 <= h <= 80) or (d > warning_threshold_dust)
    if is_alert:
        warning_count_24h += 1

    # 4. Prediction Logic (Heading towards the zones)
    # Temp rising but still below 20 AND Hum rising but still below 75
    temp_rising = t > last_t and t < 20
    hum_rising = h > last_h and h < 75
    predict_mites = temp_rising and hum_rising

    # 5. Calculate Maxes for Sidebar
    max_t = max([x["temp"] for x in history]) if history else t
    max_h = max([x["hum"] for x in history]) if history else h
    max_d = max([x["dust"] for x in history]) if history else d

    # Store current values as "last" for next cycle trend check
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
