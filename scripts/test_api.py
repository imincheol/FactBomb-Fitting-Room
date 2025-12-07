import requests
import cv2
import numpy as np

import os

# Get the directory of the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(SCRIPT_DIR, '..', 'samples')

# Read generated images
with open(os.path.join(SAMPLES_DIR, 'sample_user.png'), 'rb') as f:
    user_data = f.read()
with open(os.path.join(SAMPLES_DIR, 'sample_model.png'), 'rb') as f:
    model_data = f.read()

url = 'http://127.0.0.1:8000/process-image'
files = {
    'user_image': ('sample_user.png', user_data, 'image/png'),
    'model_image': ('sample_model.png', model_data, 'image/png')
}

try:
    print("Sending request to backend...")
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        print("✅ Backend Success! Received processed image.")
        output_path = os.path.join(SAMPLES_DIR, 'sample_result.jpg')
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Saved result to {output_path}")
    else:
        print(f"❌ Backend Failed: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Connection Error: {e}")
