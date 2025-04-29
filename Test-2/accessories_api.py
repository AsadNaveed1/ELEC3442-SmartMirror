from flask import Flask, request, jsonify, Response
import cv2
import numpy as np
import base64
import time
import os
import threading
from simple_accessories import SimpleAccessoryOverlay

app = Flask(__name__)
accessor = SimpleAccessoryOverlay(accessories_dir="accessories")

current_accessory = None
process_lock = threading.Lock()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/apply_accessory', methods=['POST'])
def apply_accessory():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    if 'accessory' not in request.form:
        return jsonify({'error': 'No accessory specified'}), 400
        
    image_file = request.files['image']
    accessory_name = request.form['accessory']
    
    image_bytes = image_file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    result = accessor.apply_accessory(image, accessory_name)
    
    _, buffer = cv2.imencode('.jpg', result)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({
        'image': f'data:image/jpeg;base64,{img_base64}',
        'accessory': accessory_name
    })

@app.route('/set_active_accessory', methods=['POST'])
def set_active_accessory():
    global current_accessory
    
    if not request.json or 'accessory' not in request.json:
        return jsonify({'error': 'No accessory specified'}), 400
        
    accessory_name = request.json['accessory']
    
    if accessory_name.lower() == "none":
        with process_lock:
            current_accessory = None
        return jsonify({'status': 'success', 'accessory': None})
    
    if accessory_name not in accessor.accessories and accessory_name.lower() != "none":
        return jsonify({'error': f'Accessory {accessory_name} not found', 'available': list(accessor.accessories.keys())}), 404
        
    with process_lock:
        current_accessory = accessory_name
        
    return jsonify({
        'status': 'success',
        'accessory': current_accessory
    })

@app.route('/process_frame', methods=['POST'])
def process_frame():
    global current_accessory
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    image_file = request.files['image']
    
    image_bytes = image_file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    with process_lock:
        active_accessory = current_accessory
    
    if active_accessory and active_accessory.lower() != "none":
        result = accessor.apply_accessory(image, active_accessory)
    else:
        result = image
    
    _, buffer = cv2.imencode('.jpg', result)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({
        'image': f'data:image/jpeg;base64,{img_base64}',
        'accessory': active_accessory
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'ok',
        'accessories': list(accessor.accessories.keys()),
        'active_accessory': current_accessory
    })

if __name__ == '__main__':
    app.run(debug=True, port=5002)