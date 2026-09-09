"""
tools/reasoning.py
-------------------
Role: Exposes the specialist models (reasoning, coder) as tools the main
agent-loop model can call out to for sub-tasks they're individually better
at, rather than doing everything with the tool-calling model.
"""
import platform
from typing import Optional

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

from src.llm_provider import get_llm

_DEFAULT_SHELL_BY_OS = {
    "Windows": "powershell",
    "Darwin": "bash",
    "Linux": "bash",
}


def _detect_shell() -> str:
    return _DEFAULT_SHELL_BY_OS.get(platform.system(), "bash")

@tool
def think_deeply(question: str, context: str) -> str:
    """
    Hands a complex reasoning, summarization, or semantic-ranking sub-task to
    a stronger reasoning model. Use this for things like "summarize this
    document and answer a question about it" or "rank these files by how
    semantically relevant they are to a query" — pass the raw context (file
    contents, file lists, etc.) and the question to answer about it.
    """
    llm = get_llm("reasoning", temperature=0.2)
    messages = [
        SystemMessage(content="You are a careful reasoning assistant. Answer precisely and concisely based only on the given context."),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"),
    ]
    response = llm.invoke(messages)
    return response.content

@tool
def generate_shell_command(natural_language_request: str, target_shell: Optional[str] = None) -> str:
    """
    Translates a natural-language request into a single, correct shell
    command using a coding-specialist model. Returns ONLY the command text
    — pass it to execute_command to actually run it (which will ask for
    confirmation). target_shell defaults to the shell native to this host
    OS (PowerShell on Windows, bash on macOS/Linux); only pass it
    explicitly if the user asks for a specific shell.
    """
    shell = target_shell or _detect_shell()
    llm = get_llm("coder", temperature=0)
    messages = [
        SystemMessage(
            content=(
                f"You translate natural-language requests into a single correct {shell} "
                "command. Reply with ONLY the command, no explanation, no markdown fences."
            )
        ),
        HumanMessage(content=natural_language_request),
    ]
    response = llm.invoke(messages)
    return response.content.strip().strip("`")

reasoning_tools = [think_deeply, generate_shell_command]
