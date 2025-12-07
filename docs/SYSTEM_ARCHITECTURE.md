# FactBomb Fitting Room: System Architecture

## 1. Project Overview
**FactBomb Fitting Room** is a brutally honest, hyper-realistic clothes fitting application.
Unlike traditional virtual try-ons that beautify the user, this app focuses on **Proportion Reality Check**.
It visualizes how a specific outfit would look on the user's *actual* body proportions (Head-to-Body ratio, Leg length, Shoulder width).

---

## 2. Core Service Architecture (3-Mode System)

The backend (`/backend`) is powered by FastAPI and integrates Computer Vision (OpenCV) with Generative AI (Google Gemini 3.0 Pro).

### A. Vision Mode (Standard)
*   **File**: `backend/services/mode_vision.py` (formerly `image_processor`)
*   **Technology**: OpenCV, Dlib(optional), MediaPipe logic.
*   **Function**: 
    - Extracts `User` and `Model` body landmarks.
    - Calculates precise body ratios (Heads tall, Leg-to-Body ratio).
    - Performs **2D Image Warping**: Geometrically distorts the Model's image to match the User's ratios.
    - **No Generative AI** is used for the image; purely mathematical transformation.
*   **Output**: A warped "Blueprint" image + Ratio Analysis.

### B. AI Mode (Generative)
*   **File**: `backend/services/mode_ai.py`
*   **Technology**: Gemini 3.0 Pro (Visiom) + Gemini 3.0 Pro Image.
*   **Function**: 
    - **Proportion Transfer**: Uses AI to understand the user's ratio (e.g., 6 heads tall) and the Model's scene.
    - Generates a completely NEW image where the Model's body is morphed to the User's ratio, while preserving the Model's face and gender.
*   **Output**: A high-fidelity generative image + "Fact Bomb" critique.

### C. Pro Mode (Integrated Hybrid)
*   **File**: `backend/services/mode_pro.py`
*   **Technology**: Vision Mode (Base) + Gemini 3.0 Pro (Physics Engine).
*   **Function**:
    - **Step 1**: Runs `Vision Mode` to get a geometrically accurate "Blueprint" (Warped Image).
    - **Step 2**: Feeds this Blueprint + Skeleton analysis to Gemini 3.
    - **Step 3 (Physics Simulation)**: The AI acts as a **VFX Artist**. It fixes the warping artifacts and adds **Physical Realism** (e.g., buttons bursting on a tight shirt, pants bunching up on short legs, fabric tension).
*   **Output**: The ultimate "Reality Check" image that combines geometric accuracy with photorealistic physics.

---

## 3. Directory Structure (Refactored)

```
smh-fassion/
├── backend/
│   ├── main.py             # FastAPI Entry Point (Routes requests to modes)
│   └── services/
│       ├── ai_engine.py    # Core Gemini Client & Image Gen Utilities
│       ├── mode_vision.py  # Vision Mode Logic (OpenCV)
│       ├── mode_ai.py      # AI Mode Logic (Proportion Transfer)
│       └── mode_pro.py     # Pro Mode Logic (Vision + Physics)
│
├── frontend/
│   ├── src/
│   │   └── pages/
│   │       └── LabPage.jsx # Main Interface (Mode Selector: Vision/AI/Pro)
│   └── ...
└── docs/
    └── SYSTEM_ARCHITECTURE.md # This File
```

## 4. Key AI Prompts

- **AI Mode Persona**: `AI Body Proportion Specialist`. Focuses on Face Preservation + Body Morphing.
- **Pro Mode Persona**: `Expert Fashion Physicist & VFX Artist`. Focuses on Fabric Physics, Tension, and Realistic Fit Failures based on the Vision Blueprint.
