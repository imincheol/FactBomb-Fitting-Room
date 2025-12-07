
import cv2
import numpy as np
import mediapipe as mp

# Initialize MediaPipe
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, model_complexity=1, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def detect_face_bounds(image):
    # Returns {top, bottom, height} or None
    results = face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    if not results.detections:
        return None
    
    h, w, _ = image.shape
    # Use the first detection (usually the main person)
    detection = results.detections[0]
    bboxC = detection.location_data.relative_bounding_box
    
    ymin = int(bboxC.ymin * h)
    height = int(bboxC.height * h)
    
    # Optional: Face detection is usually "tight" (brows to chin). 
    # To get "Head Size" (Crown to Chin), we might want to expand top slightly?
    # Standard Face Detection: Forehead to Chin.
    # To get "Head Size" (Crown to Chin), we need to expand top significantly.
    # Face box is usually brows to chin. Add ~35% for forehead + hair.
    expansion = int(height * 0.35)
    top_y = max(0, ymin - expansion)
    real_height = height + expansion
    
    return {
        'top': top_y,
        'bottom': top_y + real_height,
        'height': real_height,
        'raw_box': (int(bboxC.xmin * w), ymin, int(bboxC.width * w), height)
    }

def get_landmarks_with_results(image):
    results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    if not results.pose_landmarks:
        return None, None
    
    h, w, _ = image.shape
    landmarks = {}
    lm = results.pose_landmarks.landmark
    
    # 0: nose, 2: left_eye, 5: right_eye
    # 11: left_shoulder, 12: right_shoulder, 23: left_hip, 24: right_hip, 27: left_ankle, 28: right_ankle
    
    landmarks['nose_y'] = int(lm[0].y * h)
    landmarks['eye_y'] = int((lm[2].y + lm[5].y) / 2 * h) # Avg of Left/Right Eye
    
    landmarks['shoulder_y'] = int((lm[11].y + lm[12].y) / 2 * h)
    landmarks['hip_y'] = int((lm[23].y + lm[24].y) / 2 * h)
    landmarks['knee_y'] = int((lm[25].y + lm[26].y) / 2 * h) # Avg of Left/Right Knee
    landmarks['ankle_y'] = int((lm[27].y + lm[28].y) / 2 * h)
    
    # Calculate Heel/Foot Bottom (Max Y)
    foot_ys = [lm[29].y, lm[30].y, lm[31].y, lm[32].y]
    valid_foot_ys = [y for y in foot_ys if 0 <= y <= 1.1] # Allow slight overshoot
    if valid_foot_ys:
        landmarks['heel_y'] = int(max(valid_foot_ys) * h)
    else:
        landmarks['heel_y'] = landmarks['ankle_y'] + int(h * 0.03) # Fallback

    # --- Shoulder Width Calculation ---
    x11 = lm[11].x * w
    x12 = lm[12].x * w
    landmarks['shoulder_width_px'] = abs(x11 - x12)
    
    # Hip Width
    x23 = lm[23].x * w
    x24 = lm[24].x * w
    landmarks['hip_width_px'] = abs(x23 - x24)

    # --- Top of Head Estimation ---
    nose_y = landmarks['nose_y']
    eye_y = landmarks['eye_y']
    dist_eye_nose = nose_y - eye_y
    
    if dist_eye_nose > 1:
        top_of_head_y = eye_y - (dist_eye_nose * 2.5)
        landmarks['top_y'] = int(max(0, top_of_head_y))
    else:
        # Fallback
        head_neck_dist = landmarks['shoulder_y'] - landmarks['nose_y']
        landmarks['top_y'] = max(0, landmarks['nose_y'] - (head_neck_dist * 0.8))

    # Add X-bounds for Ruler placement
    xs = [lm.x for lm in results.pose_landmarks.landmark]
    landmarks['min_x'] = int(min(xs) * w)
    landmarks['max_x'] = int(max(xs) * w)
    landmarks['nose_x'] = int(results.pose_landmarks.landmark[0].x * w)

    return landmarks, results

