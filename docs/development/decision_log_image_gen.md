# Image Generation Model Decision Log

This document records the history and decision-making process regarding the selection of the Image Generation AI model for the "FactBomb Fitting Room" project.

## Current Choice: Google Gemini (Imagen 3 / gemini-2.5-flash-image)
- **Status**: **Active**
- **Reason**:
    1.  **Unified Ecosystem**: We are already using Gemini for Vision (Image Analysis) and Text (Fact Bomb comments). Using the same provider simplifies key management (single `GEMINI_API_KEY`).
    2.  **Cost/Free Tier**: Google currently offers a generous free tier for Gemini API usage, whereas competitors often require immediate billing info or paid credits.
    3.  **Speed**: Direct integration via `google-genai` SDK and simplified authentication proved to be faster and less error-prone during development.

---

## 1. Replicate (Model: FLUX.1 [schnell])
- **Status**: **Deprecated / Removed**
- **Attempt Period**: Early Development Phase
- **Why it was removed**:
    *   **Authentication Issues**: Encountered persistent `401 Unauthenticated` errors despite having a valid API Token.
    *   **Billing Barrier**: Even with free credits, Replicate often triggers errors if no billing method (credit card) is attached to the account, blocking usage.
    *   **Library Instability**: The `replicate` Python library had breaking changes (v1.0.0+) regarding output format (`FileOutput` objects vs URLs) which complicated the implementation.
- **Conditions for Re-adoption**:
    *   If FLUX.1's specific artistic style or quality becomes strictly necessary.
    *   If the project scales to a paid infrastructure where Replicate's cost per image is justified.
    *   **Estimated Cost**: Approx. $0.003 - $0.05 per image depending on model/steps.

## 2. OpenAI (Model: DALL-E 3)
- **Status**: **Skipped / Removed**
- **Attempt Period**: Intermediate Phase (Alternative to Replicate)
- **Why it was removed**:
    *   **Cost**: DALL-E 3 is generally more expensive ($0.04 - $0.08 per image for HD) compared to other options for mass testing.
    *   **Separate Billing**: Requires a separate `OPENAI_API_KEY` with prepaid credits. It does not work on a purely "pay-later" or "free-tier" basis as easily as Gemini for developers.
    *   **Complexity**: Introducing another provider purely for image generation added overhead to the `.env` management and dependency list.
- **Conditions for Re-adoption**:
    *   If Gemini's image quality (prompt adherence, photorealism) proves insufficient.
    *   If strict safety filters in Gemini block fashion-related prompts (DALL-E also has filters, but behavior differs).
    *   **Estimated Cost**: $0.04 per image (Standard 1024x1024).

---

## Summary for Future Migration
If we decide to move back to Replicate or OpenAI, we must resolve:
1.  **Reliable Payment**: Set up a corporate/personal credit card on the respective platform to avoid `401/Billing` errors.
2.  **SDK Management**: Ensure the latest SDK version is locked in `requirements.txt` to avoid breaking changes (especially for Replicate).
3.  **Cost Analysis**: Calculate the projected monthly cost based on Daily Active Users (DAU) x Avg Images Generated.
