"""
config.py
---------
Role: Handles environment variables and configuration loading for the Agentic-AI-OS.
It loads secrets from the .env file and exposes them as constants used throughout
the application, including which LLM provider/model backs each task the agent
performs.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Provider credentials
# ---------------------------------------------------------------------------
# NVIDIA NIM (https://build.nvidia.com) - OpenAI-compatible endpoint, primary.
NIM_API_KEY = os.getenv("NIM_API_KEY")
NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

# OpenRouter (https://openrouter.ai) - OpenAI-compatible endpoint, fallback.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# ---------------------------------------------------------------------------
# Task -> model routing
# ---------------------------------------------------------------------------
# Each task has a NIM model id and an OpenRouter (free-tier) fallback model id.
# Override any of these via .env without touching code.
MODELS = {
    "agent": {
        "nim": os.getenv("MODEL_AGENT_NIM", "meta/llama-3.3-70b-instruct"),
        "openrouter": os.getenv("MODEL_AGENT_OPENROUTER", "meta-llama/llama-3.3-70b-instruct:free"),
    },
    "reasoning": {
        "nim": os.getenv("MODEL_REASONING_NIM", "nvidia/llama-3.1-nemotron-70b-instruct"),
        "openrouter": os.getenv("MODEL_REASONING_OPENROUTER", "nvidia/llama-3.1-nemotron-70b-instruct:free"),
    },
    "coder": {
        "nim": os.getenv("MODEL_CODER_NIM", "qwen/qwen2.5-coder-32b-instruct"),
        "openrouter": os.getenv("MODEL_CODER_OPENROUTER", "qwen/qwen-2.5-coder-32b-instruct:free"),
    },
}

# Require explicit confirmation before running destructive tools
# (file delete/move, shell commands). Defaults on; set to "false" to disable
# for non-interactive use (not recommended).
REQUIRE_CONFIRMATION = os.getenv("REQUIRE_CONFIRMATION", "true").lower() != "false"
