"""
Thin wrapper around Groq's OpenAI-compatible API.

Groq is used because:
  - it's free (no credit card) with generous rate limits
  - it supports real, native tool/function calling in the same shape as OpenAI
  - it's fast, so iterating on the agent loop and running 10+ examples is quick

Get a free key at https://console.groq.com/keys and put it in a .env file
(copy .env.example -> .env and fill it in).

To switch providers later (e.g. to Google Gemini), you only need to change
this file -- agent.py and tools.py are provider-agnostic.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_api_key = os.environ.get("GROQ_API_KEY")

if not _api_key or _api_key == "your_key_here":
    raise RuntimeError(
        "GROQ_API_KEY is not set. Copy .env.example to .env and add a free key "
        "from https://console.groq.com/keys"
    )

client = OpenAI(
    api_key=_api_key,
    base_url="https://api.groq.com/openai/v1",
)

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
