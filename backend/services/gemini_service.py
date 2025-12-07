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
    Generates an image using Gemini 3 Pro Image Preview (or 2.5 Flash Image).
    Can accept reference images (PIL Images) for better context.
    """
    if not os.environ.get("GEMINI_API_KEY"):
         return None, "Missing GEMINI_API_KEY in .env"

    try:
        # Initialize the new client
        client = new_genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        print(f"[Gemini] Generating... Prompt: {prompt[:50]}...")
        
        # Prepare contents
        contents = [prompt]
        if reference_images:
            print(f"[Gemini] Including {len(reference_images)} reference images.")
            contents.extend(reference_images)

        # Use gemini-2.0-flash-exp for image generation (likely better quota/availability)
        model_name = "gemini-2.0-flash-exp"

        response = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=new_genai.types.GenerateContentConfig(
                        response_modalities=["IMAGE"], # Ensure we get an image
                    )
                )
                break
            except Exception as e:
                # Basic check for 429 or Resource Exhausted
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 10  # 10s, 20s...
                        print(f"[Gemini] Rate limit hit. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                raise e
        
        # Extract image from response parts
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
    Full AI Mode: Vision Analysis (Gemini) + Image Generation (Gemini 3 Pro).
    Now passes reference images directly to the generation model.
    """
    if not os.environ.get("GEMINI_API_KEY"): 
         return {
             "comment": "[Full AI (Mock)] API Key Missing.",
             "user_heads": 0, "model_heads": 0, "image": None
         }

    try:
        # 1. Vision Analysis (Gemini 2.5) to understand Scene + Create Gen Prompt
        img_user = PIL.Image.open(io.BytesIO(user_img_bytes))
        img_model = PIL.Image.open(io.BytesIO(model_img_bytes))
        
        model = get_gemini_model("gemini-2.0-flash")
        
        lang_target = "Korean"
        if language == "vi": lang_target = "Vietnamese"
        elif language == "en": lang_target = "English"

        # Update prompt to be compatible with Image-to-Image logic
        analysis_prompt = [
            "Role: Professional Fashion Director.",
            "Task: Deep-Fake Simulation Planning.",
            "STEP 1: Analyze Image 1 (User) for Body Ratios & Background.",
            "STEP 2: Analyze Image 2 (Model) for Clothing Details.",
            "STEP 3: Compare & Critique (Text).",
            f"   - Language: {lang_target}",
            "   - Tone: Sarcastic but useful fashion advice.",
            "STEP 4: Create a prompt for Gemini 3 Pro Image generation.",
            "- The prompt should instruct the model to generate a person resembling Image 1 wearing the clothes from Image 2.",
            "- Mention 'photorealistic, 8k, high quality'.",
            "- Keep the background from Image 1.",
            "Return JSON: {",
            "  'user_heads': number, 'model_heads': number,",
            f"  'comment': string (Savage {lang_target} Critique),",
            "  'gen_prompt': string (English Prompt)"
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
            except:
                data = {"comment": text, "gen_prompt": "A stylish person"}
        else:
            data = {"comment": text, "gen_prompt": "A stylish person"}
            
        # 2. Image Generation (Gemini 3 Pro with Reference Images)
        gen_prompt = data.get("gen_prompt", "Fashion model wearing stylish clothes")
        
        # Make the prompt explicit about the images provided
        full_gen_prompt = (
            f"{gen_prompt}. "
            "Use the first image as the reference for the person and background. "
            "Use the second image as the reference for the clothing. "
            "Generate a realistic image."
        )

        generated_b64, error_msg = generate_gemini_image(full_gen_prompt, reference_images=[img_user, img_model])

        
        final_comment = data.get("comment", "Analysis complete.")
        if error_msg:
             final_comment += f"\n\n[System Error] {error_msg}"

        return {
            "user_heads": data.get("user_heads", 0),
            "model_heads": data.get("model_heads", 0),
            "comment": final_comment,
            "image": generated_b64 
        }

    except Exception as e:
        return {
             "comment": f"Full AI Error: {str(e)}",
             "user_heads": 0, "model_heads": 0, "image": None
         }

def fallback_response(u_h, m_h, msg_prefix=""):
    return f"{msg_prefix}"
