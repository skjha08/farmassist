"""
agents/orchestrator.py
======================
Root orchestrator agent for FarmAssist.

ROLE IN THE ARCHITECTURE:
  This is the entry point for every user query.  The orchestrator is an
  LlmAgent (Gemini 2.0 Flash with vision) that:
    1. Reads the user's text query (and optional image).
    2. Decides which specialist sub-agent(s) to call.
    3. Assembles their responses into a single coherent reply.

WHY a separate orchestrator (not one big agent with all tools inline):
  Separation of concerns.  Each sub-agent has a focused instruction set and
  tool list, making them independently testable.  The orchestrator's only job
  is routing and synthesis — it does NOT implement domain logic itself.

WHY AgentTool (not sub_agents list):
  google.adk.tools.agent_tool.AgentTool wraps a child LlmAgent as a callable
  tool.  This gives the orchestrator full control over WHEN to call each
  specialist (function-calling semantics) rather than ADK's automatic
  handoff pattern.  The orchestrator can call multiple tools in one turn,
  which is required for mixed queries (e.g. "should I spray AND sell today?").

WHY vision is handled at the orchestrator level (not in pest_scout):
  ADK's AgentTool passes TEXT between agents — multimodal content in the
  top-level Content object is visible to the orchestrator but is NOT forwarded
  to sub-agents.  The orchestrator (which has Gemini Vision) describes what it
  sees in the image, then calls pest_scout with that text description.
"""

import os
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

# ── Import sub-agents (each is a focused LlmAgent with its own tools) ─────────
from .crop_advisor import crop_advisor_agent
from .market_watch import market_watch_agent
from .pest_scout import pest_scout_agent

# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator agent definition
# ─────────────────────────────────────────────────────────────────────────────

orchestrator_agent = Agent(
    name="farmassist_orchestrator",

    # WHY gemini-2.0-flash: fast, cost-efficient, and supports multimodal input
    # (vision).  The orchestrator needs vision to describe uploaded crop photos
    # before forwarding symptom text to pest_scout.
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),

    instruction=(
        "You are FarmAssist, an AI assistant for Indian farmers. "
        "You have three specialist tools: crop_advisor (crop management and weather questions), "
        "market_watch (mandi prices and selling timing), and pest_scout (pest/disease diagnosis). "

        # ── Vision handling — critical for Pest Scout flow ─────────────────────
        # WHY explicit vision instructions: without them the model sometimes
        # says "I cannot see the image" even though gemini-2.0-flash does
        # support vision.  Explicit prompting removes ambiguity.
        "IMPORTANT — when the farmer uploads an IMAGE: "
        "You have vision capability. First, carefully look at the image and describe what you see "
        "(e.g. 'holes eaten through the leaf with skeletonised veins and no visible insects'). "
        "Then call pest_scout with that symptom description to get the diagnosis and treatment. "
        "Do NOT say you cannot see the image — you can, and you must describe it. "

        # ── Routing rules ──────────────────────────────────────────────────────
        # WHY explicit routing rules: LLMs can be ambiguous about when to
        # call tools.  Explicit rules reduce missed tool calls and ensure
        # multi-topic queries (crop + price) always call all relevant agents.
        "For text-only pest/symptom queries (no image), call pest_scout with the described symptoms. "
        "For crop/weather questions, call crop_advisor. "
        "For price/selling questions, call market_watch. "
        "If a query covers multiple topics, call ALL relevant tools and combine their answers. "
        "Always include specific price figures from market_watch when discussing selling. "
        "Remember the crop and location the farmer mentioned earlier in the conversation."
    ),

    # WHY AgentTool wrapper: converts each sub-agent into a callable tool so
    # the orchestrator can invoke them via Gemini function-calling.
    # The sub-agent's `name` and `description` fields become the tool's
    # name and description in the function declaration sent to the model.
    tools=[
        AgentTool(agent=crop_advisor_agent),
        AgentTool(agent=market_watch_agent),
        AgentTool(agent=pest_scout_agent),
    ],
)