
def analyze_body_proportions(user, model):
    user_head_ratio = user.get('head_stat_ratio', user['head'])
    model_head_ratio = model.get('head_stat_ratio', model['head'])
    
    user_heads = round(1 / user_head_ratio, 1) if user_head_ratio > 0 else 0
    model_heads = round(1 / model_head_ratio, 1) if model_head_ratio > 0 else 0
    
    comments = []
    
    diff_heads = model_heads - user_heads
    if diff_heads > 1.5:
        comments.append(f"충격! 모델은 {model_heads}등신인데, 당신은 {user_heads}등신이군요. 인류가 맞나요?")
    elif diff_heads > 0.5:
        comments.append(f"모델({model_heads}등신)보다 살짝 더 친근한 비율({user_heads}등신)이네요.")
    elif diff_heads < -0.5:
        comments.append(f"와우! 모델({model_heads}등신)보다 당신({user_heads}등신) 비율이 더 좋아요! 모델 하셔야겠는데요?")
    else:
        comments.append(f"오, 모델이랑 거의 비슷한 {user_heads}등신입니다! 옷걸이가 좋으시네요.")

    user_leg_ratio = user['legs'] * 100
    model_leg_ratio = model['legs'] * 100
    diff_legs = model_leg_ratio - user_leg_ratio
    
    if diff_legs > 10:
        comments.append(f"다리 길이가 전체의 {user_leg_ratio:.1f}%... 모델보다 꽤 짧네요. 바지단 수선비 준비하세요.")
    elif diff_legs > 5:
        comments.append("다리가 살짝 짧지만 귀여운 수준입니다.")
        
    return {
        "comment": " ".join(comments),
        "user_heads": user_heads,
        "model_heads": model_heads
    }
