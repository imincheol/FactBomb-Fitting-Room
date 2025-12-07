
import cv2
import numpy as np
import base64
from .cv_utils import (
    get_landmarks_with_results, detect_face_bounds, calculate_body_ratios,
    draw_skeleton, draw_measurements, warp_image_to_ratio, get_crop_bounds, apply_crop
)

def analyze_body_proportions(user, model, language="ko"):
    """
    Analyzes body proportions and generates a text comment (Fact Bomb).
    Used for Vision Mode (Basic).
    """
    user_head_ratio = user.get('head_stat_ratio', user['head'])
    model_head_ratio = model.get('head_stat_ratio', model['head'])
    
    user_heads = round(1 / user_head_ratio, 1) if user_head_ratio > 0 else 0
    model_heads = round(1 / model_head_ratio, 1) if model_head_ratio > 0 else 0
    
    user_leg_ratio = user['legs'] * 100
    model_leg_ratio = model['legs'] * 100
    
    comments = []
    
    diff_heads = model_heads - user_heads
    diff_legs = model_leg_ratio - user_leg_ratio

    # 1. Head Ratio Comments
    if diff_heads > 1.5:
        if language == "ko":
            comments.append(f"충격! 모델은 {model_heads}등신인데, 당신은 {user_heads}등신이군요. 인류가 맞나요?")
        elif language == "vi":
            comments.append(f"Sốc! Người mẫu tỉ lệ {model_heads} đầu, còn bạn là {user_heads}. Bạn có phải người Trái Đất không?")
        else:
            comments.append(f"Shocking! Model is {model_heads} heads tall, you are {user_heads}. Are you human?")
            
    elif diff_heads > 0.5:
        if language == "ko":
            comments.append(f"모델({model_heads}등신)보다 살짝 더 친근한 비율({user_heads}등신)이네요.")
        elif language == "vi":
            comments.append(f"Tỉ lệ ({user_heads}) thân thiện hơn một chút so với người mẫu ({model_heads}).")
        else:
            comments.append(f"Slightly more friendly ratio ({user_heads}) than the model ({model_heads}).")
            
    elif diff_heads < -0.5:
        if language == "ko":
            comments.append(f"와우! 모델({model_heads}등신)보다 당신({user_heads}등신) 비율이 더 좋아요! 모델 하셔야겠는데요?")
        elif language == "vi":
            comments.append(f"Wow! Tỉ lệ của bạn ({user_heads}) đẹp hơn cả người mẫu ({model_heads})! Bạn nên đi làm người mẫu đi!")
        else:
            comments.append(f"Wow! Your ratio ({user_heads}) is better than the model ({model_heads})! You should be a model!")
            
    else:
        if language == "ko":
            comments.append(f"오, 모델이랑 거의 비슷한 {user_heads}등신입니다! 옷걸이가 좋으시네요.")
        elif language == "vi":
            comments.append(f"Ồ, gần như giống hệt người mẫu ({user_heads})! Dáng chuẩn đấy.")
        else:
            comments.append(f"Oh, almost the same as the model ({user_heads})! Great fit.")

    # 2. Leg Ratio Comments
    if diff_legs > 10:
        if language == "ko":
            comments.append(f"다리 길이가 전체의 {user_leg_ratio:.1f}%... 모델보다 꽤 짧네요. 바지단 수선비 준비하세요.")
        elif language == "vi":
            comments.append(f"Chiều dài chân được {user_leg_ratio:.1f}%... Ngắn hơn nhiều so với mẫu. Chuẩn bị tiền sửa quần nhé.")
        else:
            comments.append(f"Leg length is {user_leg_ratio:.1f}%... Much shorter than model. Prepare for hemming fees.")
            
    elif diff_legs > 5:
        if language == "ko":
            comments.append("다리가 살짝 짧지만 귀여운 수준입니다.")
        elif language == "vi":
            comments.append("Chân hơi ngắn một chút nhưng vẫn dễ thương.")
        else:
            comments.append("Legs are slightly short but cute.")
        
    return {
        "comment": " ".join(comments),
        "user_heads": user_heads,
        "model_heads": model_heads
    }

def encode_img(img):
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')

def process_visuals_core(img_user, img_model):
    """
    Core Logic for 'Vision Mode'.
    Performs face detection, landmark extraction, ratio calculation, and warping.
    """
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
