"""
agents/orchestrator.py
======================
Root orchestrator agent for FarmAssist.

WHY an orchestrator pattern:
  Instead of one monolithic agent that does everything, we use a
  hierarchical design where a root LlmAgent (the orchestrator) receives
  all user messages and delegates to specialist sub-agents.  This lets
  each sub-agent be independently developed, tested, and swapped without
  touching the routing logic — critical as we add market_watch and
  pest_scout in later phases.

ADK routing mechanism:
  When `sub_agents` is set, ADK gives the orchestrator LLM awareness of
  each sub-agent's `name` and `description`.  The orchestrator decides
  whether to answer directly or transfer control; ADK handles the
  transfer internally.  We do NOT write custom dispatch code.

Phase 1: routes to crop_advisor_agent only.
Phase 2: market_watch_agent will be added to sub_agents here.
Phase 4: pest_scout_agent will be added here.
"""
import os
from agents.crop_advisor import crop_advisor_agent
from google.adk.agents import LlmAgent

# ── Source-confirmed fields used below ───────────────────────────────────────
#   LlmAgent.name          : str          (BaseAgent)
#   LlmAgent.model         : str          (LlmAgent)
#   LlmAgent.instruction   : str          (LlmAgent)
#   LlmAgent.description   : str          (BaseAgent)
#   LlmAgent.sub_agents    : list[BaseAgent] (BaseAgent)


orchestrator_agent = LlmAgent(
    name="farmassist_orchestrator",

    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),

    description=(
        "FarmAssist: an AI assistant for Indian farmers covering crop advice, "
        "market prices, and pest detection."
    ),

    instruction=(
        "You are FarmAssist, a helpful AI assistant for Indian farmers. "
        "You speak clearly and avoid technical jargon.\n\n"
        "Routing rules:\n"
        "- If the user asks about crop management, weather impact on crops, "
        "when to spray, when to sell, or field conditions → delegate to "
        "crop_advisor.\n"
        "- After receiving a response from a sub-agent, synthesise it into "
        "a single, friendly reply addressed directly to the farmer. "
        "Do not expose internal agent names or tool names in your reply.\n"
        "- If the query is not farm-related, politely say you can only help "
        "with farming topics."
    ),

    # WHY sub_agents here (not tools=[crop_advisor_agent.as_tool()]):
    #   Using sub_agents lets ADK manage the full conversation handoff —
    #   the sub-agent sees the full message history in its context window,
    #   which is important for multi-turn memory in Phase 3.
    #   as_tool() would give only a single function call, losing history.
    sub_agents=[crop_advisor_agent],
)
