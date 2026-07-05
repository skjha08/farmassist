"""
mcp_server.py
=============
FarmAssist MCP (Model Context Protocol) Tool Server.

WHY an MCP server in addition to the existing ADK multi-agent system?
  The ADK orchestrator already delegates to crop_advisor, market_watch, and
  pest_scout sub-agents internally.  This MCP server exposes the SAME
  underlying tool functions over the standardised MCP protocol so that any
  MCP-compatible client (Claude Desktop, another ADK agent via MCPToolset,
  the Agents CLI, etc.) can call them without knowing about FarmAssist's
  internal architecture.

  In short: the multi-agent system IS the product; the MCP server makes the
  tools composable and discoverable in the broader AI-agent ecosystem.

HOW to run:
  python mcp_server.py               # stdio transport (default, for CLI/ADK)

HOW an ADK agent would connect (example, not used in main app.py):
  from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
  toolset = MCPToolset(
      connection_params=StdioServerParameters(command="python", args=["mcp_server.py"])
  )

Tools exposed:
  - crop_advice(crop, location)       → weather-aware farming advice
  - market_advice(crop, location)     → mandi price & selling-timing advice
  - get_pest_treatment(symptoms)      → pest/disease treatment recommendations

NOTE: This file intentionally imports the tool *functions* directly from the
existing agent modules so there is NO code duplication.  The business logic
lives in agents/; this file is purely the MCP protocol layer on top.
"""

from mcp.server.fastmcp import FastMCP

# ── Import tool functions from the existing agent modules ─────────────────────
# Only the plain Python functions are imported, NOT the LlmAgent objects.
# This keeps the MCP server self-contained and avoids initialising Gemini here.
from agents.crop_advisor import crop_advice as _crop_advice
from agents.market_watch import market_advice as _market_advice
from agents.pest_scout import get_pest_treatment as _get_pest_treatment

# ── FastMCP server instance ───────────────────────────────────────────────────
# The name "farmassist-tools" becomes the server identifier in MCP handshakes.
mcp = FastMCP("farmassist-tools")


# ── Tool 1: Crop Advisor ──────────────────────────────────────────────────────
@mcp.tool()
def crop_advice(crop: str, location: str) -> str:
    """
    Returns weather-aware crop management advice for Indian farmers.

    Provides three action items based on current conditions:
    whether to spray/fertilise, drainage checks, and selling timing.

    Args:
        crop:     The crop being grown (e.g. "wheat", "rice", "tomato").
        location: The region or district (e.g. "Punjab", "Vidarbha").

    Returns:
        Plain-text advice suitable for a farmer with limited literacy.
    """
    return _crop_advice(crop=crop, location=location)


# ── Tool 2: Market Watch ──────────────────────────────────────────────────────
@mcp.tool()
def market_advice(crop: str, location: str) -> str:
    """
    Returns current mandi (wholesale market) price information and
    selling-timing recommendations for a given crop and location.

    Args:
        crop:     The crop to check prices for (e.g. "wheat", "onion").
        location: The market location (e.g. "Amritsar", "Nashik").

    Returns:
        Price summary and a clear hold/sell recommendation.
    """
    return _market_advice(crop=crop, location=location)


# ── Tool 3: Pest Scout ────────────────────────────────────────────────────────
@mcp.tool()
def get_pest_treatment(symptoms: str) -> str:
    """
    Returns practical, affordable pest and disease treatment recommendations
    based on a plain-text description of visible crop symptoms.

    The orchestrator (which has Gemini Vision) describes what it sees in an
    uploaded photo; this tool maps that description to actionable treatment
    advice without needing direct image access.

    Args:
        symptoms: Plain-text description of visible damage or disease signs,
                  e.g. "holes eaten through leaves, skeletonised veins,
                  no insects visible during the day".

    Returns:
        Diagnosis and treatment options (organic/affordable + chemical).
    """
    return _get_pest_treatment(symptoms=symptoms)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # stdio transport: the server communicates over stdin/stdout.
    # This is the standard transport for ADK MCPToolset and the Agents CLI.
    mcp.run(transport="stdio")
