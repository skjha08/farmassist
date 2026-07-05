"""
agents/market_watch.py
======================
Market Watch sub-agent for FarmAssist.

PURPOSE:
  Answers questions about wholesale (mandi) prices for crops and advises
  farmers on whether it is a good time to sell their produce.

WHY a separate sub-agent (not a tool in crop_advisor):
  Market timing and crop field management are distinct domains.  A farmer
  asking "should I sell today?" needs price data and trend analysis, not
  weather-driven agronomic advice.  Keeping them separate lets each agent
  stay focused and lets the orchestrator combine both when needed.

CURRENT STATE — mock data:
  get_mock_market_price() returns hardcoded prices simulating a realistic
  scenario (below-average prices due to wet market conditions).
  WHY mocked: no free, reliable Agmarknet (agmarknet.gov.in) API was
  available during development.  The agent architecture is designed so that
  replacing _get_mock_market_price with a real HTTP call requires no changes
  to the agent definition or the orchestrator.
"""

import os
from google.adk.agents import Agent


# ─────────────────────────────────────────────────────────────────────────────
# Mock data layer
# ─────────────────────────────────────────────────────────────────────────────

def get_mock_market_price(crop: str, location: str) -> dict:
    """
    Returns a simulated mandi price snapshot for a given crop and location.

    WHY this function is separate from market_advice:
      Isolating data fetching from business logic makes it easy to swap in a
      real Agmarknet / data.gov.in API call later without changing market_advice.

    Returns a dict with:
      crop, location, current_price_per_quintal, avg_price_per_quintal, trend
    """
    # Hardcoded scenario: prices are currently soft due to wet/damp grain
    # flooding the market after recent rain — a realistic Indian mandi pattern.
    return {
        "crop": crop,
        "location": location,
        "current_price_per_quintal": 2100,       # Rs/quintal (below average)
        "avg_price_per_quintal": 2350,            # seasonal average
        "trend": "below_average",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADK Tool
# ─────────────────────────────────────────────────────────────────────────────

def market_advice(crop: str, location: str) -> str:
    """
    Fetches the current mandi price for a crop and returns a plain-text
    hold/sell recommendation with specific price figures.

    WHY return specific price numbers (not just "hold" or "sell"):
      Farmers make financial decisions based on this advice.  Vague guidance
      ("prices are low") is not actionable; quoting exact Rs/quintal figures
      lets the farmer compare against their cost of production or target price.

    Args:
        crop:     The crop to price-check (e.g. "wheat", "onion", "rice").
        location: The mandi location (e.g. "Amritsar", "Nashik").

    Returns:
        Plain-text advice with price figures and a clear hold/sell direction.
    """
    data = get_mock_market_price(crop, location)

    if data["trend"] == "below_average":
        # ── Below-average price scenario ──────────────────────────────────────
        # Advice: hold.  Wet grain in the market after rain depresses prices;
        # waiting a few days typically recovers 10-20% of the price gap.
        return (
            f"{crop} market in {location}: current price is "
            f"Rs.{data['current_price_per_quintal']}/quintal, "
            f"below the seasonal average of Rs.{data['avg_price_per_quintal']}/quintal. "
            f"Prices are currently soft, likely due to wet/damp grain in the market. "
            f"Recommend waiting a few days for prices to recover before selling."
        )

    # ── At or above average ────────────────────────────────────────────────────
    return (
        f"{crop} market in {location}: prices are at or above average "
        f"(Rs.{data['current_price_per_quintal']}/quintal vs avg "
        f"Rs.{data['avg_price_per_quintal']}/quintal). "
        f"A reasonable time to sell."
    )


# ─────────────────────────────────────────────────────────────────────────────
# ADK Agent definition
# ─────────────────────────────────────────────────────────────────────────────

market_watch_agent = Agent(
    # WHY name="market_watch": the orchestrator's system prompt references this
    # exact name when routing price-related queries.  Must match exactly.
    name="market_watch",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=(
        "You are a Market Watch advisor for Indian farmers. "
        "Use the market_advice tool to answer questions about crop prices and selling timing. "
        "Always quote the specific current price and the seasonal average price in Rs/quintal. "
        "Be concise and practical — the farmer needs a clear hold or sell recommendation."
    ),
    tools=[market_advice],
)