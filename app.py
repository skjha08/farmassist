import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from google.genai.types import Content, Part
from google.adk.runners import InMemoryRunner
from google.adk.errors.already_exists_error import AlreadyExistsError
from agents.orchestrator import orchestrator_agent
from security.guardrails import validate_input, validate_image_path

st.set_page_config(page_title="FarmAssist", page_icon="🌾")
st.title("🌾 FarmAssist — AI Farm Advisor")
st.caption("Ask about crops, weather, market prices, or upload a photo for pest/disease diagnosis.")

if "runner" not in st.session_state:
    st.session_state.runner = InMemoryRunner(agent=orchestrator_agent, app_name="farmassist_ui")
    st.session_state.session_id = "ui_session"
    st.session_state.history = []

async def ensure_session():
    try:
        await st.session_state.runner.session_service.create_session(
            app_name="farmassist_ui", user_id="ui_user", session_id=st.session_state.session_id
        )
    except AlreadyExistsError:
        pass

async def get_response(query: str, image_bytes=None, mime_type=None):
    await ensure_session()
    parts = [Part(text=query)]
    if image_bytes:
        parts.append(Part.from_bytes(data=image_bytes, mime_type=mime_type))
    message = Content(role="user", parts=parts)
    final_text = ""
    async for event in st.session_state.runner.run_async(
        user_id="ui_user", session_id=st.session_state.session_id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text += part.text
    return final_text

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

uploaded_image = st.file_uploader("Upload a crop photo (optional)", type=["jpg", "jpeg", "png"])
query = st.chat_input("Ask FarmAssist...")

if query:
    is_valid, reason = validate_input(query)
    if not is_valid:
        st.error(f"Blocked: {reason}")
    else:
        st.session_state.history.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        image_bytes, mime_type = None, None
        if uploaded_image:
            image_bytes = uploaded_image.read()
            mime_type = uploaded_image.type

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = asyncio.run(get_response(query, image_bytes, mime_type))
                    st.markdown(response)
                    st.session_state.history.append({"role": "assistant", "content": response})
                except Exception as e:
                    err = str(e)
                    if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                        st.warning(
                            "⏳ **API rate limit reached** — the free-tier Gemini quota is "
                            "exhausted for this minute/day. Please wait 30–60 seconds and "
                            "try again, or check quota at "
                            "[Google AI Studio](https://aistudio.google.com/).",
                            icon="⚠️",
                        )
                    elif "401" in err or "API_KEY_INVALID" in err or "UNAUTHENTICATED" in err:
                        st.error("🔑 Authentication failed — check that GEMINI_API_KEY is set correctly in Space Secrets.")
                    else:
                        st.error(f"❌ Unexpected error: {e}")

# ── Sidebar: model info & limits note ────────────────────────────────────────
with st.sidebar:
    st.markdown("### ℹ️ About FarmAssist")
    st.markdown(
        "Multi-agent AI advisor for Indian farmers built with "
        "**Google ADK** + **Gemini Vision**.\n\n"
        "**Agents:**\n"
        "- 🌱 Crop Advisor\n"
        "- 📈 Market Watch\n"
        "- 🔍 Pest Scout (vision)\n\n"
        "**Note:** Running on Gemini free tier. "
        "If you see a rate-limit warning, wait ~60 s and retry."
    )