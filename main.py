"""
main.py
=======
CLI test entrypoint for FarmAssist — Phase 1.

Run with:
    python main.py

This file demonstrates and verifies the full ADK session lifecycle:
  1. Load API key from .env via python-dotenv
  2. Create InMemoryRunner (which auto-creates its own InMemorySessionService)
  3. Explicitly create a session before calling run_async  ← CRITICAL
  4. Send a message and iterate the async event stream
  5. Print the final response
  6. Handle errors (quota, auth, general) with clear messages

WHY asyncio.run() here (not in the agents):
  ADK's runner.run_async() is an async generator — it must be driven inside
  an event loop.  asyncio.run() creates a fresh loop, runs our coroutine to
  completion, then closes the loop.  This is the standard pattern for
  CLI entry points into async code.
"""

import asyncio
import os
import sys

# ── Step 1: Load .env BEFORE importing any ADK module ────────────────────────
# WHY first: google-adk reads GEMINI_API_KEY from os.environ at import time
# in some internal initialisation paths.  Loading .env after the import could
# mean the key is seen as absent even though it's in the file.
from dotenv import load_dotenv
load_dotenv()  # reads .env from cwd (farmassist/) into os.environ

# ── Guard: fail fast with a clear message depending on auth mode ─────────────
# WHY branch here: we support two auth backends — AI Studio (GEMINI_API_KEY)
# or Vertex AI (GOOGLE_GENAI_USE_VERTEXAI + GOOGLE_CLOUD_PROJECT via ADC).
# Checking only for GEMINI_API_KEY would wrongly fail when running in Vertex
# mode, since Vertex mode uses gcloud application-default credentials instead.
USING_VERTEX = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").strip().upper() == "TRUE"

if USING_VERTEX:
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    if not GOOGLE_CLOUD_PROJECT:
        print(
            "\n[FarmAssist ERROR] GOOGLE_CLOUD_PROJECT is not set.\n"
            "Vertex AI mode requires GOOGLE_CLOUD_PROJECT and "
            "GOOGLE_CLOUD_LOCATION in your .env file, plus credentials from:\n"
            "  gcloud auth application-default login",
            file=sys.stderr,
        )
        sys.exit(1)
else:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    if not GEMINI_API_KEY:
        print(
            "\n[FarmAssist ERROR] GEMINI_API_KEY is not set.\n"
            "Create a .env file in the farmassist/ folder with:\n"
            "  GEMINI_API_KEY=your_actual_key_here\n"
            "Copy .env.example as a starting point.",
            file=sys.stderr,
        )
        sys.exit(1)
        
# ── ADK imports (after load_dotenv so key is in os.environ) ──────────────────
from google.genai.types import Content, Part          # confirmed in source
from google.adk.runners import InMemoryRunner          # confirmed: exists

from agents.orchestrator import orchestrator_agent     # our root agent

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# WHY APP_NAME / USER_ID / SESSION_ID as constants here:
#   create_session() and run_async() must receive the EXACT same string for
#   all three identifiers — a mismatch causes a session-not-found error.
#   Centralising them as module-level constants prevents typos across calls.
APP_NAME = "farmassist"
USER_ID = "farmer_001"
SESSION_ID = "session_phase1"

# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

# WHY InMemoryRunner (not Runner):
#   InMemoryRunner bundles InMemorySessionService + InMemoryArtifactService
#   internally — no external database or file system needed.  Perfect for
#   development and CI.  In production (Phase 5+) swap to the base Runner
#   with a persistent session store.
#
# WHY agent= not node=:
#   We have an LlmAgent (not a workflow graph node).  The `agent` parameter
#   is the correct one — confirmed in InMemoryRunner.__init__ source.
runner = InMemoryRunner(agent=orchestrator_agent, app_name=APP_NAME)


# ─────────────────────────────────────────────────────────────────────────────
# Core async function
# ─────────────────────────────────────────────────────────────────────────────

async def run_query(query: str) -> None:
    """
    Sends a single query to the orchestrator and prints the response.

    Session lifecycle (WHY explicit create_session):
      InMemoryRunner does NOT auto-create sessions.  If you call run_async()
      without a prior create_session(), ADK raises a KeyError / session not
      found error.  The session must exist before the first message is sent.

      Signature confirmed from source inspection:
        create_session(app_name, user_id, state=None, session_id=None)
    """
    print(f"\n[FarmAssist] Query: {query}\n{'─' * 60}")

    # ── Create session ────────────────────────────────────────────────────────
    # WHY await: create_session is a coroutine in InMemorySessionService
    await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    # ── Build the message ─────────────────────────────────────────────────────
    # WHY Content(role="user", ...): ADK requires a google.genai.types.Content
    # object for new_message.  role="user" marks it as the human turn.
    # Confirmed: run_async(new_message=...) expects this type.
    message = Content(role="user", parts=[Part(text=query)])

    # ── Stream events ─────────────────────────────────────────────────────────
    # WHY async for: run_async() is an async generator that yields Event
    # objects as the agent thinks, calls tools, and finally responds.
    # We only print when event.is_final_response() is True to avoid printing
    # intermediate tool-call events.
    try:
        final_printed = False
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=message,
        ):
            # event.is_final_response() — confirmed exists in Event source:
            #   returns True when there are no pending function calls,
            #   no partial streaming chunks, and no trailing code execution.
            if event.is_final_response():
                # event.content is Optional[types.Content] (from LlmResponse)
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(f"[FarmAssist Response]\n{part.text}")
                            final_printed = True

        if not final_printed:
            print("[FarmAssist] No text response received from the agent.")

    except Exception as exc:
        # ── Error handling with clear, actionable messages ────────────────────
        # WHY catch by string pattern (not import): google-api-core may not be
        # installed as a direct dep; matching the repr is safer than importing
        # ResourceExhausted directly.
        err_str = str(exc)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            print(
                "\n[FarmAssist ERROR] API quota exceeded (HTTP 429).\n"
                "You have hit the Gemini free-tier rate limit.\n"
                "Wait 60 seconds and try again, or check your quota at:\n"
                "  https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas",
                file=sys.stderr,
            )
        elif "401" in err_str or "API_KEY_INVALID" in err_str or "UNAUTHENTICATED" in err_str:
            print(
                "\n[FarmAssist ERROR] Authentication failed.\n"
                "Check that GEMINI_API_KEY in your .env is correct and active.\n"
                f"Raw error: {exc}",
                file=sys.stderr,
            )
        else:
            print(
                f"\n[FarmAssist ERROR] Unexpected error: {exc}",
                file=sys.stderr,
            )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Phase 1 test query — matches the Definition of Done in the spec.
    # Expected: response mentions rain delay + drainage + selling/mandi timing.
    TEST_QUERY = (
        "I'm growing wheat in Punjab. It's been raining for 3 days. "
        "What should I do?"
    )
    asyncio.run(run_query(TEST_QUERY))