def calculate_body_ratios(landmarks, precise_head_height=None):
    head_segment_len = landmarks['shoulder_y'] - landmarks['top_y']
    torso_len = landmarks['hip_y'] - landmarks['shoulder_y']
    leg_len = landmarks['ankle_y'] - landmarks['hip_y']
    
    total_len = head_segment_len + torso_len + leg_len
    
    # Determine Head Height for Stats
    if precise_head_height:
        stats_head_height = precise_head_height
    else:
        # Fallback to estimation
        eye_to_top = landmarks['eye_y'] - landmarks['top_y']
        if eye_to_top > 0:
            stats_head_height = eye_to_top * 2.0
        else:
            stats_head_height = head_segment_len * 0.6
            
    body_height_px = landmarks['heel_y'] - landmarks['top_y'] # Visible body height
    if body_height_px <= 0: body_height_px = 1

    # Detailed Ratios for 5-segment warping
    chin_y = landmarks.get('chin_y', landmarks['top_y'] + (head_segment_len * 0.6))
    
    h1_head = chin_y - landmarks['top_y']
    h2_neck = landmarks['shoulder_y'] - chin_y
    h3_torso = landmarks['hip_y'] - landmarks['shoulder_y']
    h4_thigh = landmarks['knee_y'] - landmarks['hip_y']
    h5_shin = landmarks['heel_y'] - landmarks['knee_y']
    
    total_5_seg = h1_head + h2_neck + h3_torso + h4_thigh + h5_shin
    if total_5_seg <= 0: total_5_seg = 1
    
    shoulder_width_px = landmarks.get('shoulder_width_px', 100) 
    hip_width_px = landmarks.get('hip_width_px', 100)
    
    face_width = landmarks.get('face_width', stats_head_height * 0.7)
    if face_width <= 0: face_width = 1
    
    shoulder_heads = shoulder_width_px / face_width
    hip_heads = hip_width_px / face_width
    
    face_aspect_ratio = face_width / stats_head_height if stats_head_height > 0 else 0.7

    return {
        'head': head_segment_len / total_len if total_len > 0 else 0.15,
        'torso': torso_len / total_len if total_len > 0 else 0.35,
        'legs': leg_len / total_len if total_len > 0 else 0.5,
        'head_stat_ratio': stats_head_height / body_height_px if body_height_px > 0 else 0.15,
        
        # New 5-segment ratios
        'r1_head': h1_head / total_5_seg,
        'r2_neck': h2_neck / total_5_seg,
        'r3_torso': h3_torso / total_5_seg,
        'r4_thigh': h4_thigh / total_5_seg,
        'r5_shin': h5_shin / total_5_seg,
        
        'shoulder_heads': shoulder_heads,
        'hip_heads': hip_heads,
        'face_aspect_ratio': face_aspect_ratio
    }

def draw_skeleton(image, results):
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )

