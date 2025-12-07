
import cv2
import numpy as np
import base64
from .cv_utils import (
    get_landmarks_with_results, detect_face_bounds, calculate_body_ratios,
    draw_skeleton, draw_measurements, warp_image_to_ratio, get_crop_bounds, apply_crop
)

def encode_img(img):
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')

def process_visuals_core(img_user, img_model):
    # 1. Get Pose Landmarks (For Body)
    user_landmarks, user_results = get_landmarks_with_results(img_user)
    model_landmarks, model_results = get_landmarks_with_results(img_model)
    
    # 1.5 Get Face Detection (For Accurate Head Size)
    user_face = detect_face_bounds(img_user)
    model_face = detect_face_bounds(img_model)

    if not user_landmarks or not model_landmarks:
         raise ValueError("Could not detect full body in one of the images")

    # Merge Logic
    if user_face:
        user_landmarks['top_y'] = user_face['top']
        user_landmarks['chin_y'] = user_face['bottom']
        user_landmarks['face_width'] = user_face['raw_box'][2]
        user_head_height = user_face['height']
    else:
        user_landmarks['face_width'] = int(abs(user_landmarks['eye_y'] - user_landmarks['nose_y']) * 4)
        user_head_height = None 

    if model_face:
        model_landmarks['top_y'] = model_face['top']
        model_landmarks['chin_y'] = model_face['bottom']
        model_landmarks['face_width'] = model_face['raw_box'][2]
        model_head_height = model_face['height']
    else:
        model_landmarks['face_width'] = int(abs(model_landmarks['eye_y'] - model_landmarks['nose_y']) * 4)
        model_head_height = None
        
    # 2. Calculate Ratios
    user_ratios = calculate_body_ratios(user_landmarks, precise_head_height=user_head_height)
    model_ratios = calculate_body_ratios(model_landmarks, precise_head_height=model_head_height)

    # 3. Create Debug Images
    img_user_debug = img_user.copy()
    img_model_debug = img_model.copy()
    
    draw_skeleton(img_user_debug, user_results)
    draw_skeleton(img_model_debug, model_results)
    
    draw_measurements(img_user_debug, user_landmarks, user_ratios.get('head_stat_ratio', 0.15), face_box=user_face)
    draw_measurements(img_model_debug, model_landmarks, model_ratios.get('head_stat_ratio', 0.15), face_box=model_face)

    # 4. Warp
    result_img = warp_image_to_ratio(img_model, model_landmarks, user_ratios)
    
    # 5. Process Result Image for Skeleton/Measurements
    res_landmarks, res_results = get_landmarks_with_results(result_img)
    res_face = detect_face_bounds(result_img)
    
    if res_face:
         res_landmarks['face_width'] = res_face['raw_box'][2]
    
    result_img_debug = result_img.copy()
    res_ratios = {}
    res_heads = 0
    
    if res_landmarks:
        draw_skeleton(result_img_debug, res_results)
        
        res_head_height = res_face['height'] if res_face else None
        res_ratios = calculate_body_ratios(res_landmarks, precise_head_height=res_head_height)
        res_head_ratio = res_ratios.get('head_stat_ratio', 0.15)
        res_heads = round(1 / res_head_ratio, 1) if res_head_ratio > 0 else 0
        
        draw_measurements(result_img_debug, res_landmarks, res_ratios.get('head_stat_ratio', 0.15), face_box=res_face)
    
    # 6. AUTO-CROP IMAGES
    user_bounds = get_crop_bounds(img_user_debug, user_results, user_landmarks)
    img_user_debug = apply_crop(img_user_debug, user_bounds)
    
    model_bounds = get_crop_bounds(img_model_debug, model_results, model_landmarks)
    img_model_debug = apply_crop(img_model_debug, model_bounds)
    
    res_bounds = get_crop_bounds(result_img, res_results, res_landmarks)
    if res_bounds:
        result_img = apply_crop(result_img, res_bounds)
        result_img_debug = apply_crop(result_img_debug, res_bounds)

    return {
        "final_result": result_img,
        "final_result_debug": result_img_debug,
        "user_debug": img_user_debug,
        "model_debug": img_model_debug,
        "user_ratios": user_ratios,
        "model_ratios": model_ratios,
        "result_ratios": res_ratios,
        "result_heads": res_heads,
        "user_landmarks": user_landmarks,
        "model_landmarks": model_landmarks
    }

def get_base64_results(processed_data):
    # Converts images in the dict to base64
    return {
        "result_image": encode_img(processed_data['final_result']),
        "result_debug_image": encode_img(processed_data['final_result_debug']),
        "user_debug_image": encode_img(processed_data['user_debug']),
        "model_debug_image": encode_img(processed_data['model_debug']),
    }
