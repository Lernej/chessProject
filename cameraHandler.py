from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
import cv2
import threading
from picamera2 import Picamera2, Preview
import time

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)

picam2.start()
time.sleep(2)


app = Flask(__name__)

# HTML page with embedded stream
HTML_TEMPLATE = """
<html>
<head><title>Picamera2 Live Stream</title></head>
<body>
    <h1>PiCamera2 Live Feed</h1>
    <img src="{{ url_for('video_feed') }}" width="640" height="480" />
</body>
</html>
"""

def generate_frames():
    while True:
        # Capture frame for OpenCV
        frame = picam2.capture_array("main")
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Convert to JPEG
        success, encoded_image = cv2.imencode('.jpg', frame)
        if not success:
            continue
            
        # Yield frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def start_stream():
	app.run(host='0.0.0.0', port=5000, threaded=True)

server_thread = threading.Thread(
      target = start_stream,
      daemon = True
)

server_thread.start()

def capture_photo():
	picam2.capture_file("test.jpg")
	
def video_stream():
	while True:
		picam2.capture_file("stream.jpg")