def draw_measurements(image, landmarks, head_height_ratio, face_box=None):
    h, w, _ = image.shape
    
    px_head_h = int(head_height_ratio * h) if head_height_ratio > 0 else 0
    if px_head_h < 10: return
    
    ruler_x = landmarks.get('min_x', 30 + 50) - 60
    if ruler_x < 10: ruler_x = 10

    top_y = landmarks['top_y']
    bottom_y = landmarks['heel_y']
    
    if face_box:
         fx, fy, fw, fh = face_box['raw_box']
         cv2.rectangle(image, (fx, fy), (fx + fw, fy + fh), (0, 0, 255), 2)
         cv2.putText(image, "Face AI", (fx, fy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    cv2.rectangle(image, (ruler_x, top_y), (ruler_x + 40, top_y + px_head_h), (0, 255, 255), 2)
    cv2.putText(image, "1", (ruler_x + 10, top_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    
    current_y = top_y + px_head_h
    count = 2
    while current_y < bottom_y + px_head_h:
        cv2.line(image, (ruler_x, current_y), (ruler_x + 20, current_y), (0, 0, 255), 2)
        if count % 1 == 0:
             cv2.putText(image, str(count), (ruler_x + 25, current_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        current_y += px_head_h
        count += 1

    cv2.line(image, (ruler_x + 10, top_y), (ruler_x + 10, bottom_y), (255, 0, 0), 2)
    
    nose_x = landmarks.get('nose_x', w//2)
    
    cv2.line(image, (nose_x - 50, top_y), (nose_x + 50, top_y), (0, 255, 255), 2)
    cv2.putText(image, "Top", (nose_x + 55, top_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    chin_y = top_y + px_head_h
    cv2.line(image, (nose_x - 50, chin_y), (nose_x + 50, chin_y), (0, 255, 255), 2)
    cv2.putText(image, "Chin", (nose_x + 55, chin_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    cv2.line(image, (nose_x - 50, bottom_y), (nose_x + 50, bottom_y), (255, 0, 255), 2)
    cv2.putText(image, "Heel", (nose_x + 55, bottom_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

def warp_image_to_ratio(image, landmarks, target_ratios):
    h, w, _ = image.shape
    
    y_top = landmarks['top_y']
    y_chin = landmarks.get('chin_y', int(y_top + (landmarks['shoulder_y'] - y_top) * 0.5))
    y_shoulder = landmarks['shoulder_y']
    y_hip = landmarks['hip_y']
    y_knee = landmarks['knee_y']
    y_heel = landmarks['heel_y']
    
    src_h1 = y_chin - y_top
    src_h2 = y_shoulder - y_chin
    src_h3 = y_hip - y_shoulder
    src_h4 = y_knee - y_hip
    src_h5 = y_heel - y_knee
    
    total_src_h = src_h1 + src_h2 + src_h3 + src_h4 + src_h5
    
    tgt_h1 = int(total_src_h * target_ratios['r1_head'])
    tgt_h2 = int(total_src_h * target_ratios['r2_neck'])
    tgt_h3 = int(total_src_h * target_ratios['r3_torso'])
    tgt_h4 = int(total_src_h * target_ratios['r4_thigh'])
    tgt_h5 = int(total_src_h * target_ratios['r5_shin'])
    
    def get_segment(y_start, h_src, h_tgt):
        if h_src <= 0: return np.zeros((h_tgt, w, 3), dtype=np.uint8)
        segment = image[y_start : y_start + h_src, :]
        if segment.size == 0 or h_tgt <= 0: return np.zeros((h_tgt, w, 3), dtype=np.uint8)
        return cv2.resize(segment, (w, h_tgt), interpolation=cv2.INTER_LINEAR)

    img_top_bg = image[0:y_top, :]
    img_1 = get_segment(y_top, src_h1, tgt_h1)
    img_2 = get_segment(y_chin, src_h2, tgt_h2)
    img_3 = get_segment(y_shoulder, src_h3, tgt_h3)
    img_4 = get_segment(y_hip, src_h4, tgt_h4)
    img_5 = get_segment(y_knee, src_h5, tgt_h5)
    img_bottom_bg = image[y_heel:, :]
    
    result_vertical = np.vstack([img_top_bg, img_1, img_2, img_3, img_4, img_5, img_bottom_bg])
    
    target_ar = target_ratios.get('face_aspect_ratio', 0.7)
    model_face_w = landmarks.get('face_width', w * 0.15)
    tgt_face_w = tgt_h1 * target_ar
    
    if model_face_w > 0:
        scale_x = tgt_face_w / model_face_w
    else:
        scale_x = 1.0
        
    scale_x = max(0.6, min(scale_x, 1.8))
    
    new_w = int(w * scale_x)
    if new_w > 0:
        result = cv2.resize(result_vertical, (new_w, result_vertical.shape[0]), interpolation=cv2.INTER_LINEAR)
        return result
        
    return result_vertical

def get_crop_bounds(image, results, custom_landmarks, padding_x_ratio=0.5, padding_y_ratio=0.2):
    if not results or not results.pose_landmarks:
        return None
        
    h, w, _ = image.shape
    
    xs = [lm.x for lm in results.pose_landmarks.landmark]
    min_x_norm = min(xs)
    max_x_norm = max(xs)
    
    min_x = int(min_x_norm * w)
    max_x = int(max_x_norm * w)
    
    min_y = custom_landmarks.get('top_y', 0)
    max_y = custom_landmarks.get('heel_y', h)
    
    body_w = max_x - min_x
    body_h = max_y - min_y
    
    pad_x = int(body_w * padding_x_ratio)
    pad_y = int(body_h * padding_y_ratio)
    
    pad_x = max(50, pad_x)
    pad_y = max(50, pad_y)

    x1 = max(0, min_x - pad_x)
    x2 = min(w, max_x + pad_x)
    y1 = max(0, min_y - pad_y)
    y2 = min(h, max_y + pad_y)
    
    ruler_x = custom_landmarks.get('min_x', min_x) - 60
    if ruler_x < x1:
        x1 = max(0, ruler_x - 40) 
    
    if x2 <= x1 or y2 <= y1:
        return None
        
    return (y1, y2, x1, x2)

def apply_crop(img, bounds):
    if bounds:
        y1, y2, x1, x2 = bounds
        return img[y1:y2, x1:x2]
    return img
