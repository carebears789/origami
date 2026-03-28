import os
import cv2
import base64
import numpy as np
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from ultralytics import YOLO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Load base YOLO model - no training needed
model = YOLO('yolov8n.pt')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('process_frame')
def handle_process_frame(data):
    try:
        # Extract base64 image data
        image_data = data.split(',')[1]
        decoded_data = base64.b64decode(image_data)
        np_data = np.frombuffer(decoded_data, np.uint8)
        img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

        if img is None:
            emit('error', {'message': 'Invalid image data'})
            return

        # Run YOLO inference
        results = model.predict(source=img, show=False, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()

        # Extract detected classes for later use in feedback
        detected_classes = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                detected_classes.append(model.names[cls_id])

        # Encode annotated image back to base64
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        result_data = f"data:image/jpeg;base64,{encoded_image}"

        # Emit back the annotated image and the detections
        emit('annotated_frame', {'image': result_data, 'detections': detected_classes})

    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('get_feedback')
def handle_get_feedback(data):
    try:
        import requests
        import json

        origami_name = data.get('origami_name', 'origami')
        detected_classes = data.get('detections', [])
        detected_str = ", ".join(detected_classes) if detected_classes else "nothing"

        prompt = (f"The student is trying to fold an origami '{origami_name}'. "
                  f"The camera currently sees: {detected_str}. "
                  "Give brief, encouraging feedback and advice on what they might need to do next or if they made a mistake. "
                  "Keep it under 3 sentences.")

        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.2:1b",  # Adjust model name as needed for Ollama
            "prompt": prompt,
            "stream": False
        }
        headers = {"Content-Type": "application/json"}

        # Use timeout to prevent hanging if Ollama is not running
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            feedback = result.get('response', 'No feedback received.')
            emit('feedback', {'message': feedback})
        else:
            emit('feedback', {'message': f'Error from Llama API: {response.status_code}'})

    except Exception as e:
        emit('feedback', {'message': f'Error connecting to Llama: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)