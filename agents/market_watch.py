import os
from google.adk.agents import Agent


def get_mock_market_price(crop: str, location: str) -> dict:
    """Mock commodity price lookup — replace with real Agmarknet API later.
    Returns a fixed scenario: prices are currently low due to wet conditions."""
    return {
        "crop": crop,
        "location": location,
        "current_price_per_quintal": 2100,
        "avg_price_per_quintal": 2350,
        "trend": "below_average",
    }


def market_advice(crop: str, location: str) -> str:
    """Tool: given a crop and location, fetch market price (mocked) and advise on selling timing."""
    data = get_mock_market_price(crop, location)
    if data["trend"] == "below_average":
        return (
            f"{crop} market in {location}: current price is Rs.{data['current_price_per_quintal']}/quintal, "
            f"below the average of Rs.{data['avg_price_per_quintal']}/quintal. "
            f"Prices are currently soft, likely due to wet/damp grain in the market. "
            f"Recommend waiting a few days for prices to recover before selling."
        )
    return f"{crop} market in {location}: prices are at or above average, a reasonable time to sell."


market_watch_agent = Agent(
    name="market_watch",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=(
        "You are a Market Watch advisor for Indian farmers. Use the market_advice "
        "tool to answer questions about crop prices and selling timing. Be concise "
        "and practical."
    ),
    tools=[market_advice],
)