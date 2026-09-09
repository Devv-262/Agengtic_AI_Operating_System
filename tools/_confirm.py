"""
tools/_confirm.py
------------------
Role: Human-in-the-loop confirmation gate for destructive tools (file
delete/move, shell command execution). Per the project's security notice,
these tools must not execute silently.

Defaults to a stdin prompt. A UI front end that can't use stdin (e.g. the
PyQt floating bar, which processes commands on a worker thread) can install
its own handler via set_confirm_handler().
"""
from src.config import REQUIRE_CONFIRMATION

_handler = None


def set_confirm_handler(handler) -> None:
    """Overrides how confirm_action() asks the user. handler(description: str) -> bool."""
    global _handler
    _handler = handler


def _default_stdin_handler(description: str) -> bool:
    answer = input(f"\n  [CONFIRM] {description} — proceed? [y/N] › ").strip().lower()
    return answer in ("y", "yes")


def confirm_action(description: str) -> bool:
    """
    Asks the user to approve a destructive action, via the installed handler
    (stdin prompt by default). Returns True if approved, False otherwise.
    Always True when REQUIRE_CONFIRMATION is disabled via config/env.
    """
    if not REQUIRE_CONFIRMATION:
        return True

    handler = _handler or _default_stdin_handler
    return handler(description)
