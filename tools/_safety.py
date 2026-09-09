"""
tools/_safety.py
-----------------
Role: Shared guardrails for tools that touch the filesystem or a shell.

- check_path_allowed(): refuses file operations outside ALLOWED_ROOTS.
- check_command_blocked(): refuses shell commands matching known-destructive
  patterns outright, before confirmation is even asked (confirmation is not
  a strong enough gate for these — a rushed "y" shouldn't be able to approve
  a filesystem wipe).
"""
import re
from pathlib import Path
from typing import Optional

from src.config import ALLOWED_ROOTS, ENABLE_PATH_SANDBOX

_ALLOWED_ROOT_PATHS = [Path(p).expanduser().resolve() for p in ALLOWED_ROOTS]


def check_path_allowed(path: Path) -> Optional[str]:
    """
    Returns an error message if `path` falls outside the configured sandbox
    roots, or None if it's allowed.
    """
    if not ENABLE_PATH_SANDBOX:
        return None

    for root in _ALLOWED_ROOT_PATHS:
        if path == root or root in path.parents:
            return None

    allowed = ", ".join(str(r) for r in _ALLOWED_ROOT_PATHS)
    return (
        f"Error: '{path}' is outside the allowed sandbox. "
        f"Allowed roots: {allowed}. Set ALLOWED_ROOTS in .env to change this."
    )


# Destructive shell patterns that are refused unconditionally, regardless of
# confirmation. Intentionally conservative — false positives here just mean
# an unusual-but-safe command needs rephrasing; false negatives mean data
# loss, so we err toward blocking.
_BLOCKED_PATTERNS = [
    r"\brm\s+.*-[a-z]*r[a-z]*f",           # rm -rf ...
    r"\brm\s+.*-[a-z]*f[a-z]*r",           # rm -fr ...
    r"\bdel\s+/[sf]\b.*/[sf]\b",           # del /s /q, del /f /s ...
    r"\brd\s+/s\b",                        # rd /s
    r"\bformat\s+[a-z]:",                  # format c:
    r"\bmkfs(\.\w+)?\b",                   # mkfs / mkfs.ext4 ...
    r"\bdd\s+.*of=/dev/",                  # dd if=... of=/dev/sdX
    r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:",    # classic fork bomb
    r"\bshutdown\b.*-[fF]\b",              # forced shutdown
    r">\s*/dev/sd[a-z]\b",                 # raw device overwrite
]
_BLOCKED_RE = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]


def check_command_blocked(command: str) -> Optional[str]:
    """
    Returns an error message if `command` matches a known-destructive
    pattern (filesystem wipes, fork bombs, raw device writes), or None if
    it's not on the blocklist.
    """
    for pattern in _BLOCKED_RE:
        if pattern.search(command):
            return (
                f"Error: command refused — it matches a blocked destructive "
                f"pattern ({pattern.pattern}). This is a hard block, not a "
                f"confirmation prompt; rephrase the request if this was a "
                f"false positive."
            )
    return None
