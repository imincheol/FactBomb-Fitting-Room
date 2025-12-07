import sys
if sys.version_info < (3, 10):
    try:
        import importlib.metadata
        import importlib_metadata
        if not hasattr(importlib.metadata, "packages_distributions"):
            importlib.metadata.packages_distributions = importlib_metadata.packages_distributions
    except ImportError:
        pass

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import io
import traceback

# Import Services
from backend.services.image_processor import process_visuals_core, get_base64_results
from backend.services.legacy_analysis import analyze_body_proportions
from backend.services.gemini_service import analyze_mix_mode, analyze_full_ai_mode
from backend.services.lab_service import run_experiment_flow_a, run_experiment_flow_b

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/process-baseline")
async def process_baseline(
    user_image: UploadFile = File(...), 
    model_image: UploadFile = File(...),
):
    print("Received Baseline Request")
    try:
        user_bytes = await user_image.read()
        model_bytes = await model_image.read()

        nparr_user = np.frombuffer(user_bytes, np.uint8)
        img_user = cv2.imdecode(nparr_user, cv2.IMREAD_COLOR)

        nparr_model = np.frombuffer(model_bytes, np.uint8)
        img_model = cv2.imdecode(nparr_model, cv2.IMREAD_COLOR)

        if img_user is None or img_model is None:
             raise HTTPException(status_code=400, detail="Invalid image data")

        # 1. Process Visuals (Common: Warping / Ratios)
        try:
            visual_data = process_visuals_core(img_user, img_model)
        except ValueError as ve:
             raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
             traceback.print_exc()
             raise HTTPException(status_code=500, detail=f"Image Processing Failed: {str(e)}")

        # 2. Base Data Preparation
        user_ratios = visual_data['user_ratios']
        model_ratios = visual_data['model_ratios']
        real_user_heads = round(1 / user_ratios.get('head_stat_ratio', 0.15), 1)
        real_model_heads = round(1 / model_ratios.get('head_stat_ratio', 0.15), 1)

        # 3. Generate Baseline Result (Standard Mode)
        legacy_analysis = analyze_body_proportions(user_ratios, model_ratios)
        legacy_analysis['fact_bomb'] = legacy_analysis.get('comment')
        
        legacy_analysis['result_heads'] = visual_data['result_heads']
        legacy_analysis['result_ratios'] = visual_data['result_ratios']
        legacy_analysis['user_heads'] = legacy_analysis.get('user_heads', real_user_heads)
        legacy_analysis['model_heads'] = legacy_analysis.get('model_heads', real_model_heads)
        
        base64_images = get_base64_results(visual_data)

        response_payload = {
            "baseline": {
                "image": base64_images['result_image'],
                "analysis": legacy_analysis,
                "debug_user": base64_images['user_debug_image'],
                "debug_model": base64_images['model_debug_image']
            },
            # Pass ratios back so frontend can send them to AI endpoint
            "meta": {
                "user_ratios": user_ratios,
                "model_ratios": model_ratios
            }
        }
        return response_payload

    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-ai")
async def process_ai(
    user_image: UploadFile = File(...), 
    model_image: UploadFile = File(...),
    mode: str = Form(...), # 'lab', 'full_ai'
    lab_flow: str = Form(None),
    # Receive ratios as JSON string to avoid complex parsing or re-calc
    user_ratios_json: str = Form(None), 
    model_ratios_json: str = Form(None)
):
    print(f"Received AI Request. Mode: {mode}")
    import json
    
    try:
        user_bytes = await user_image.read()
        model_bytes = await model_image.read()
        
        # Parse ratios if provided
        user_ratios = json.loads(user_ratios_json) if user_ratios_json else {}
        model_ratios = json.loads(model_ratios_json) if model_ratios_json else {}
        
        # Default heads if ratios missing (fallback)
        real_user_heads = round(1 / user_ratios.get('head_stat_ratio', 0.15), 1) if user_ratios else 0
        real_model_heads = round(1 / model_ratios.get('head_stat_ratio', 0.15), 1) if model_ratios else 0
        
        generated_image = None
        
        if mode == 'full_ai':
            print("Running Active Mode: Full AI")
            ai_vision_res = analyze_full_ai_mode(user_bytes, model_bytes)
            
            u_h = ai_vision_res.get('user_heads', real_user_heads)
            m_h = ai_vision_res.get('model_heads', real_model_heads)
            if u_h == 0: u_h = real_user_heads
            if m_h == 0: m_h = real_model_heads
            
            generated_image = ai_vision_res.get('image') # Get real image from Nano Banana

            active_analysis = {
                "fact_bomb": ai_vision_res.get('comment', 'AI Vision Failed'),
                "user_heads": u_h,
                "model_heads": m_h,
                "result_heads": 0, 
                "result_ratios": {}
            }

        elif mode == 'lab':
            print(f"Running Active Mode: Lab ({lab_flow})")
            lab_result = {"comment": "Lab error", "image": None}
            
            if lab_flow == 'exp_a':
                # Flow A: Model Image + User Ratios (Reality Check)
                lab_result = run_experiment_flow_a(user_ratios, model_ratios, model_bytes)
            elif lab_flow == 'exp_b':
                # Flow B: Model Clothes + User Ratios (Fit Check)
                lab_result = run_experiment_flow_b(user_ratios, model_ratios, model_bytes)
            
            lab_comment = lab_result.get("comment", "No comment")
            generated_image = lab_result.get("image")
            
            active_analysis = {
                "fact_bomb": f"[🧪 Lab Report]\n{lab_comment}",
                "user_heads": real_user_heads,
                "model_heads": real_model_heads,
                "result_heads": 0, 
                "result_ratios": {}
            }

        return {
            "active": {
                "image": generated_image, 
                "analysis": active_analysis
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        print(f"CRITICAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
