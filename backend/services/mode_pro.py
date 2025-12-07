
import os
import io
import json
import re
import cv2
import PIL.Image
from .ai_engine import get_gemini_client, generate_gemini_image

TEXT_MODEL_NAME = "gemini-3-pro-preview"

def run_pro_mode_analysis(user_bytes, model_bytes, visual_data, language="ko"):
    """
    Pro Mode: Vision Mode Result + AI Physics.
    Uses the 'Warping Engine' result as a geometric blueprint, and uses AI to add photorealism and physics (fabric tension, fit).
    """
    try:
        # 1. Prepare Images
        img_user = PIL.Image.open(io.BytesIO(user_bytes))
        img_model = PIL.Image.open(io.BytesIO(model_bytes))
        
        # Convert OpenCV images from visual_data to PIL
        img_base_result = PIL.Image.fromarray(cv2.cvtColor(visual_data['final_result'], cv2.COLOR_BGR2RGB))
        img_user_debug = PIL.Image.fromarray(cv2.cvtColor(visual_data['user_debug'], cv2.COLOR_BGR2RGB))
        img_model_debug = PIL.Image.fromarray(cv2.cvtColor(visual_data['model_debug'], cv2.COLOR_BGR2RGB))

        # 2. Client & Language
        client = get_gemini_client()
        if not client:
             return {"comment": "API Key Missing", "image": None}

        lang_target = "Korean"
        if language == "vi": lang_target = "Vietnamese"
        elif language == "en": lang_target = "English"

        # 3. Data Diet (Summary)
        user_ratios = visual_data['user_ratios']
        model_ratios = visual_data['model_ratios']
        
        u_heads = round(1 / user_ratios.get('head_stat_ratio', 0.15), 1)
        m_heads = round(1 / model_ratios.get('head_stat_ratio', 0.15), 1)

        slim_data_summary = {
            "comparison": {
                "user_heads": u_heads,
                "model_heads": m_heads,
                "structure_diff": "User is Wider" if user_ratios.get('shoulder_heads', 0) > model_ratios.get('shoulder_heads', 0) else "Similar"
            }
        }
        data_block = f"**DATA SUMMARY:**\n{json.dumps(slim_data_summary)}"

        # 4. PRO MODE PROMPT (The "Physics Simulation" Logic)
        prompt_text = f"""
        Role: Expert 3D Character Artist & Physics Simulation Specialist.
        Task: Create the Ultimate Reality Check. Combine the 'Geometric Blueprint' (Image 5) with 'Physical Realism'.
        
        **INPUTS:**
        1. [USER BODY]: Reference for Mass/Volume.
        2. [MODEL STYLE]: Reference for Outfit/Lighting.
        3. [USER SKELETON]: Visual Ratio Guide.
        4. [MODEL SKELETON]: Visual Ratio Guide.
        5. [GEOMETRIC BLUEPRINT]: **(CRITICAL)** This is the 'Vision Mode' result. It has the CORRECT proportions but looks fake/warped.
        
        **YOUR JOB:**
        - Take Image 5 (Blueprint) and "Render" it into a Photorealistic Image.
        - Fix the "Warping Artifacts" (blurriness, smudging) but KEEP the "Distorted Proportions".
        - **ADD PHYSICS:**
          - If the Blueprint shows a wide User in a slim outfit -> Show BUTTONS BURSTING, Fabric pulling.
          - If the Blueprint shows short legs -> Show pants BUNCHING at the ankles.
          - Make it look like a high-end CGI fail or a harsh reality photo.
          
        {data_block}
        
        **OUTPUT JSON:**
        {{
            "analysis": {{
                "user_body": {{
                    "shape_desc": "string (e.g. Broad Shoulders, High BMI)",
                    "volume_factor": "string (e.g. Girth is 20% wider than model)"
                }},
                "model_fit": {{
                    "fit_status": "string (e.g. Bursting Buttons)",
                    "stress_points": "string (e.g. Chest, Belly, Thighs)",
                    "fabric_type": "string (e.g. Stiff Cotton)"
                }}
            }},
            "comment": "string ({lang_target} Fact Bomb. Comment on the specific fit failure visible in the Blueprint. e.g. 'The geometry is correct, but the physics are screaming. That shirt button is holding on for dear life.')",
            "gen_prompt": "string (Detailed Image Prompt. Describe the visual state of Image 5 but with 8k texture. 'Photorealistic shot of person, tight shirt buttons straining, fabric wrinkled horizontally across belly, short pant legs bunching on shoes, awkward stance, high detail.')"
        }}
        """

        # 5. Vision Analysis (Gemini 3 Pro)
        response = client.models.generate_content(
            model=TEXT_MODEL_NAME, 
            contents=[prompt_text, img_user, img_model, img_user_debug, img_model_debug, img_base_result]
        )
        text = response.text.strip()
        
        # Parse JSON
        data = {}
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except:
                data = {"comment": text, "gen_prompt": "Realistic fit check"}
        else:
             data = {"comment": text, "gen_prompt": "Realistic fit check"}

        # 6. Image Generation (Gemini Image)
        gen_prompt = data.get("gen_prompt", "Realistic fit check")
        final_comment = data.get("comment", text)
        
        print(f"[PRO MODE] Generating with prompt: {gen_prompt[:50]}...")
        
        # Use Model + BaseResult as structure reference
        ref_images = [img_model, img_base_result]
        
        image_b64, error_msg = generate_gemini_image(gen_prompt, reference_images=ref_images)
        
        if error_msg:
             final_comment += f"\n[Gen Error] {error_msg}"
        
        # Parse analysis for debug view
        analysis = data.get("analysis", {})
        user_info = analysis.get("user_body", {})
        model_info = analysis.get("model_fit", {})

        return {
            "comment": final_comment,
            "image": image_b64,
            "debug_user_info": json.dumps(user_info, indent=2, ensure_ascii=False),
            "debug_model_info": json.dumps(model_info, indent=2, ensure_ascii=False),
            "gen_prompt": gen_prompt
        }

    except Exception as e:
        print(f"Pro Mode Error: {e}")
        return {"comment": f"Pro Error: {str(e)}", "image": None}
