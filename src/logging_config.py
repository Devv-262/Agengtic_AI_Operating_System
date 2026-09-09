"""
logging_config.py
------------------
Role: Structured logging so agent errors are diagnosable after the fact
instead of only visible in a terminal that's already scrolled past.
Call setup_logging() once at startup (both the CLI and GUI entry points do).
"""
import logging
import os
from logging.handlers import RotatingFileHandler

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(_PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "agentic_ai_os.log")


def setup_logging(level: int = logging.INFO) -> None:
    """Configures the root logger with a rotating file handler (everything
    at `level`+) and a console handler (warnings+ only, so normal operation
    stays quiet on stdout — the UI layers handle user-facing output)."""
    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    os.makedirs(LOG_DIR, exist_ok=True)
    root.setLevel(level)

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(console_handler)
