"""
tools/_confirm.py
------------------
Role: Human-in-the-loop confirmation gate for destructive tools (file
delete/move, shell command execution). Per the project's security notice,
these tools must not execute silently.
"""
from src.config import REQUIRE_CONFIRMATION


def confirm_action(description: str) -> bool:
    """
    Prompts the user on stdin to approve a destructive action.
    Returns True if approved, False otherwise. Always True when
    REQUIRE_CONFIRMATION is disabled via config/env.
    """
    if not REQUIRE_CONFIRMATION:
        return True

    answer = input(f"\n  [CONFIRM] {description} — proceed? [y/N] › ").strip().lower()
    return answer in ("y", "yes")
