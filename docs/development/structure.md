# Documentation Structure Plan

This document outlines the refactored document structure, ensuring accuracy with the current Vision/AI/Pro architecture.

## 1. Project Overview & Architecture
*File: `docs/guides/01_overview.md`*
*   **Subject**: Introduction to 'FactBomb Fitting Room'.
*   **Tech Stack**: React/Vite (Frontend) + FastAPI (Backend) + Gemini 3.0 Pro.
*   **Architecture**: The 3-Mode System (Vision, AI, Pro).
*   **Directory Map**: Updated structure refelcting `mode_vision.py`, `mode_ai.py`, `mode_pro.py`.

## 2. Analysis Modes & Logic
*File: `docs/guides/02_analysis_modes.md`*
*   **Vision Mode (Basic)**: Pure OpenCV algorithms. 2D Warping, Ratio Calculation. Fast & Deterministic.
*   **AI Mode (Generative)**: Gemini 3.0 Proportion Transfer. Generates a new image morphing the model's body to user's stats while keeping the face.
*   **Pro Mode (Integrated)**: Vision Blueprints + AI Physics Simulation. The most advanced mode adding realistic fabric physics and fit failures to the warped blueprint.

## 3. Configuration & secrets
*File: `docs/guides/03_configuration.md`*
*   **Env Vars**: `.env` setup (GEMINI_API_KEY).
*   **Requirements**: Python dependencies (`opencv-python`, `google-genai` SDK).
*   **Local Run**: `start_app.bat` usage.

## 4. Deployment Guide
*File: `docs/guides/04_deployment.md`*
*   Standard production guidelines for React/FastAPI.

---
*Note: Legacy docs have been archived or updated.*
