"""
llm_provider.py
----------------
Role: Builds LangChain chat model clients for the Agentic-AI-OS "Brain".

Both NVIDIA NIM and OpenRouter expose OpenAI-compatible chat-completions APIs,
so a single ChatOpenAI client (pointed at a different base_url/api_key/model)
covers either provider. get_llm(task) returns a NIM-backed model with an
automatic LangChain fallback to the equivalent free OpenRouter model, so a NIM
outage or missing key doesn't take the agent down.
"""
from langchain_openai import ChatOpenAI

from src.config import (
    MODELS,
    NIM_API_KEY,
    NIM_BASE_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)


# Both providers' free tiers rate-limit aggressively; let the OpenAI client's
# own retry/backoff absorb transient 429s/5xxs before we give up on this
# provider and fall through to the other one via with_fallbacks().
_MAX_RETRIES = 2
_REQUEST_TIMEOUT = 30


def _nim_client(model: str, temperature: float) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=NIM_API_KEY,
        base_url=NIM_BASE_URL,
        temperature=temperature,
        max_retries=_MAX_RETRIES,
        timeout=_REQUEST_TIMEOUT,
    )


def _openrouter_client(model: str, temperature: float) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
        max_retries=_MAX_RETRIES,
        timeout=_REQUEST_TIMEOUT,
    )


def get_llm(task: str = "agent", temperature: float = 0):
    """
    Returns a chat model for the given task ("agent", "reasoning", or "coder"),
    backed by NVIDIA NIM with an automatic fallback to the equivalent free
    OpenRouter model if the NIM call fails (missing key, rate limit, outage).
    """
    if task not in MODELS:
        raise ValueError(f"Unknown task '{task}'. Expected one of: {list(MODELS)}")

    nim_model = MODELS[task]["nim"]
    openrouter_model = MODELS[task]["openrouter"]

    primary = _nim_client(nim_model, temperature)
    fallback = _openrouter_client(openrouter_model, temperature)

    return primary.with_fallbacks([fallback])
