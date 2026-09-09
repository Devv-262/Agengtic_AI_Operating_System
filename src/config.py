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
# Each task has a NIM model id and an OpenRouter fallback model id. The
# OpenRouter fallback defaults to "openrouter/free", OpenRouter's own router
# alias that auto-selects among currently-available free models filtered by
# required capabilities (e.g. tool calling) — chosen over pinning a specific
# free model because OpenRouter's free-tier roster is volatile (whole free
# model families have gone dark before), which would otherwise undermine the
# fallback's entire purpose. Override any of these via .env without touching
# code. See plan.md's "Operational note" if a model here goes stale again.
MODELS = {
    "agent": {
        "nim": os.getenv("MODEL_AGENT_NIM", "nvidia/nemotron-3-super-120b-a12b"),
        "openrouter": os.getenv("MODEL_AGENT_OPENROUTER", "openrouter/free"),
    },
    "reasoning": {
        "nim": os.getenv("MODEL_REASONING_NIM", "nvidia/nemotron-3-ultra-550b-a55b"),
        "openrouter": os.getenv("MODEL_REASONING_OPENROUTER", "openrouter/free"),
    },
    "coder": {
        "nim": os.getenv("MODEL_CODER_NIM", "qwen/qwen2.5-coder-32b-instruct"),
        "openrouter": os.getenv("MODEL_CODER_OPENROUTER", "openrouter/free"),
    },
}

# Require explicit confirmation before running destructive tools
# (file delete/move, shell commands). Defaults on; set to "false" to disable
# for non-interactive use (not recommended).
REQUIRE_CONFIRMATION = os.getenv("REQUIRE_CONFIRMATION", "true").lower() != "false"

# ---------------------------------------------------------------------------
# File tool sandboxing
# ---------------------------------------------------------------------------
# File tools (read/move/delete/organize) refuse to touch paths outside these
# roots. Defaults to the user's own profile folders. Override via .env with a
# comma-separated list of absolute paths. Set ENABLE_PATH_SANDBOX=false to
# disable entirely (not recommended).
ENABLE_PATH_SANDBOX = os.getenv("ENABLE_PATH_SANDBOX", "true").lower() != "false"

_home = os.path.expanduser("~")
_default_roots = [
    _home,
    os.path.join(_home, "Desktop"),
    os.path.join(_home, "Downloads"),
    os.path.join(_home, "Documents"),
]
_roots_env = os.getenv("ALLOWED_ROOTS")
ALLOWED_ROOTS = (
    [p.strip() for p in _roots_env.split(",") if p.strip()]
    if _roots_env
    else _default_roots
)

# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------
# Local ChromaDB persisted index (embeddings computed on-device via
# chromadb's bundled ONNX MiniLM model — no API key or network call needed
# for embedding, keeping search available even if both LLM providers are down).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", os.path.join(_PROJECT_ROOT, "memory", "vector_store"))
SEMANTIC_INDEX_MAX_CHARS = int(os.getenv("SEMANTIC_INDEX_MAX_CHARS", "8000"))
