"""
agents/pest_scout.py
====================
Pest & Disease Scout sub-agent for FarmAssist.

WHY the tool takes symptoms text (not an image path):
  Google ADK's AgentTool passes TEXT between agents — image bytes in the
  top-level Content object are seen by the orchestrator but are NOT forwarded
  to sub-agents called via AgentTool. The orchestrator (gemini-2.0-flash with
  vision) does the visual analysis itself, then calls this tool with a text
  description of what it sees. This tool provides domain-expert treatment
  advice based on that description.
"""
import os
from google.adk.agents import Agent


def get_pest_treatment(symptoms: str) -> str:
    """
    Returns practical, affordable treatment recommendations for crop pest or
    disease symptoms observed by the farmer or identified visually.

    WHY text-in / text-out: ADK sub-agents called via AgentTool receive a
    text summary from the orchestrator, not multimodal content. This function
    maps symptom descriptions to actionable treatment advice without needing
    to see the image itself.

    Args:
        symptoms: Plain-text description of the visible damage or symptoms,
                  e.g. "holes eaten through leaves, skeletonised veins visible,
                  no insects currently visible".

    Returns:
        Treatment recommendation string suitable for a small Indian farm.
    """
    symptoms_lower = symptoms.lower()

    # ── Insect / chewing damage ───────────────────────────────────────────────
    if any(kw in symptoms_lower for kw in ["hole", "eaten", "chew", "skeleto", "caterpillar", "worm", "larva"]):
        return (
            "DIAGNOSIS: Chewing insect damage — likely caterpillars (armyworm / "
            "tobacco caterpillar) or leaf-eating beetles.\n\n"
            "TREATMENT OPTIONS (affordable, small-farm):\n"
            "1. NEEM-BASED SPRAY: Mix 5 ml neem oil + 1 ml liquid soap in 1 litre "
            "water. Spray on both leaf surfaces every 5-7 days for 3 weeks. "
            "Neem disrupts the insect's feeding and growth cycle.\n"
            "2. MANUAL REMOVAL: For small plots, check plants at dawn/dusk when "
            "caterpillars are active. Hand-pick and destroy them.\n"
            "3. CHEMICAL OPTION (if severe): Chlorpyrifos 20 EC @ 2 ml/litre or "
            "Spinosad @ 0.5 ml/litre. Spray in the evening — avoids harming bees.\n"
            "4. PREVENTION: Intercrop with marigold (repels pests). Clear crop "
            "residue after harvest to break the insect life cycle.\n\n"
            "URGENCY: Act within 2-3 days if more than 20% of leaves are affected."
        )

    # ── Fungal / blight / spot disease ───────────────────────────────────────
    elif any(kw in symptoms_lower for kw in ["spot", "blight", "rust", "mold", "fungal", "yellow patch", "brown patch", "lesion"]):
        return (
            "DIAGNOSIS: Fungal disease — likely leaf spot, early blight, or rust.\n\n"
            "TREATMENT OPTIONS:\n"
            "1. COPPER-BASED FUNGICIDE: Copper oxychloride 50 WP @ 3 g/litre. "
            "Spray on affected leaves. Safe and widely available.\n"
            "2. MANCOZEB 75 WP @ 2.5 g/litre for blight/spot diseases.\n"
            "3. Remove and burn severely infected leaves — reduces spore load.\n"
            "4. Avoid overhead watering; water at the base of plants.\n\n"
            "PREVENTION: Ensure good spacing between plants for airflow. "
            "Avoid working in the field when leaves are wet."
        )

    # ── Wilting / root issues ────────────────────────────────────────────────
    elif any(kw in symptoms_lower for kw in ["wilt", "droop", "yellow", "root"]):
        return (
            "DIAGNOSIS: Possible root rot, wilt disease (Fusarium/Verticillium), "
            "or water stress.\n\n"
            "STEPS:\n"
            "1. Check soil moisture — overwatering causes root rot.\n"
            "2. Pull one affected plant and inspect roots: brown/black roots = rot, "
            "white healthy roots = likely wilt disease.\n"
            "3. FOR ROOT ROT: Improve drainage, reduce watering, apply Trichoderma "
            "viride @ 4 g/litre as a soil drench.\n"
            "4. FOR WILT: No cure once severe — remove and destroy affected plants "
            "to prevent spread. Treat remaining plants with Carbendazim 50 WP "
            "@ 1 g/litre as a drench."
        )

    # ── General / unrecognised ───────────────────────────────────────────────
    else:
        return (
            f"Observed symptoms: {symptoms}\n\n"
            "GENERAL ADVICE:\n"
            "1. Send a clear photo to your local Krishi Vigyan Kendra (KVK) for "
            "exact identification.\n"
            "2. As a precaution, spray Neem oil (5 ml/litre) to cover fungal and "
            "insect possibilities.\n"
            "3. Ensure plants are not water-stressed or waterlogged.\n"
            "4. Check nearby plants for the same symptoms — early spread detection "
            "is key to limiting crop loss."
        )


pest_scout_agent = Agent(
    name="pest_scout",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    description=(
        "Diagnoses visible crop pest and disease symptoms and recommends "
        "affordable treatments suitable for small Indian farms."
    ),
    instruction=(
        "You are a Pest and Disease Scout for Indian farmers. You will receive "
        "a description of visible symptoms on a crop (holes, spots, wilting, "
        "discoloration, etc.). Call the get_pest_treatment tool with those "
        "symptoms to get a specific diagnosis and treatment plan. "
        "Present the advice clearly, using simple language a farmer can act on "
        "immediately. Always mention both organic/affordable and chemical options."
    ),
    tools=[get_pest_treatment],
)