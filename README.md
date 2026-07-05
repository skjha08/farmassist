---
title: FarmAssist
emoji: 🌾
colorFrom: green
colorTo: yellow
sdk: streamlit
sdk_version: "1.42.0"
app_file: app.py
pinned: false
---

# 🌾 FarmAssist — AI Farm Advisor for Indian Farmers

> Multi-agent AI assistant built with **Google Agent Development Kit (ADK)** and **Gemini Vision**.  
> Helps Indian farmers with crop management, mandi market prices, and pest/disease diagnosis from photos.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.3.0-4285F4?logo=google&logoColor=white)](https://google.github.io/adk-docs/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-HF%20Spaces-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/spaces/shivam-hf/farmassist)

---

## 🌍 Problem Statement

Indian smallholder farmers (average land holding: 1.1 hectares) lose significant income every season due to:
- **Mistimed field operations** — spraying or fertilising right before rain washes inputs away
- **Selling at wrong times** — taking produce to the mandi when prices are depressed due to damp grain in the market
- **Delayed pest response** — not knowing what a disease is or how to treat it affordably until crop damage is extensive

Access to agricultural extension officers is limited (1 officer per ~800 farmers in many Indian states). FarmAssist puts AI-powered advisory in the hands of farmers via a simple chat + photo interface.

---

## 🤖 Why Agents?

A single LLM prompt cannot solve this problem well because:
- **Domain separation matters** — crop advice, market timing, and pest diagnosis require different expertise and different tools
- **Multi-topic queries are common** — "It's raining and prices are low — should I spray and sell?" requires combining weather-aware agronomic advice *and* market data
- **Tools must be independently testable** — each specialist agent has its own tool, test cases, and pass/fail criteria

The agent architecture routes each query to the right specialist(s) and combines their outputs into a single coherent answer.

---

## 🏗️ Architecture

```
User (Streamlit UI / CLI)
        │
        ▼
  ┌─────────────────────────────────────────┐
  │       Security Guardrails Layer         │
  │  (prompt injection filter, path         │
  │   traversal protection, length check)   │
  └──────────────────┬──────────────────────┘
                     │  validated query
                     ▼
  ┌─────────────────────────────────────────┐
  │       Orchestrator Agent                │
  │  (Gemini 2.0 Flash + Vision)            │
  │  Reads image → describes → routes       │
  └──────┬─────────────┬──────────┬─────────┘
         │             │          │
   AgentTool      AgentTool   AgentTool
         │             │          │
         ▼             ▼          ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │  Crop    │  │ Market   │  │  Pest    │
  │ Advisor  │  │  Watch   │  │  Scout   │
  │          │  │          │  │          │
  │ crop_    │  │ market_  │  │ get_pest_│
  │ advice() │  │ advice() │  │treatment │
  └──────────┘  └──────────┘  └──────────┘
         │
         ▼
  ┌─────────────────┐
  │   MCP Server    │  ← same tools exposed over
  │ mcp_server.py   │    Model Context Protocol
  └─────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **`AgentTool` (not `sub_agents`)** | Gives the orchestrator function-calling control — it can invoke multiple agents in one turn for mixed queries |
| **Vision at orchestrator level** | ADK's `AgentTool` passes text between agents; images are visible only to the orchestrator, which describes them before forwarding to Pest Scout |
| **Guardrails as a separate module** | Security logic is independently testable and runs *before* any query reaches the LLM |
| **MCP server alongside ADK agents** | Exposes the same tools over the Model Context Protocol so any MCP-compatible client can call them without knowledge of FarmAssist's internal architecture |
| **Mock data for weather and prices** | No free, reliable Agmarknet/IMD API was available; the architecture is designed so real API calls are a drop-in replacement |

---

## 📁 Project Structure

```
farmassist/
├── agents/
│   ├── orchestrator.py     # Root agent — routing + vision + synthesis
│   ├── crop_advisor.py     # Weather-aware crop management advice
│   ├── market_watch.py     # Mandi price lookup and selling timing
│   ├── pest_scout.py       # Pest/disease diagnosis from symptom text
│   └── __init__.py
├── security/
│   ├── guardrails.py       # Input validation (injection, traversal, length)
│   ├── policy_server.py    # Role-based tool allow-list
│   └── __init__.py
├── tests/
│   └── eval_harness.py     # Non-deterministic evaluation suite
├── .github/
│   └── workflows/ci.yml    # GitHub Actions CI (lint + import checks)
├── app.py                  # Streamlit UI (primary deployable interface)
├── main.py                 # CLI entrypoint (agent skills demo)
├── mcp_server.py           # MCP server (exposes tools over MCP protocol)
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Running Locally

### Prerequisites
- Python 3.10+
- A Google Gemini API key ([get one free](https://aistudio.google.com/)) **or** a GCP project with Vertex AI enabled

### 1. Clone & install
```bash
git clone https://github.com/skjha08/farmassist.git
cd farmassist
pip install -r requirements.txt
```

### 2. Configure credentials

**Option A — Gemini API Key (AI Studio, free tier):**
```bash
cp .env.example .env
# Edit .env and set:
#   GEMINI_API_KEY=your_key_here
```

**Option B — Vertex AI (GCP, higher quotas):**
```bash
# In .env:
#   GOOGLE_GENAI_USE_VERTEXAI=TRUE
#   GOOGLE_CLOUD_PROJECT=your-project-id
#   GOOGLE_CLOUD_LOCATION=us-central1
gcloud auth application-default login
```

### 3. Run the Streamlit UI
```bash
streamlit run app.py
```
Open http://localhost:8501 in your browser.

### 4. Run the CLI (agent skills demo)
```bash
python main.py
```

### 5. Run the MCP server
```bash
python mcp_server.py
# Starts a stdio-transport MCP server exposing crop_advice,
# market_advice, and get_pest_treatment as MCP tools.
```

### 6. Run the evaluation suite
```bash
python tests/eval_harness.py
# Runs 3 test cases × 3 runs each and reports pass rates.
# Requires a valid Gemini / Vertex AI credential.
```

---

## 🧑‍🤝‍🧑 Agent Capabilities

### 🌱 Crop Advisor
**Tool:** `crop_advice(crop, location)`  
Returns weather-aware farming advice with three specific action items:
- Whether to spray / fertilise (or delay)
- Drainage check instructions
- Whether to hold or move produce to market

### 📈 Market Watch
**Tool:** `market_advice(crop, location)`  
Returns current mandi price vs seasonal average with a clear hold/sell recommendation and specific Rs/quintal figures.

### 🔬 Pest Scout
**Tool:** `get_pest_treatment(symptoms)`  
Maps symptom descriptions (holes, spots, wilting, discolouration) to:
- Diagnosis (insect damage / fungal / wilt / general)
- Affordable treatment options (neem-based first, chemical as fallback)
- Urgency guidance

### 🛡️ Security Layer
- **Prompt injection filter** — blocks "ignore previous instructions" and jailbreak patterns before they reach the LLM
- **Path traversal protection** — validates image file paths
- **Length check** — rejects queries over 2,000 characters
- **Role-based tool allow-list** — `policy_server.py` defines which tools each role may call

### 🔌 MCP Server
`mcp_server.py` exposes all three tool functions over the **Model Context Protocol**, making them callable from any MCP-compatible client (Claude Desktop, ADK `MCPToolset`, Agents CLI) without knowledge of FarmAssist's internal multi-agent structure.

---

## 🌐 Live Demo

**Hugging Face Spaces:** https://huggingface.co/spaces/shivam-hf/farmassist

> ⚠️ The live demo runs on Gemini free-tier. If you see a rate-limit message, wait 30–60 seconds and retry.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Agent framework | Google Agent Development Kit (ADK) 2.3.0 |
| LLM / Vision | Gemini 2.0 Flash (via Vertex AI or AI Studio) |
| MCP protocol | `mcp` Python SDK ≥ 1.0 |
| UI | Streamlit |
| Deployment | Hugging Face Spaces |
| CI | GitHub Actions |
| Auth | python-dotenv + GCP Application Default Credentials |

---

## 📜 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | If using AI Studio | API key from [aistudio.google.com](https://aistudio.google.com/) |
| `GOOGLE_GENAI_USE_VERTEXAI` | If using Vertex | Set to `TRUE` to use Vertex AI instead of AI Studio |
| `GOOGLE_CLOUD_PROJECT` | If Vertex | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | If Vertex | Region (e.g. `us-central1`) |
| `GEMINI_MODEL` | No | Model override. Defaults to `gemini-2.0-flash` |

---

## 🔒 Security Note

**No API keys or credentials are committed to this repository.**  
`.env` and `ci-key.json` are in `.gitignore`.  
In HF Spaces, secrets are set via the Space Secrets UI and injected as environment variables at runtime.
