"""
Shared LLM client — single source of truth for API configuration.
All agents import from here instead of creating their own clients.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────
MODEL = "llama-3.3-70b-versatile"
BASE_URL = "https://api.groq.com/openai/v1"

# ── Shared client instance ─────────────────────────────────────────
client = OpenAI(
    base_url=BASE_URL,
    api_key=os.environ.get("GROQ_API_KEY")
)
