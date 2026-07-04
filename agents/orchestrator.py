import os
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from .crop_advisor import crop_advisor_agent
from .market_watch import market_watch_agent
from .pest_scout import pest_scout_agent

orchestrator_agent = Agent(
    name="farmassist_orchestrator",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=(
        "You are FarmAssist. You have three tools: crop_advisor (crop/weather "
        "questions), market_watch (price/selling questions), and pest_scout "
        "(when the farmer shares an image or describes visible symptoms like "
        "spots, wilting, or discoloration). If a query touches multiple "
        "topics, call ALL relevant tools and combine their answers into one "
        "clear response. Always include specific figures from market_watch "
        "when discussing selling. Remember crop/location the farmer already "
        "shared earlier in the conversation."
    ),
    tools=[
        AgentTool(agent=crop_advisor_agent),
        AgentTool(agent=market_watch_agent),
        AgentTool(agent=pest_scout_agent),
    ],
)