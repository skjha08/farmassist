---
title: FarmAssist
emoji: 🌾
colorFrom: green
colorTo: yellow
sdk: streamlit
sdk_version: 1.35.0
app_file: app.py
pinned: false
---

# 🌾 FarmAssist - AI Farm Advisor

Multi-agent AI assistant for Indian farmers built with Google ADK and Gemini Vision.

## What it does

- Crop Advisor: weather-aware farming advice (spraying, drainage, yield timing)
- Market Watch: mandi price lookup and selling-timing recommendations
- Pest Scout: upload a crop photo for visual pest/disease diagnosis via Gemini Vision

## Running locally

pip install -r requirements.txt
cp .env.example .env
streamlit run app.py

## Environment variables (HF Space Secrets)

GEMINI_API_KEY  - Required. Gemini API key from Google AI Studio.
GEMINI_MODEL    - Optional. Defaults to gemini-2.0-flash.

Built with Google Agent Development Kit (ADK) as a learning project.
