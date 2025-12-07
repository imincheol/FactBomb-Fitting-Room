# AI Integration Plan for FactBomb Fitting Room

## Objective
Integrate an AI API (e.g., OpenAI GPT-4o or Google Gemini) to enhance the "FactBomb" analysis capabilities while maintaining the existing computer-vision-based image processing logic as a "Legacy" or "Standard" mode.

## Core Constraint
- **Input**: 2 Images (User Body, Model Body).
- **Output**: 1 Result Image (Warped/Fitted) + Analysis (Text/Stats).
- **Interface**: Remains unchanged for the user, except for a new "Mode Selection" option.

## Phase 1: Backend Refactoring (Modularization)
Currently, `backend/main.py` contains all logic (Image Processing, Face Detection, Ratio Calculation, Text Generation). We will clean this up to support multiple "strategies".

1.  **Create `backend/services/` directory.**
2.  **Extract Legacy Logic**:
    -   Move `process_image`, `get_landmarks_with_results`, `warp_image_to_ratio`, etc., into `backend/services/legacy_processor.py`.
    -   This ensures the current working version is preserved safely.
3.  **Define Shared Types**:
    -   Ensure both modes return data in a consistent format: `{ "result_image": ..., "analysis": { ... } }`.

## Phase 2: Implement "AI Mode" (Analysis Focus)
We will introduce an AI Mode that uses the *existing* image processing for the visual "Fit" (since generic AI APIs are not yet specialized for precise virtual try-on without complex setups), but uses an **LLM (Large Language Model)** for the *Analysis/Critique*.

1.  **Create `backend/services/ai_processor.py`**:
    -   It will call the Legacy Processor to get the *Metrics* (ratios, head count) and the *Warped Image*.
    -   **New Step**: Instead of using the hardcoded `analyze_body_proportions` function, it will construct a prompt for the AI API.
    -   **Prompt Engineering**:
        -   Input: User's Body Ratios, Model's Body Ratios, Calculated "N-Heads" (Example: "User is 6.5 heads, Model is 8.5 heads").
        -   Persona: "Brutally honest fashion critic", "Witty", "Sarcastic".
        -   Task: Generate a 1-2 sentence "FactBomb" comment comparing the user to the model.
2.  **API Integration**:
    -   Library: `openai` or `google-generativeai`.
    -   Environment Variables: Needs `OPENAI_API_KEY` or `GEMINI_API_KEY`.

## Phase 3: Frontend Updates
1.  **Add Mode Selector**:
    -   In `frontend/src/App.jsx`, add a Switch/Toggle:
        -   Option A: "Unknown Algorithm (Standard)"
        -   Option B: "AI Analyst (Powered by LLM)"
2.  **API Logic**:
    -   Update `handleProcess` to send `mode: 'legacy' | 'ai'` to the backend.
3.  **UI Feedback**:
    -   Show a different loading state or icon when AI is "thinking".

## Phase 4: Future Expansion (Image Generation)
*Note: This plan currently assumes AI is used for ANALYSIS. If AI is desired for IMAGE GENERATION (e.g., Generative Fill for missing parts or full diffusion-based try-on), that would be a separate Phase 4 involving tools like Stable Diffusion, which is significantly more complex.*

## Execution Steps
1.  **Refactor**: Split `main.py` -> **Unknown Algorithm (Standard)**. (Completed)
2.  **Endpoint**: Update `POST /process-image` to accept `mode`. (Completed)
3.  **AI Service**: Implement `ai_processor.py` / `gemini_service.py`. (Completed)
    -   Mix Mode: Implemented (Text Analysis).
    -   Full AI Mode: Implemented (Vision Analysis + Image Gen).
4.  **Frontend**: Add the toggle for Standard/Mix/Full AI. (Completed)

## Current Status (2025-12-07)
-   **Refactoring**: Cleaned up backend structure (`services/`).
-   **AI Integration**: Switched to Google Gemini (2.5 Flash / 2.0 Flash Exp) for both analysis and image generation.
-   **Documentation**: Created README, updated structure, and organized samples.
-   **Stability**: Handled various API limitations (Quota handling) and created "Lab Mode" for experiments.
