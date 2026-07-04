import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from google.genai.types import Content, Part
from google.adk.runners import InMemoryRunner
from google.adk.errors.already_exists_error import AlreadyExistsError
from agents.orchestrator import orchestrator_agent
from security.guardrails import validate_input

st.set_page_config(
    page_title="FarmAssist — AI Farm Advisor",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
#MainMenu,footer,header{visibility:hidden}
.stApp{background:linear-gradient(135deg,#0a1a0f 0%,#0d2118 50%,#0a1a0f 100%)}
.hero{
    background:linear-gradient(135deg,#1a4a2e,#2d7a4f,#1a4a2e);
    border:1px solid rgba(76,175,80,.3);border-radius:16px;
    padding:2rem 2.5rem;margin-bottom:1.5rem;
    box-shadow:0 8px 32px rgba(0,0,0,.4);
}
.badge{
    display:inline-block;background:rgba(76,175,80,.2);
    border:1px solid rgba(76,175,80,.4);border-radius:20px;
    padding:.2rem .8rem;font-size:.72rem;color:#81c784;
    margin-bottom:.8rem;font-weight:500;letter-spacing:.5px;
}
.htitle{font-size:2.2rem;font-weight:700;color:#e8f5e9;margin:0}
.hsub{font-size:.95rem;color:rgba(200,230,210,.7);margin:.4rem 0 0}
.cards{display:flex;gap:.75rem;margin-bottom:1.5rem;flex-wrap:wrap}
.card{
    flex:1;min-width:160px;background:rgba(255,255,255,.04);
    border:1px solid rgba(76,175,80,.2);border-radius:12px;
    padding:1rem 1.2rem;transition:all .2s;
}
.card:hover{background:rgba(76,175,80,.08);border-color:rgba(76,175,80,.4);transform:translateY(-2px)}
.ci{font-size:1.8rem;margin-bottom:.4rem}
.ct{font-size:.85rem;font-weight:600;color:#a5d6a7;margin-bottom:.2rem}
.cd{font-size:.75rem;color:rgba(200,230,210,.55);line-height:1.4}
.ulabel{font-size:.85rem;color:#81c784;font-weight:500;margin-bottom:.5rem}
.gdiv{height:1px;background:linear-gradient(90deg,transparent,rgba(76,175,80,.3),transparent);margin:1.2rem 0}
.sa{
    display:flex;align-items:flex-start;gap:.75rem;padding:.75rem;
    background:rgba(76,175,80,.06);border:1px solid rgba(76,175,80,.15);
    border-radius:10px;margin-bottom:.6rem;
}
.si{font-size:1.4rem;flex-shrink:0}
.sn{font-size:.82rem;font-weight:600;color:#a5d6a7}
.sr{font-size:.73rem;color:rgba(165,214,167,.6);margin-top:.15rem;line-height:1.3}
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0d2118,#091510)!important;
    border-right:1px solid rgba(76,175,80,.15)!important;
}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-thumb{background:rgba(76,175,80,.3);border-radius:4px}
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────────────────
if "runner" not in st.session_state:
    st.session_state.runner = InMemoryRunner(agent=orchestrator_agent, app_name="farmassist_ui")
    st.session_state.session_id = "ui_session"
    st.session_state.history = []

# ── ADK helpers ──────────────────────────────────────────────────────────────
async def ensure_session():
    try:
        await st.session_state.runner.session_service.create_session(
            app_name="farmassist_ui", user_id="ui_user",
            session_id=st.session_state.session_id
        )
    except AlreadyExistsError:
        pass

async def get_response(query: str, image_bytes=None, mime_type=None) -> str:
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

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:1rem 0 .5rem'>"
        "<div style='font-size:2.5rem'>🌾</div>"
        "<div style='font-size:1.1rem;font-weight:700;color:#a5d6a7'>FarmAssist</div>"
        "<div style='font-size:.72rem;color:rgba(165,214,167,.55);margin-top:.2rem'>AI Farm Advisor</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='gdiv'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:.78rem;font-weight:600;color:#81c784;"
        "letter-spacing:.8px;margin-bottom:.6rem'>ACTIVE AGENTS</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sa'><div class='si'>🌱</div><div>"
        "<div class='sn'>Crop Advisor</div>"
        "<div class='sr'>Weather-aware advice on spraying, drainage &amp; field ops</div>"
        "</div></div>"
        "<div class='sa'><div class='si'>📈</div><div>"
        "<div class='sn'>Market Watch</div>"
        "<div class='sr'>Mandi prices and optimal selling timing</div>"
        "</div></div>"
        "<div class='sa'><div class='si'>🔬</div><div>"
        "<div class='sn'>Pest Scout</div>"
        "<div class='sr'>Gemini Vision diagnoses pests &amp; diseases from photos</div>"
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='gdiv'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:.78rem;font-weight:600;color:#81c784;"
        "letter-spacing:.8px;margin-bottom:.6rem'>TRY ASKING</div>",
        unsafe_allow_html=True,
    )
    for ex in [
        "🌧 Raining in Punjab — when to spray?",
        "💰 Good time to sell wheat in Haryana?",
        "📷 Upload a leaf photo for diagnosis",
    ]:
        st.markdown(
            f"<div style='font-size:.78rem;color:rgba(200,230,210,.6);"
            f"padding:.35rem 0;border-bottom:1px solid rgba(76,175,80,.08)'>{ex}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div class='gdiv'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:.72rem;color:rgba(165,214,167,.45);line-height:1.6'>"
        "Built with <strong style='color:#81c784'>Google ADK</strong> · Gemini 2.0 Flash<br>"
        "Multi-agent · Vision · Security guardrails<br><br>"
        "⚠️ Free-tier quota: wait 60s if rate-limited.</div>",
        unsafe_allow_html=True,
    )

# ── Main ─────────────────────────────────────────────────────────────────────
col_main, _ = st.columns([3, 0.01])
with col_main:
    # Hero header
    st.markdown(
        "<div class='hero'>"
        "<div class='badge'>● POWERED BY GOOGLE ADK + GEMINI VISION</div>"
        "<div class='htitle'>🌾 FarmAssist</div>"
        "<div class='hsub'>Multi-agent AI advisor for Indian farmers — "
        "crop management, market prices &amp; pest diagnosis</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Agent capability cards
    st.markdown(
        "<div class='cards'>"
        "<div class='card'><div class='ci'>🌱</div>"
        "<div class='ct'>Crop Advisor</div>"
        "<div class='cd'>Weather-aware advice on spraying, drainage &amp; field operations</div></div>"
        "<div class='card'><div class='ci'>📈</div>"
        "<div class='ct'>Market Watch</div>"
        "<div class='cd'>Live mandi prices and optimal selling timing</div></div>"
        "<div class='card'><div class='ci'>🔬</div>"
        "<div class='ct'>Pest Scout</div>"
        "<div class='cd'>Upload a photo — Gemini Vision identifies disease &amp; treatment</div></div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Chat history
    if not st.session_state.history:
        st.markdown(
            "<div style='text-align:center;padding:2.5rem;color:rgba(165,214,167,.35)'>"
            "<div style='font-size:2.5rem;margin-bottom:.5rem'>💬</div>"
            "<div style='font-size:.9rem'>Ask your first question below, or upload a crop photo to start</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state.history:
            av = "👨‍🌾" if msg["role"] == "user" else "🌾"
            with st.chat_message(msg["role"], avatar=av):
                st.markdown(msg["content"])

    st.markdown("<div class='gdiv'></div>", unsafe_allow_html=True)

    # Image uploader
    st.markdown(
        "<div class='ulabel'>📷 Attach a crop photo for pest/disease diagnosis (optional)</div>",
        unsafe_allow_html=True,
    )
    uploaded_image = st.file_uploader(
        label="crop_photo",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
        help="Upload a clear photo of the affected leaf or plant.",
    )
    if uploaded_image:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(uploaded_image, caption="Uploaded", use_container_width=True)
        with c2:
            st.markdown(
                f"<div style='padding:.75rem;background:rgba(76,175,80,.08);"
                f"border:1px solid rgba(76,175,80,.2);border-radius:10px;margin-top:.5rem'>"
                f"<div style='font-size:.8rem;color:#81c784;font-weight:600'>📷 Photo ready</div>"
                f"<div style='font-size:.75rem;color:rgba(165,214,167,.6);margin-top:.3rem'>"
                f"File: <strong>{uploaded_image.name}</strong><br>"
                f"Pest Scout will analyze this with your question.</div></div>",
                unsafe_allow_html=True,
            )

    # Chat input
    query = st.chat_input("Ask FarmAssist — crops, weather, prices, or describe your problem...")

    if query:
        is_valid, reason = validate_input(query)
        if not is_valid:
            st.error(f"🛡️ Blocked by safety filter: {reason}")
        else:
            st.session_state.history.append({"role": "user", "content": query})
            with st.chat_message("user", avatar="👨‍🌾"):
                st.markdown(query)

            image_bytes, mime_type = None, None
            if uploaded_image:
                uploaded_image.seek(0)
                image_bytes = uploaded_image.read()
                mime_type = uploaded_image.type

            with st.chat_message("assistant", avatar="🌾"):
                spin = "🤔 Consulting agents" + (" + analyzing photo..." if image_bytes else "...")
                with st.spinner(spin):
                    try:
                        response = asyncio.run(get_response(query, image_bytes, mime_type))
                        st.markdown(response)
                        st.session_state.history.append({"role": "assistant", "content": response})
                    except Exception as e:
                        err = str(e)
                        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                            st.warning(
                                "⏳ **API rate limit reached** — free-tier quota exhausted. "
                                "Wait 30–60 s and retry.",
                                icon="⚠️",
                            )
                        elif "401" in err or "API_KEY_INVALID" in err or "UNAUTHENTICATED" in err:
                            st.error("🔑 Auth failed — check GEMINI_API_KEY in Space Secrets.")
                        else:
                            st.error(f"❌ Unexpected error: {e}")
            st.rerun()
