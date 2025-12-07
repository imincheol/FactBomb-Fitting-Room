
import os
import io
import PIL.Image
from dotenv import load_dotenv
from google import genai
from .gemini_service import get_gemini_client, generate_gemini_image

load_dotenv()

# Using Gemini 3
TEXT_MODEL_NAME = "gemini-3-pro-preview"
import json
import re

def generate_lab_image(prompt, base_image_bytes=None):
    """
    Gemini 3 Lab Integration.
    1. Vision Analysis (Gemini 3 Pro) -> JSON (Critique + Gen Prompt)
    2. Image Generation (Gemini 3 Pro Image) -> Real Image
    """
    try:
        client = get_gemini_client()
        if not client:
             return {"comment": "API Key Missing", "image": None}

        # We append the JSON instruction generically to ensure format
        json_instruction = """
        IMPORTANT JSON OUTPUT FORMAT:
        Return valid JSON only.
        {
            "comment": "Your savage Korean critique here (fact bomb).",
            "gen_prompt": "A highly detailed, photorealistic English prompt for Gemini Image Generation. Describe specifically the person, clothes, and background. Start with 'A photorealistic full body shot of...'"
        }
        """
        
        full_inputs = [prompt + json_instruction]
        if base_image_bytes:
            img = PIL.Image.open(io.BytesIO(base_image_bytes))
            full_inputs.append(img)
            
        # 1. Vision / Critique (Gemini 3)
        response = client.models.generate_content(
            model=TEXT_MODEL_NAME,
            contents=full_inputs
        )
        text = response.text.strip()
        
        # Parse JSON
        data = {}
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except:
                data = {"comment": text, "gen_prompt": "Fashion model k-style"}
        else:
             data = {"comment": text, "gen_prompt": "Fashion model k-style"}
             
        # 2. Image Gen (Gemini)
        gen_prompt = data.get("gen_prompt", "Fashion model k-style")
        print(f"[LAB] Generating Image (Gemini) with prompt: {gen_prompt[:30]}...")
        
        # Call Gemini instead of DALL-E
        image_b64, error_msg = generate_gemini_image(gen_prompt)

        
        final_comment = data.get("comment", text)
        if error_msg:
             final_comment += f"\n\n[Lab Error] {error_msg}"

        return {
            "comment": final_comment,
            "image": image_b64
        }
        
    except Exception as e:
        print(f"Lab Error: {e}")
        return {"comment": f"Lab Error: {str(e)}", "image": None}

def run_experiment_flow_a(user_ratios, model_ratios, model_img_bytes):
    """ Flow A: Reality Check """
    prompt = f"""
    [Lab Experiment: Flow A - Reality Check]
    Task: Analyze the Model Image. Imagine if this person had the USER's specific body ratios.
    
    User Metrics:
    - Head Ratio: {user_ratios.get('head', 0.15):.2f}
    - Legs Ratio: {user_ratios.get('legs', 0.5):.2f}
    
    OUTPUT:
    1. 'comment': Korean Fact Bomb. Describe the visual awkwardness (Savage). Max 2 sentences.
    2. 'gen_prompt': English Prompt. Describe the transformed look. "A full body photo of a person wearing [desribe clothes], with [describe body proportions: large head, short legs, etc], photorealistic, high quality."
    """
    return generate_lab_image(prompt, model_img_bytes)

def run_experiment_flow_b(user_ratios, model_ratios, model_img_bytes):
    """ Flow B: Virtual Fitting """
    prompt = f"""
    [Lab Experiment: Flow B - Virtual Fitting]
    Task: Analyze the Model Image (Clothes). Simulate the USER (with specific ratios) wearing these clothes.
    
    User User Spec:
    - Head Proportions: {user_ratios.get('head', 0.15):.2f} 
    - Leg Proportions: {user_ratios.get('legs', 0.5):.2f}
    
    OUTPUT:
    1. 'comment': Korean Fact Bomb. Focus on FIT FAILURES (dragging, pulling). Max 2 sentences.
    2. 'gen_prompt': English Prompt. Describe the fit failure visually. "Full body shot, person wearing [clothes], clothes are too long dragging on floor, or too tight buttons bursting, awkward fit, realistic."
    """
    return generate_lab_image(prompt, model_img_bytes)
