import os
from google import genai
from google.genai import types
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

def analyze_mix_mode(user_bytes, model_bytes, user_ratios, model_ratios, user_landmarks, model_landmarks, base_result_bytes, user_debug_bytes, model_debug_bytes, language="ko"):
    """
    Mix Mode: Base Mode(Geometric) + Generative AI(Physics/Realism)
    - Raw Data is minimized to text summary, complex spatial info is passed via Visuals.
    """
    if not os.environ.get("GEMINI_API_KEY"):
         return {
             "comment": "[Mix Mode (Mock)] API Key Missing.", 
             "image": None,
             "debug_info": "API Key Missing"
         }

    try:
        # 1. Load Images (Bytes -> PIL Image)
        img_user = PIL.Image.open(io.BytesIO(user_bytes))
        img_model = PIL.Image.open(io.BytesIO(model_bytes))
        img_base_result = PIL.Image.open(io.BytesIO(base_result_bytes))
        img_user_debug = PIL.Image.open(io.BytesIO(user_debug_bytes))
        img_model_debug = PIL.Image.open(io.BytesIO(model_debug_bytes))

        # 2. Gemini Client Init
        client = get_gemini_client() # Use shared helper

        # 3. Language Settings
        lang_target = "Korean"
        if language == "vi": lang_target = "Vietnamese (Tiếng Việt)"
        elif language == "en": lang_target = "English"

        # 4. [Data Diet] Key Summary Generation
        # Calculate Heads from ratios
        u_heads = round(1 / user_ratios.get('head_stat_ratio', 0.15), 1)
        m_heads = round(1 / model_ratios.get('head_stat_ratio', 0.15), 1)
        
        slim_data_summary = {
            "user_metrics": {
                "head_ratio_heads": u_heads,
                "estimated_bmi_shape": "Wide" if user_ratios.get('shoulder_heads', 2.5) > 3.0 else "Average"
            },
            "model_metrics": {
                "head_ratio_heads": m_heads,
                "original_fit": "Slim/Regular Fit"
            },
            "comparison_logic": {
                "user_is_wider": True if user_ratios.get('shoulder_heads', 0) > model_ratios.get('shoulder_heads', 0) else False,
                "user_head_is_larger": True if u_heads < m_heads else False
            }
        }
        data_block_str = f"**ANALYTICAL DATA SUMMARY:**\n{json.dumps(slim_data_summary, indent=2)}"

        # 5. Construct Prompt (Physics & Volume Focused)
        instruction_text = [
            "Role: Expert 3D Character Artist & Physics Simulation Specialist.",
            "Task: Generate a Hyper-Realistic 'Virtual Try-On' image. Prioritize Physical Reality over Aesthetic.",
            "",
            "**VISUAL INPUTS (Your Primary Spatial Data):**",
            "1. [IMAGE 1 - USER BODY]: Reference for MASS and VOLUMN (Z-Axis/Girth). Look at the belly/chest depth.",
            "2. [IMAGE 2 - MODEL STYLE]: Reference for Outfit design and Lighting.",
            "3. [IMAGE 3 - USER SKELETON]: **Visual Measure.** Yellow rulers show the actual Head-to-Body ratio.",
            "4. [IMAGE 4 - MODEL SKELETON]: **Visual Measure.** Compare this skeleton with Image 3.",
            "5. [IMAGE 5 - GEOMETRIC BLUEPRINT]: The 'Draft' shape. It has the correct proportions but lacks texture.",
            "",
            data_block_str, # Injected Summary
            "",
            "**CRITICAL PHYSICS SIMULATION (REALITY CHECK):**",
            "1. **Volume & Closure Logic (The 'Button' Check):**",
            "   - Look at Image 1 (User's Girth). Compare it to Image 2 (Outfit Size).",
            "   - IF the User is significantly wider/heavier: The jacket/shirt CANNOT button up.",
            "   - **ACTION:** Render the jacket OPEN or buttons BURSTING. Show the shirt pulling apart or the undershirt visible.",
            "2. **Fabric Tension:** Fabric must follow the 'Geometric Blueprint' (Image 5) shape but behave like real cloth under stress. Create horizontal wrinkles across the belly.",
            "",
            "**OUTPUT JSON FORMAT:**",
            "{",
            f"  \"comment\": \"string ({lang_target} comment. Use the 'Summary Metrics' and Skeleton visuals to roast the fit. e.g., '데이터상 고객님의 상체가 모델보다 훨씬 큽니다. 단추는 포기하고 오픈 스타일로 가시죠!')\",",
            "  \"gen_prompt\": \"string (The Final Image Prompt. MUST describe: 'Jacket unbuttoned/gaping', 'Tight fit', 'Stomach protruding', 'Fabric tension'. Do NOT describe a perfectly fitted suit.)\"",
            "}"
        ]
        
        main_prompt_str = "\n".join(instruction_text)

        # 6. Assemble Contents (Text + Images)
        contents = [
            main_prompt_str,
            img_user, img_model, img_user_debug, img_model_debug, img_base_result
        ]
        
        # 7. Vision Analysis & Prompt Gen (Reasoning Step)
        # Using Gemini 3 Pro for best reasoning
        analysis_model = "gemini-3-pro-preview" 
        
        response = client.models.generate_content(
            model=analysis_model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json" # Enforce JSON
            )
        )
        
        # 8. Parse JSON (Safe Method)
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            data = {"comment": "분석 결과를 처리하는 중 오류가 발생했습니다.", "gen_prompt": "A realistic photo of a person wearing a suit that is too tight."}

        gen_prompt = data.get("gen_prompt", "Photorealistic fashion shot")
        final_comment = data.get("comment", "분석 완료.")
        
        print(f"[Mix Mode] Generated Prompt: {gen_prompt[:100]}...")

        # 9. Image Generation (Creation Step)
        ref_images = [img_model, img_base_result] 
        
        # Negative Prompt
        negative_prompt = "perfect fit, tailored suit, slimming effect, loose clothing, photoshop, illustration, cartoon"
        final_gen_prompt = f"{gen_prompt}, 8k, highly detailed, realistic texture. Negative prompt: {negative_prompt}"
        
        generated_b64, error_msg = generate_gemini_image(final_gen_prompt, reference_images=ref_images)
        
        if error_msg:
             final_comment += f"\n(이미지 생성 중 오류: {error_msg})"

        return {
            "comment": final_comment,
            "image": generated_b64,
            "gen_prompt": gen_prompt
        }

    except Exception as e:
        print(f"Mix Mode Error: {e}")
        return {
             "comment": f"시스템 오류가 발생했습니다: {str(e)}", 
             "image": None,
             "gen_prompt": ""
        }

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

        # Update prompt to be compatible with Proportion Transfer logic
        analysis_prompt = [
            "Role: AI Body Proportion Specialist & Image Synthesizer.",
            "Task: Transfer the User's (Image 1) body proportions onto the Model's (Image 2) body while strictly preserving the Model's face and gender identity.",
            "",
            "**INPUT PROCESSING:**",
            "1. [IMAGE 1 - USER]: Source of **Proportions, Ratios, and BMI**. (Analyze Head-to-Body ratio, Leg-to-Torso ratio, Shoulder-to-Hip ratio).",
            "2. [IMAGE 2 - MODEL]: Source of **Face, Gender, Outfit, and Background**.",
            "",
            "**GENERATION LOGIC (Proportion Transfer):**",
            "1. **Analyze Gender:** Identify the gender of the person in Image 2 (Male/Female/Non-binary). The output must respect this gender.",
            "2. **Analyze User's Ratio:** Calculate the User's physical ratios from Image 1 (e.g., 6 heads tall, short legs, wider hips, narrow shoulders).",
            "3. **Apply to Model:** Resize and warp the **Model's body parts** to match the User's calculated ratios exactly.",
            "   - **Head Size:** If User's head is large relative to body, scale up the Model's head size.",
            "   - **Limb Length:** Match the User's leg and arm lengths (shorten or lengthen).",
            "   - **Volume/Width:** Match the User's specific width (e.g., wider belly, wider hips, narrower shoulders).",
            "4. **Identity Preservation (CRITICAL):** Keep the **Model's Original Face and Gender** exactly as seen in Image 2. Do NOT swap faces.",
            "5. **Clothing Interaction:** The outfit must wrap around this new \"distorted\" body proportion. It should look realistic but potentially unflattering due to the mismatched proportions (e.g., pants bunching up, sleeves too long/short, buttons straining).",
            "",
            "**OUTPUT JSON FORMAT:**",
            "{",
            "  \"analysis\": {",
            "    \"detected_gender_model\": \"string (e.g., Female)\",",
            "    \"user_ratio\": \"number (e.g., 5.8 heads)\",",
            "    \"model_original_ratio\": \"number (e.g., 8.2 heads)\",",
            "    \"key_change_point\": \"string (e.g., Head size scaled up 15%, Legs shortened, Hips widened)\"",
            "  },",
            f"  \"fact_bomb_comment\": \"string (Humorous Korean comment. e.g., '모델분은 8등신인데... 고객님 비율을 적용하니 머리가 꽤 커졌네요! 현실적인 핏입니다.')\",",
            "  \"gen_prompt\": \"string (Final prompt: A photo of the [GENDER] MODEL from Image 2, but modified to have the BODY PROPORTIONS of Image 1. The face remains the original [GENDER] model's face. The body is morphed: Head is LARGER, legs are SHORTER/LONGER, and width is adjusted to match User's ratio. Wearing the same outfit, but the fit reflects the new proportions.)\"",
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
        
        # Extract analysis data (Updated for Proportion Transfer mode)
        analysis = data.get("analysis", {})
        
        user_body = {
            "user_ratio": analysis.get("user_ratio", "N/A"),
            "key_change_point": analysis.get("key_change_point", "N/A")
        }
        
        model_info = {
            "detected_gender_model": analysis.get("detected_gender_model", "N/A"),
            "model_original_ratio": analysis.get("model_original_ratio", "N/A")
        }
        
        # For backward compat in the return dict (if needed), or just dump the new json
        return {
            "user_heads": 0, # Deprecated in VFX mode, set 0
            "model_heads": 0,
            "comment": final_comment,
            "image": generated_b64,
            "debug_user_info": json.dumps(user_body, indent=2, ensure_ascii=False),
            "debug_model_info": json.dumps(model_info, indent=2, ensure_ascii=False),
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
