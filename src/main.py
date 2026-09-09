"""
main.py
-------
Role: Main entry point for the Agentic-AI-OS.
      Validates configuration and hands control to the Rich-based interactive
      CLI (ui/cli.py), which owns the REPL loop.
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
from src.config import NIM_API_KEY, OPENROUTER_API_KEY


def _validate_env() -> bool:
    """
    Sanity-check that at least one LLM provider is configured.
    Returns True if everything is fine, False otherwise.
    """
    if not NIM_API_KEY and not OPENROUTER_API_KEY:
        print("[ERROR] Neither NIM_API_KEY nor OPENROUTER_API_KEY is set.")
        print("        Copy .env.example -> .env and add at least one key, then retry.")
        return False
    if not NIM_API_KEY:
        print("[WARN] NIM_API_KEY is not set — will run entirely on the OpenRouter fallback.")
    if not OPENROUTER_API_KEY:
        print("[WARN] OPENROUTER_API_KEY is not set — no fallback if NIM is unavailable.")
    return True


def main() -> None:
    """Bootstrap the OS Agent and launch either the terminal REPL or the
    PyQt floating bar, depending on the --gui flag."""
    if not _validate_env():
        sys.exit(1)

    if "--gui" in sys.argv:
        from ui.floating_bar import main as run_gui
        run_gui()
    else:
        from ui.cli import run
        run()


if __name__ == "__main__":
    main()
