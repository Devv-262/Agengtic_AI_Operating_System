"""
agent.py
--------
Role: Defines the core LangGraph agent (the "Brain") for the Agentic-AI-OS.
It initializes the tool-calling LLM (NVIDIA NIM, falling back to free
OpenRouter models), binds it to the available system tools, and sets up the
ReAct (Reasoning and Acting) loop. This module exposes the `OSAgentSystem`
class, which the UI or CLI can import to process user commands.
"""
import logging

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from src.llm_provider import get_llm
from tools import ALL_TOOLS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = SystemMessage(content="""\
You are Agentic-AI-OS, a personal AI operating-system assistant. You control \
the user's local machine through the tools available to you: organizing and \
inspecting files, reading documents, running shell commands, and changing \
system settings.

Guidelines:
- Prefer the most specific tool for the job (e.g. read_document for PDFs/DOCX, \
  not execute_command).
- For "find the file about X" / "find the PDF I downloaded about Y" style \
  requests, use semantic_search (it finds files by meaning, not just exact \
  filename/keyword matches). If it says the index is empty for that area, \
  run index_directory on the relevant folder first, then search again.
- For other complex reasoning over file contents or ranking results by \
  meaning once you already have the text in hand, use think_deeply with \
  the relevant context rather than guessing yourself.
- For requests to run shell/PowerShell commands, use generate_shell_command \
  to produce the exact command, then execute_command to run it.
- For requests to clean up or organize a folder (e.g. "clean up my \
  Downloads"), use organize_directory rather than moving files one by one \
  yourself — it proposes a full category plan and asks for a single \
  confirmation. If the user wants to reverse it, use undo_last_organize.
- For multi-step batch tasks ("resize these images and zip them"), chain \
  the individual tools yourself (e.g. resize_images then create_archive) \
  rather than asking the user to do it manually.
- Destructive actions (delete_file, move_file, execute_command, \
  organize_directory, undo_last_organize, resize_images, create_archive, \
  extract_archive) always ask the user for confirmation before acting — \
  this is expected and safe; do not try to work around it.
- File tools only operate within the user's home directory tree; if a tool \
  returns a sandbox error, tell the user rather than retrying with a \
  different path.
- Be concise. State what you did and the result, not your internal reasoning.
""")

llm = get_llm(task="agent", temperature=0)

# MemorySaver checkpoints conversation state per thread_id in-process, so the
# agent remembers earlier turns within a running session (e.g. "delete that
# file" referring to something named two turns ago). It does not persist
# across process restarts — see plan.md if that's needed later.
os_agent = create_react_agent(llm, tools=ALL_TOOLS, prompt=SYSTEM_PROMPT, checkpointer=MemorySaver())

class OSAgentSystem:
    def __init__(self):
        self.agent = os_agent
        self.config = {"configurable": {"thread_id": "session_1"}}

    def process_command(self, user_input: str) -> str:
        inputs = {"messages": [("user", user_input)]}
        try:
            result = self.agent.invoke(inputs, config=self.config)
            return result["messages"][-1].content
        except Exception as e:
            logger.exception("Agent failed to process command: %r", user_input)
            return f"Error processing command: {str(e)}"

if __name__ == "__main__":
    system = OSAgentSystem()
    print("Testing Agent...")
    print("User: What files are in the current directory?")
    response = system.process_command("What files are in the current directory?")
    print(f"Agent: {response}")
