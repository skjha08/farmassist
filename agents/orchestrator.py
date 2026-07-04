import os
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from .crop_advisor import crop_advisor_agent
from .market_watch import market_watch_agent

orchestrator_agent = Agent(
    name="farmassist_orchestrator",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=(
    "You are FarmAssist. You have two tools: crop_advisor (for crop/weather "
    "questions) and market_watch (for price/selling questions). If a farmer's "
    "question touches both topics, call BOTH tools and combine their answers "
    "into one clear response. Always include the specific price figures "
    "returned by market_watch. "
    "IMPORTANT: Remember details the farmer already told you earlier in this "
    "conversation (crop, location) and use them automatically in follow-up "
    "questions without asking again, unless the farmer changes them."
),
    tools=[
        AgentTool(agent=crop_advisor_agent),
        AgentTool(agent=market_watch_agent),
    ],
)