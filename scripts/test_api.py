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


# 1. Test Health Check
try:
    health_url = 'http://127.0.0.1:8000/health'
    print(f"Checking health at {health_url}...")
    resp = requests.get(health_url)
    if resp.status_code == 200:
        print("✅ Health Check Passed!")
    else:
        print(f"❌ Health Check Failed: {resp.status_code}")
except Exception as e:
    print(f"❌ Health Check Connection Error: {e}")
    # Don't exit, try the main endpoint anyway just in case

# 2. Test Processing
url = 'http://127.0.0.1:8000/process-baseline'
files = {
    'user_image': ('sample_user.png', user_data, 'image/png'),
    'model_image': ('sample_model.png', model_data, 'image/png')
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        print("✅ Backend Success! Received JSON response.")
        data = response.json()
        
        # Save main result image
        if 'baseline' in data and 'image' in data['baseline']:
            import base64
            img_data = base64.b64decode(data['baseline']['image'])
            output_path = os.path.join(SAMPLES_DIR, 'sample_result.jpg')
            with open(output_path, 'wb') as f:
                f.write(img_data)
            print(f"Saved result image to {output_path}")
            
            # Print analysis
            analysis = data['baseline'].get('analysis', {})
            print("\n--- Analysis Result ---")
            print(f"FactBomb: {analysis.get('fact_bomb')}")
            print(f"User Heads: {analysis.get('user_heads')}")
            print(f"Model Heads: {analysis.get('model_heads')}")
        else:
            print("⚠️ Response format unexpected (missing baseline image)")
            
    else:
        print(f"❌ Backend Failed: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Connection Error: {e}")
