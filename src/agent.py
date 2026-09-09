"""
agent.py
--------
Role: Defines the core LangGraph agent (the "Brain") for the Agentic-AI-OS.
It initializes the tool-calling LLM (NVIDIA NIM, falling back to free
OpenRouter models), binds it to the available system tools, and sets up the
ReAct (Reasoning and Acting) loop. This module exposes the `OSAgentSystem`
class, which the UI or CLI can import to process user commands.
"""
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from src.llm_provider import get_llm
from tools import ALL_TOOLS

SYSTEM_PROMPT = SystemMessage(content="""\
You are Agentic-AI-OS, a personal AI operating-system assistant. You control \
the user's local machine through the tools available to you: organizing and \
inspecting files, reading documents, running shell commands, and changing \
system settings.

Guidelines:
- Prefer the most specific tool for the job (e.g. read_document for PDFs/DOCX, \
  not execute_command).
- For requests that need careful reasoning over file contents or ranking \
  results by meaning (e.g. "find the PDF about machine learning"), use \
  think_deeply with the relevant context rather than guessing yourself.
- For requests to run shell/PowerShell commands, use generate_shell_command \
  to produce the exact command, then execute_command to run it.
- Destructive actions (delete_file, move_file, execute_command) always ask \
  the user for confirmation before acting — this is expected and safe; do \
  not try to work around it.
- Be concise. State what you did and the result, not your internal reasoning.
""")

llm = get_llm(task="agent", temperature=0)

os_agent = create_react_agent(llm, tools=ALL_TOOLS, prompt=SYSTEM_PROMPT)

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
            return f"Error processing command: {str(e)}"

if __name__ == "__main__":
    system = OSAgentSystem()
    print("Testing Agent...")
    print("User: What files are in the current directory?")
    response = system.process_command("What files are in the current directory?")
    print(f"Agent: {response}")
