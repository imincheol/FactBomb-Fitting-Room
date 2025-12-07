
import os
import io
import json
import re
import PIL.Image
from .ai_engine import get_gemini_client, generate_gemini_image

def analyze_full_ai_mode(user_img_bytes, model_img_bytes, language="ko"):
    """
    AI Mode: Vision Analysis (Gemini 3) + Image Generation (Gemini 3 Image).
    Focus: Proportion Transfer using pure AI generation (No warping pipeline).
    """
    if not os.environ.get("GEMINI_API_KEY"): 
         return {
             "comment": "[AI Mode (Mock)] API Key Missing.",
             "user_heads": 0, "model_heads": 0, "image": None
         }

    try:
        # 1. Vision Analysis (Gemini 3 Pro) to understand Scene + Create Gen Prompt
        img_user = PIL.Image.open(io.BytesIO(user_img_bytes))
        img_model = PIL.Image.open(io.BytesIO(model_img_bytes))
        
        client = get_gemini_client()
        if not client:
             return fallback_response(0, 0, "[AI Mode] Gemini Client Init Failed")
        
        model_name = "gemini-3-pro-preview"
        
        lang_target = "Korean"
        if language == "vi": lang_target = "Vietnamese"
        elif language == "en": lang_target = "English"

        # AI Mode Prompt (Proportion Transfer)
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
            f"  \"fact_bomb_comment\": \"string (Humorous {lang_target} comment. e.g., '모델분은 8등신인데... 고객님 비율을 적용하니 머리가 꽤 커졌네요! 현실적인 핏입니다.')\",",
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
        import ast
        data = {}
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                try:
                    data = ast.literal_eval(json_str)
                    if not isinstance(data, dict): raise ValueError("Parsed data is not a dict")
                except:
                     data = {"fact_bomb_comment": text, "gen_prompt": "A stylish person"}
        else:
            data = {"fact_bomb_comment": text, "gen_prompt": "A stylish person"}
            
        # 2. Image Generation
        gen_prompt = data.get("gen_prompt", "Fashion model wearing stylish clothes")
        full_gen_prompt = f"{gen_prompt}, photorealistic, 8k, high quality"

        generated_b64, error_msg = generate_gemini_image(full_gen_prompt, reference_images=[img_user, img_model])
        
        final_comment = data.get("fact_bomb_comment", data.get("comment", "Analysis complete."))
        if error_msg:
             final_comment += f"\n\n[System Error] {error_msg}"
        
        # Structure Return Data
        analysis = data.get("analysis", {})
        
        user_body = {
            "user_ratio": analysis.get("user_ratio", "N/A"),
            "key_change_point": analysis.get("key_change_point", "N/A")
        }
        
        model_info = {
            "detected_gender_model": analysis.get("detected_gender_model", "N/A"),
            "model_original_ratio": analysis.get("model_original_ratio", "N/A")
        }
        
        return {
            "user_heads": 0,
            "model_heads": 0,
            "comment": final_comment,
            "image": generated_b64,
            "debug_user_info": json.dumps(user_body, indent=2, ensure_ascii=False),
            "debug_model_info": json.dumps(model_info, indent=2, ensure_ascii=False),
            "gen_prompt": gen_prompt
        }

    except Exception as e:
        return {
             "comment": f"AI Mode Error: {str(e)}",
             "user_heads": 0, "model_heads": 0, "image": None,
             "debug_user_info": "", "debug_model_info": "", "gen_prompt": ""
         }

def fallback_response(u_h, m_h, msg_prefix=""):
    return {
        "user_heads": u_h, "model_heads": m_h, 
        "comment": f"{msg_prefix}. Please check server logs.",
        "image": None
    }
