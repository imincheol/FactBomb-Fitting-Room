import os
import google.generativeai as genai
import PIL.Image
import io
# Replicate for Flux.1 (Image Gen)
try:
    import replicate
    HAS_REPLICATE = True
except ImportError:
    HAS_REPLICATE = False
    print("Warning: replicate module not found. Image generation will fail.")

import requests 
import json
import base64
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# We still use Gemini for Text Analysis (Fact Bomb)
if os.environ.get("GEMINI_API_KEY"):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY")) 

def get_gemini_model(model_name="gemini-2.5-flash"):
    try:
        return genai.GenerativeModel(model_name)
    except:
        return None

def analyze_mix_mode(user_ratios, model_ratios, user_heads, model_heads, language="ko"):
    """
    Mix Mode: We provide the numeric data (calculated by our Algo).
    Gemini generates the comment based on these numbers.
    """
    if not os.environ.get("GEMINI_API_KEY"):
         return fallback_response(user_heads, model_heads, "[Mix 모드 (Mock)] API 키가 없어서 흉내만 냅니다.")

    lang_instruction = "Korean"
    if language == "vi":
        lang_instruction = "Vietnamese (Tiếng Việt)"
    elif language == "en":
        lang_instruction = "English"

    prompt = f"""
    [Persona]
    You are a brutally honest but trendy K-Fashion Stylist (like a 'Fact Bomber').
    Your audience is trendy people who care about fashion metrics.
    
    [Task]
    Compare the User's stats vs Model's stats and deliver a "Fact Bomb" critique.
    
    [Data]
    - User Heads: {user_heads:.1f} (Real)
    - Model Heads: {model_heads:.1f} (Ideal)
    
    [Rules]
    1. Language: {lang_instruction}. Trendy, Sarcastic style.
    2. Length: MAX 2-3 short sentences. Extremely concise.
    3. Tone: If user is good, praise highly. If bad, roast gently but realistically.
    
    OUTPUT ONLY THE TEXT. NO PREAMBLE.
    """
    
    try:
        model = get_gemini_model("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini Error: {str(e)}"

from google import genai as new_genai

def generate_gemini_image(prompt, reference_images=None):
    """
    Generates an image using Gemini (Nano Banana / gemini-2.5-flash-image).
    Supports reference images.
    """
    if not os.environ.get("GEMINI_API_KEY"):
         return None, "Missing GEMINI_API_KEY in .env"

    try:
        # Initialize the new client
        client = new_genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        print(f"[Gemini] Generating (Nano Banana)... Prompt: {prompt[:50]}...")
        
        # Prepare contents
        contents = [prompt]
        if reference_images:
             # Check if reference images are valid PIL images or supported types
             # The new SDK handles PIL Images directly in the list
             print(f"[Gemini] Including {len(reference_images)} reference images.")
             contents.extend(reference_images)

        # Use gemini-2.5-flash-image (Nano Banana) as per documentation
        model_name = "gemini-2.5-flash-image"

        response = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Note: valid response_modalities for this model might be implicitly TEXT/IMAGE
                # The docs don't strictly require config for basic usage, but we can add it to be safe if needed.
                # For now, following the simple doc example.
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                break
            except Exception as e:
                # Basic check for 429 or Resource Exhausted
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 10 
                        print(f"[Gemini] Rate limit hit. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                raise e
        
        # Extract image from response parts
        if response.parts:
            for part in response.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    print(f"[Gemini] Image generated successfully. Size: {len(image_bytes)} bytes")
                    return base64.b64encode(image_bytes).decode("utf-8"), None
        
        return None, "No image found in Gemini response."

    except Exception as e:
        cleaned_err = str(e).replace('"', "'")
        print(f"[Gemini] Error: {cleaned_err}")
        return None, f"Gemini Error: {cleaned_err}"


def analyze_full_ai_mode(user_img_bytes, model_img_bytes, language="ko"):
    """
    Full AI Mode: Vision Analysis (Gemini) + Image Generation (Imagen 3).
    """
    if not os.environ.get("GEMINI_API_KEY"): 
         return {
             "comment": "[Full AI (Mock)] API Key Missing.",
             "user_heads": 0, "model_heads": 0, "image": None
         }

    try:
        # 1. Vision Analysis (Gemini 2.0 Flash) to understand Scene + Create Gen Prompt
        img_user = PIL.Image.open(io.BytesIO(user_img_bytes))
        img_model = PIL.Image.open(io.BytesIO(model_img_bytes))
        
        model = get_gemini_model("gemini-2.0-flash-exp") # Explicitly use Flash Exp or Pro
        if not model:
             model = get_gemini_model("gemini-1.5-flash") # Fallback
        
        lang_target = "Korean"
        if language == "vi": lang_target = "Vietnamese"
        elif language == "en": lang_target = "English"

        # Update prompt to be compatible with Image-to-Image logic
        analysis_prompt = [
            "Role: High-level Fashion AI Expert specializing in Virtual Try-On.",
            "Task: Create a master prompt for an Image Generator to perform a 'Body Swap' Virtual Fitting.",
            "STEP 1 [User Analysis]: Analyze Image 1 (User). Identify physical specs: estimated Height, Weight, Body Type, and Proportions.",
            "STEP 2 [Model Analysis]: Analyze Image 2 (Model).",
            "   - Identify 'Model Person' specs: Height, Weight, Body Type, Proportions.",
            "   - Identify 'Model Pose': Describe the exact pose of the model.",
            "   - Identify 'Model Clothing': Note the clothing's exact cut, texture, and size.",
            "STEP 3 [Critique]: textual comparison.",
            f"   - Language: {lang_target}",
            "   - Tone: Fact-based, Humorous.",
            "STEP 4 [Gen Prompt Creation]: Write a prompt for the Image Generator following this logic:",
            "   - Logic: Replace the 'Model Person' (specs from Step 2) with the 'User Person' (specs from Step 1).",
            "   - Pose: MUST Maintain the EXACT POSE of Image 2 (Model).",
            "   - Visualization: A person with User's body specs (Height/Weight/Type) standing in Model's exact Pose, wearing Model's Clothes.",
            "   - Quality: Photorealistic, High Resolution.",
            "CONTEXT: This is a 'FactBomb Fitting Room'. The goal is REALITY CHECKS, not beautification.",
            "CRITICAL: Do NOT alter the clothes to fit the user perfectly. If the User is larger/smaller, show the clothes fitting tightly or loosely as they would in real life. Keep the 'Model Clothing' size/shape ORIGINAL.",
            "Return JSON: {",
            "  'user_heads': number, 'model_heads': number,",
            "  'debug_user_info': string (Summary of Step 1 Analysis),",
            "  'debug_model_info': string (Summary of Step 2 Analysis),",
            f"  'comment': string (Fact-based Humorous {lang_target} Critique),",
            "  'gen_prompt': string (The Detailed English Prompt described in Step 4)"
            "}",
            img_user, img_model
        ]
        
        response = model.generate_content(analysis_prompt)
        text = response.text.strip()
        
        # Parse JSON
        import json
        import re
        data = {}
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                # Log Debug Info
                print(f"\n[DEBUG] Gemini Analysis - User: {data.get('debug_user_info', 'N/A')}")
                print(f"[DEBUG] Gemini Analysis - Model: {data.get('debug_model_info', 'N/A')}\n")
            except:
                data = {"comment": text, "gen_prompt": "A stylish person"}
        else:
            data = {"comment": text, "gen_prompt": "A stylish person"}
            
        # 2. Image Generation (Imagen 3)
        gen_prompt = data.get("gen_prompt", "Fashion model wearing stylish clothes")
        
        # Refine prompt for Imagen (Text Only)
        # We rely on Gemini's detailed description in 'gen_prompt'.
        full_gen_prompt = f"{gen_prompt}, photorealistic, 8k, high quality"

        generated_b64, error_msg = generate_gemini_image(full_gen_prompt, reference_images=None)

        
        final_comment = data.get("comment", "Analysis complete.")
        if error_msg:
             final_comment += f"\n\n[System Error] {error_msg}"

        return {
            "user_heads": data.get("user_heads", 0),
            "model_heads": data.get("model_heads", 0),
            "comment": final_comment,
            "image": generated_b64,
            "debug_user_info": data.get("debug_user_info", ""),
            "debug_model_info": data.get("debug_model_info", ""),
            "gen_prompt": data.get("gen_prompt", "")
        }

    except Exception as e:
        return {
             "comment": f"Full AI Error: {str(e)}",
             "user_heads": 0, "model_heads": 0, "image": None,
             "debug_user_info": "", "debug_model_info": "", "gen_prompt": ""
         }

def fallback_response(u_h, m_h, msg_prefix=""):
    return f"{msg_prefix}"
