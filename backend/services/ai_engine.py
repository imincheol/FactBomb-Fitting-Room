
import os
from google import genai
from google.genai import types
import base64
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_gemini_client():
    if os.environ.get("GEMINI_API_KEY"):
        return genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    return None

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
        
        print(f"[Gemini Core] Generating Image... Prompt: {prompt[:50]}...")
        
        # Prepare contents
        contents = [prompt]
        if reference_images:
             # The new SDK handles PIL Images directly in the list
             print(f"[Gemini Core] Including {len(reference_images)} reference images.")
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
                        print(f"[Gemini Core] Rate limit hit. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                raise e
        
        # Extract image from response parts
        if response.parts:
            for part in response.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    print(f"[Gemini Core] Image generated successfully. Size: {len(image_bytes)} bytes")
                    return base64.b64encode(image_bytes).decode("utf-8"), None
        
        return None, "No image found in Gemini response."

    except Exception as e:
        cleaned_err = str(e).replace('"', "'")
        print(f"[Gemini Core] Error: {cleaned_err}")
        return None, f"Gemini Error: {cleaned_err}"
