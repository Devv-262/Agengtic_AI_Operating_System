"""
main.py
-------
Role: Main entry point for the Agentic-AI-OS.
      Boots the application, initialises the OSAgentSystem, and hands control
      to the interactive REPL loop.  The loop reads user input, forwards it to
      the agent, and prints the response until the user types 'exit' or 'quit'.
"""

import sys
import os

# ---------------------------------------------------------------------------
# Path setup – make sure 'src' sibling imports resolve correctly when this
# file is run directly (python src/main.py) OR from the project root
# (python -m src.main).
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------
from src.config import GROQ_API_KEY
from src.agent import OSAgentSystem

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_NAME    = "Agentic-AI-OS"
APP_VERSION = "0.1.0"
DIVIDER     = "─" * 60
EXIT_CMDS   = {"exit", "quit", "q", ":q"}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _print_banner() -> None:
    """Print a startup banner to the terminal."""
    print(DIVIDER)
    print(f"  🤖  {APP_NAME}  v{APP_VERSION}")
    print(f"  Powered by Groq (Llama 3) + LangGraph ReAct Agent")
    print(DIVIDER)
    print("  Type your command in plain English.")
    print("  Type 'exit' / 'quit' / 'q' to shut down.")
    print(DIVIDER)
    print()


def _validate_env() -> bool:
    """
    Sanity-check that required environment variables are present.
    Returns True if everything is fine, False otherwise.
    """
    if not GROQ_API_KEY:
        print("[ERROR] GROQ_API_KEY is not set.")
        print("        Copy .env.example → .env and add your key, then retry.")
        return False
    return True


# ---------------------------------------------------------------------------
# Core REPL loop
# ---------------------------------------------------------------------------

def run_repl(agent: OSAgentSystem) -> None:
    """
    Blocking read-eval-print loop.
    Keeps running until the user sends an exit command or hits Ctrl-C / Ctrl-D.
    """
    while True:
        try:
            user_input = input("You › ").strip()
        except (EOFError, KeyboardInterrupt):
            # Ctrl-D or Ctrl-C – clean shutdown
            print("\n\n  Goodbye! 👋")
            break

        if not user_input:
            continue  # ignore blank lines

        if user_input.lower() in EXIT_CMDS:
            print("\n  Goodbye! 👋")
            break

        print()  # breathing room
        response = agent.process_command(user_input)
        print(f"Agent › {response}")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Bootstrap the OS Agent and enter the interactive REPL."""
    _print_banner()

    if not _validate_env():
        sys.exit(1)

    print("  Initialising agent …")
    try:
        agent = OSAgentSystem()
    except Exception as exc:
        print(f"[ERROR] Failed to initialise the agent: {exc}")
        sys.exit(1)

    print("  Agent ready.\n")
    run_repl(agent)


if __name__ == "__main__":
    main()
