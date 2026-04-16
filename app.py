from flask import Flask, render_template, jsonify
from sense_hat import SenseHat
import serial
from datetime import datetime

app = Flask(__name__)
sense = SenseHat()

# Setup Serial
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
    t = round(sense.get_temperature(), 1)
    h = round(sense.get_humidity(), 1)
    d = get_pms_data()
    now = datetime.now().strftime("%H:%M:%S")
    
    # This prints in your terminal so you can verify it's working
    print(f"Sending Update -> Time: {now}, Temp: {t}, Dust: {d}")
    
    return jsonify(time=now, temp=t, humidity=h, dust=d)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
