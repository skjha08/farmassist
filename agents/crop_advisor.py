"""
agents/crop_advisor.py
======================
Crop Advisor sub-agent for FarmAssist.

WHY a sub-agent (not a standalone script):
  Google ADK uses a hierarchical manager-worker pattern.  The orchestrator
  LlmAgent holds `sub_agents=[crop_advisor_agent]`.  When the orchestrator
  decides the user's query is crop-related, ADK automatically delegates to
  this agent and injects its reply back into the orchestrator's context.

Phase 1 scope:
  - ONE tool: crop_advice(crop, location)
  - Mocked weather (hardcoded: raining, 3 days) — no real API keys needed yet
  - No memory, no guardrails
"""
import os
from google.adk.agents import LlmAgent

# ── Confirmed in source inspection:
#   LlmAgent field: model: Union[str, BaseLlm] = ''
#   LlmAgent field: tools: list[ToolUnion]
#   BaseAgent field: sub_agents: list[BaseAgent]
#   BaseAgent field: name: str
#   BaseAgent field: description: str


# ─────────────────────────────────────────────────────────────────────────────
# Mock weather helper
# ─────────────────────────────────────────────────────────────────────────────

def _mock_weather(location: str) -> dict:
    """
    WHY mocked: Phase 1 must be entirely self-contained (no API keys beyond
    Gemini).  A real weather call (OpenWeatherMap / IMD) will replace this in a
    later phase.  Hardcoding the response lets us validate the full ADK pipeline
    independently of weather-API availability.
    """
    # In reality this would call IMD or OpenWeatherMap.
    # For Phase 1 we hardcode: it has been raining for 3 days everywhere.
    return {
        "condition": "raining",
        "days": 3,
        "location": location,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADK Tool
# ─────────────────────────────────────────────────────────────────────────────

def crop_advice(crop: str, location: str) -> str:
    """
    Returns practical farming advice for a given crop and location,
    taking current weather conditions into account.

    WHY this is an ADK tool (not just a function):
      ADK tools are plain Python functions that the LLM can call via
      function-calling.  The LlmAgent sees the function signature + docstring
      and decides when to invoke it.  Keeping logic here (not in the
      instruction prompt) makes it testable independently of the LLM.

    Args:
        crop:     The crop the farmer is growing (e.g. "wheat", "rice").
        location: The region/district (e.g. "Punjab", "Vidarbha").

    Returns:
        A plain-text advice string suitable for reading aloud or displaying
        to a low-literacy farmer.
    """
    weather = _mock_weather(location)
    condition = weather["condition"]
    days = weather["days"]

    if condition == "raining" and days >= 2:
        # ── Rain-specific advice ──────────────────────────────────────────────
        # Three distinct action items as specified in Phase 1 requirements:
        #   1. Delay spraying / fertilising
        #   2. Check drainage
        #   3. Hold selling (wet grain fetches lower mandi price)
        return (
            f"Weather report for {location}: it has been {condition} for "
            f"{days} consecutive days.\n\n"
            f"Advice for your {crop} crop:\n"
            f"1. DELAY SPRAYING: Do NOT apply pesticides or fertilisers right "
            f"now. Rain will wash them off the leaves and into the soil before "
            f"the plant can absorb them — wasting your money and polluting "
            f"nearby water sources.\n"
            f"2. CHECK DRAINAGE: Walk your field and clear any blocked channels. "
            f"Waterlogging for more than 2-3 days can cause root rot and "
            f"significant yield loss in {crop}.\n"
            f"3. HOLD SELLING: Do not take your {crop} to the mandi yet. Wet "
            f"or damp grain is graded lower and fetches 10-20% less than dry "
            f"grain. Wait until the weather clears and the grain moisture drops "
            f"below 14% before selling."
        )
    else:
        # ── Default (dry / normal) advice ────────────────────────────────────
        return (
            f"Weather in {location} appears dry/normal. "
            f"Your {crop} crop conditions look acceptable for regular "
            f"field operations — spraying, fertilising, and selling as planned."
        )


# ─────────────────────────────────────────────────────────────────────────────
# ADK Agent definition
# ─────────────────────────────────────────────────────────────────────────────

crop_advisor_agent = LlmAgent(
    # WHY name matters: the orchestrator uses the agent's `name` and
    # `description` to decide which sub-agent to route a query to.
    # Name must be a valid Python identifier and unique in the agent tree.
    name="crop_advisor",

    # WHY "gemini-2.0-flash" exactly: faster and cheaper than Pro;
    # sufficient for structured advice generation.  No suffix variants
    # (-001, -exp) as instructed.
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),

    # WHY description is kept to one sentence: ADK passes this to the
    # orchestrator LLM as the "tool description" for this sub-agent.
    # A concise sentence is easier for the model to parse than a paragraph.
    description=(
        "Provides practical crop management advice for Indian farmers based "
        "on current weather and field conditions."
    ),

    instruction=(
        "You are an experienced Indian agricultural extension officer. "
        "When a farmer tells you about their crop and location, call the "
        "crop_advice tool to get weather-aware recommendations. "
        "Present the advice in clear, simple language. "
        "Use bullet points. Avoid technical jargon. "
        "If the farmer mentions rain, always address spraying delay, "
        "drainage, and selling timing explicitly."
    ),

    # WHY tools=[crop_advice]: this registers the function as a callable
    # tool.  ADK converts the function signature + docstring into a
    # FunctionDeclaration for the Gemini function-calling API.
    tools=[crop_advice],
)
