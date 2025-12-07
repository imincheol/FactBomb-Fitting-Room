
def analyze_body_proportions(user, model, language="ko"):
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
