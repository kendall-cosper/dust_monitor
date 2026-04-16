import serial
from flask import Flask, render_template, jsonify
from sense_hat import SenseHat
from datetime import datetime, jsonify

app = Flask(__name__)
sense = SenseHat()

# Initialize Serial for PMS7003M
# Note: '/dev/ttyS0' or '/dev/serial0' is standard for Pi 4
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1.5)

def get_pms_data():
    """Reads and parses the 32-byte data frame from PMS7003M."""
    try:
        data = ser.read(32)
        if len(data) < 32 or data[0] != 0x42 or data[1] != 0x4d:
            return 0
        # PM2.5 standard concentration is at bytes 12 and 13
        pm25 = data[12] * 256 + data[13]
        return pm25
    except Exception:
        return 0

@app.route('/')
def index():
    # Gather snapshot data for initial page load
    context = {
        "temp": round(sense.get_temperature(), 1),
        "humidity": round(sense.get_humidity(), 1),
        "dust": get_pms_data()
    }
    return render_template('index.html', **context)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
