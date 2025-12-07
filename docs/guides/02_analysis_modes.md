# 2. Analysis Modes & Logic

This document details the logic and data flow of the three core analysis modes: **Vision Mode**, **AI Mode**, and **Pro Mode**.

## A. Vision Mode (Basic)
**"Geometric Warping Engine"**
*   **File**: `backend/services/mode_vision.py`
*   **Technology**: OpenCV, MediaPipe Pose.
*   **Workflow**:
    1.  **Landmark Detection**: Extracts skeleton joints (Shoulders, Hips, Ankles) from both User and Model.
    2.  **Ratio Calculation**: Computes Head-to-Body ratio (N-Heads) and Limb ratios.
    3.  **2D Image Warping**: Geometrically stretches/compresses the Model's body to match the User's calculated ratios.
*   **Output**: A "Blueprint" image. Correct proportions, but may have warping artifacts (blur/smudge).
*   **Use Case**: Quick, mathematical comparison.

## B. AI Mode (Generative)
**"Proportion Transfer Specialist"**
*   **File**: `backend/services/mode_ai.py`
*   **Technology**: Gemini 3.0 Pro (Vision + Image).
*   **Workflow**:
    1.  **Input**: Raw User Image + Raw Model Image.
    2.  **Prompting**: "Transfer User's body proportions to Model. Preserve Model's Face."
    3.  **Generation**: The AI hallucinates a completely NEW image from scratch, morphing the body shape while keeping identity.
*   **Output**: High-fidelity generative image.
*   **Use Case**: Creative visualization, drastic body shape changes.

## C. Pro Mode (Reference + Physics)
**"The Ultimate Reality Check"**
*   **File**: `backend/services/mode_pro.py`
*   **Technology**: Vision Mode Output + Gemini 3.0 Pro (Physics Engine).
*   **Workflow**:
    1.  **Step 1 (Vision)**: Runs `mode_vision` to get the geometrically accurate "Blueprint".
    2.  **Step 2 (Physics Simulation)**: Feeds the "Blueprint" + "Skeleton Data" to Gemini.
    3.  **Step 3 (VFX Rendering)**: The AI acts as a **VFX Artist**. It fixes warping artifacts but adds **Physical Realism**.
        *   *Example*: If the user is wider than the model, it renders buttons bursting or fabric pulling.
        *   *Example*: If legs are shorter, it renders pants bunching up at the ankles.
*   **Output**: A photorealistic image that looks like a high-end CGI fit check.
*   **Use Case**: The most realistic and "brutally honest" fitting experience.

---
## Comparison Table

| Feature | Vision Mode | AI Mode | Pro Mode |
| :--- | :--- | :--- | :--- |
| **Logic** | Pure Math (OpenCV) | Pure GenAI (Gemini) | Hybrid (CV + GenAI) |
| **Input** | Landmarks/Ratios | Raw Images | Warped Blueprint |
| **Face** | Original Model | Preserved by AI | Original Model |
| **Physics** | None (Simple Stretch) | AI Imagined | **Simulated (Fabrics/Tension)** |
| **Speed** | Fastest | Slow | Slow |
| **Cost** | Low (CPU) | High (API) | High (API) |
