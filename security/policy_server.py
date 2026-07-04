"""
policy_server.py
=================
Defines which tools/agents are permitted for a given role.

WHY a separate policy file (not hardcoded in orchestrator.py):
  Separating "what's allowed" from "how agents work" means permissions can
  change without touching agent logic — standard security design pattern
  (principle of least privilege, centralised policy).
"""

# WHY a dict keyed by role: FarmAssist currently has one role (farmer), but
# this structure supports adding an "admin" or "extension_officer" role later
# (e.g. to unlock a bulk-diagnosis tool) without restructuring the policy.
ROLE_PERMISSIONS = {
    "farmer": [
        "crop_advisor",
        "market_watch",
        "pest_scout",
    ],
}

DEFAULT_ROLE = "farmer"


def get_allowed_tools(role: str = DEFAULT_ROLE) -> list:
    """Returns the list of tool/agent names permitted for a given role."""
    return ROLE_PERMISSIONS.get(role, [])