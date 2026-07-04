import os
import mimetypes
from google.adk.agents import Agent
from google.genai import types


def diagnose_crop_image(image_path: str) -> str:
    """Tool: analyzes a crop leaf/plant image for visible pest or disease symptoms.
    Reads the image file directly and returns a text description for the LLM
    to reason over — the actual visual analysis happens via the agent's own
    multimodal model call, not inside this function.
    """
    if not os.path.exists(image_path):
        return f"ERROR: Image file not found at {image_path}. Cannot diagnose."

    # We just confirm the file exists and is readable here.
    # The actual image bytes are attached to the LLM call separately in main.py,
    # since ADK tools return text, not images, back to the model.
    mime_type, _ = mimetypes.guess_type(image_path)
    return (
        f"Image at {image_path} (type: {mime_type}) has been loaded for visual "
        f"inspection. Analyze the attached image for signs of pest damage, "
        f"fungal disease, discoloration, or wilting, and provide a diagnosis "
        f"and treatment recommendation."
    )


pest_scout_agent = Agent(
    name="pest_scout",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=(
        "You are a Pest and Disease Scout for Indian farmers. When given an "
        "image of a crop, use the diagnose_crop_image tool to confirm the "
        "image is loaded, then visually analyze the actual image content "
        "yourself (you have vision capability) for pest damage, disease "
        "symptoms, or discoloration. Give a clear diagnosis and a practical, "
        "affordable treatment recommendation suitable for a small Indian farm."
    ),
    tools=[diagnose_crop_image],
)