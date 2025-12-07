import os
from google import genai
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

def get_gemini_client():
    if os.environ.get("GEMINI_API_KEY"):
        return genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
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
        client = get_gemini_client()
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Gemini Error: {str(e)}"

def generate_gemini_image(prompt, reference_images=None):
    """
    Generates an image using Gemini 3 (gemini-3-pro-image-preview).
    Supports reference images.
    """
    if not os.environ.get("GEMINI_API_KEY"):
         return None, "Missing GEMINI_API_KEY in .env"

    try:
        # Initialize the new client
        client = get_gemini_client()
        if not client:
             return None, "Missing GEMINI_API_KEY"
        
        print(f"[Gemini] Generating (Gemini 3 Pro)... Prompt: {prompt[:50]}...")
        
        # Prepare contents
        contents = [prompt]
        if reference_images:
             # Check if reference images are valid PIL images or supported types
             # The new SDK handles PIL Images directly in the list
             print(f"[Gemini] Including {len(reference_images)} reference images.")
             contents.extend(reference_images)

        # Use gemini-3-pro-image-preview
        model_name = "gemini-3-pro-image-preview"

        response = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Configure for image generation
                config = genai.types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                )
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
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
    Full AI Mode: Vision Analysis (Gemini 3) + Image Generation (Gemini 3 Image).
    """
    if not os.environ.get("GEMINI_API_KEY"): 
         return {
             "comment": "[Full AI (Mock)] API Key Missing.",
             "user_heads": 0, "model_heads": 0, "image": None
         }

    try:
        # 1. Vision Analysis (Gemini 3 Pro) to understand Scene + Create Gen Prompt
        img_user = PIL.Image.open(io.BytesIO(user_img_bytes))
        img_model = PIL.Image.open(io.BytesIO(model_img_bytes))
        
        client = get_gemini_client()
        if not client:
             return fallback_response(0, 0, "[Full AI] Gemini Client Init Failed")
        
        model_name = "gemini-3-pro-preview"
        
        lang_target = "Korean"
        if language == "vi": lang_target = "Vietnamese"
        elif language == "en": lang_target = "English"

        # Update prompt to be compatible with Image-to-Image logic
        analysis_prompt = [
            "Role: Expert VFX Artist specializing in Digital Body Morphing and Cloth Physics.",
            "Task: Generate a realistic simulation image based on two input images.",
            "",
            "**INPUT DATA MAPPING (CRITICAL):**",
            "1. [IMAGE 1 - REFERENCE ONLY]: Use ONLY the **Body Volume/Mass** and **BMI**. (IGNORE the face, IGNORE the clothes, IGNORE the background).",
            "2. [IMAGE 2 - BASE TARGET]: Use the **Face**, **Identity**, **Pose**, **Clothing Design**, **Clothing Size**, and **Background**.",
            "",
            "**GENERATION GOAL:**",
            "Render the person from [IMAGE 2] but strictly morph their body shape to match the heavy proportions of [IMAGE 1].",
            "",
            "**STEP-BY-STEP INSTRUCTIONS:**",
            "1. **Identity Lock:** Draw the face and head EXACTLY as seen in [IMAGE 2]. The person must remain the male model. DO NOT swap the face with [IMAGE 1].",
            "2. **Body Morphing:** Expand the torso, waist, hips, and limbs of the model to match the silhouette and volume of the person in [IMAGE 1].",
            "3. **The 'FactBomb' Fit (Physics Engine):**",
            "   - The suit is still Size M (from Image 2), but the body is now Size XL/XXL (from Image 1).",
            "   - **Visual Consequence:** The suit must look extremely tight.",
            "   - **Belly:** The jacket button must be pulling hard, creating an 'X' shape wrinkle. There should be a gap showing the shirt underneath.",
            "   - **Sleeves:** Because the shoulders and arms are wider, the sleeves must ride up, exposing the wrists.",
            "   - **Trousers:** The thighs should look like they are bursting the seams. The fabric is stretched smooth due to tension.",
            "4. **Environment:** Keep the clean studio background from [IMAGE 2].",
            "",
            "**OUTPUT JSON FORMAT:**",
            "Return the analysis and the final generative prompt in this JSON structure:",
            "{",
            "  \"metrics\": {",
            "    \"user_body_analysis\": {",
            "      \"shape_desc\": \"string (e.g., Heavy pear shape, Protruding belly)\",",
            "      \"volume_factor\": \"string (e.g., Body mass is approx 1.5x of the model)\"",
            "    },",
            "    \"clothing_physics\": {",
            "      \"stress_points\": \"string (e.g., Button hole, Shoulder seams, Thigh inseam)\",",
            "      \"fit_status\": \"string (e.g., Critically Undersized / Bursting)\"",
            "    }",
            "  },",
            f"  \"fact_bomb_comment\": \"string (A short, humorous reality check comment in {lang_target} regarding the tight fit)\",",
            "  \"gen_prompt\": \"string (The final prompt to generate the image. MUST include visual descriptions of tightness. AND MUST Append a Negative Prompt instruction at the end: 'Negative prompt: perfect fit, tailored suit, comfortable fit, loose clothing, slimming effect, correct sleeve length, fashion model body, photoshopped perfection'.)\"",
            "}",
            img_user, img_model
        ]
        
        response = client.models.generate_content(
            model=model_name,
            contents=analysis_prompt
        )
        text = response.text.strip()
        
        # Parse JSON
        import re
        import ast
        data = {}
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
                print(f"[DEBUG] Gemini Analysis Success (JSON)")
            except json.JSONDecodeError:
                try:
                    # Fallback for single quotes or lax JSON
                    data = ast.literal_eval(json_str)
                    print(f"[DEBUG] Gemini Analysis Success (AST)")
                    # Ensure it's a dict
                    if not isinstance(data, dict): raise ValueError("Parsed data is not a dict")
                except:
                     print(f"[DEBUG] JSON Parsing Failed completely. Text: {text[:50]}...")
                     data = {"fact_bomb_comment": text, "gen_prompt": "A stylish person"}
        else:
            data = {"fact_bomb_comment": text, "gen_prompt": "A stylish person"}
            
        # 2. Image Generation (Imagen 3)
        gen_prompt = data.get("gen_prompt", "Fashion model wearing stylish clothes")
        
        # Refine prompt for Imagen (Text Only)
        # We rely on Gemini's detailed description in 'gen_prompt'.
        full_gen_prompt = f"{gen_prompt}, photorealistic, 8k, high quality"

        generated_b64, error_msg = generate_gemini_image(full_gen_prompt, reference_images=[img_user, img_model])

        
        final_comment = data.get("fact_bomb_comment", data.get("comment", "Analysis complete."))
        if error_msg:
             final_comment += f"\n\n[System Error] {error_msg}"
        
        # Extract metrics safely (Updated for new structure)
        metrics = data.get("metrics", {})
        # Remap new keys to the variables we pass to the return dict
        # New structure: metrics: { user_body_analysis: {}, clothing_physics: {} }
        user_body = metrics.get("user_body_analysis", {})
        clothing_physics = metrics.get("clothing_physics", {})
        
        # For backward compat in the return dict (if needed), or just dump the new json
        return {
            "user_heads": 0, # Deprecated in VFX mode, set 0
            "model_heads": 0,
            "comment": final_comment,
            "image": generated_b64,
            "debug_user_info": json.dumps(user_body, indent=2, ensure_ascii=False),
            "debug_model_info": json.dumps(clothing_physics, indent=2, ensure_ascii=False),
            "gen_prompt": gen_prompt
        }

    except Exception as e:
        return {
             "comment": f"Full AI Error: {str(e)}",
             "user_heads": 0, "model_heads": 0, "image": None,
             "debug_user_info": "", "debug_model_info": "", "gen_prompt": ""
         }

def fallback_response(u_h, m_h, msg_prefix=""):
    return f"{msg_prefix}"
