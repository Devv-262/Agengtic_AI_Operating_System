"""
tools/file_organizer.py
------------------------
Role: Smart File Organizer — reads the files directly inside a directory
(names, extensions, and a short content sample where readable), asks the
reasoning model to propose a logical category per file, then moves them
into category subfolders under a single batch confirmation (not one prompt
per file). Each run is logged so it can be undone.
"""
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

from src.llm_provider import get_llm
from tools._confirm import confirm_action
from tools._safety import check_path_allowed

_LOG_FILENAME = ".agentic_ai_os_organize_log.json"
_TEXT_SAMPLE_EXTENSIONS = {".txt", ".md", ".csv", ".log", ".json", ".py", ".js", ".ts"}
_SAMPLE_CHARS = 300

_ORGANIZE_SYSTEM_PROMPT = SystemMessage(content="""\
You organize files into logical category folders based on filename, \
extension, and (when given) a short content sample. Respond with ONLY a \
JSON object mapping each input filename to a single short category folder \
name (e.g. "Documents", "Images", "Invoices", "Screenshots", "Code", \
"Archives", "Videos", "Spreadsheets", "Misc"). Prefer specific, useful \
categories over generic ones when the content justifies it (e.g. an \
invoice PDF -> "Invoices", not just "Documents"). No prose, no markdown \
fences, just the JSON object.""")


def _describe_file(path: Path) -> str:
    size_kb = path.stat().st_size / 1024
    description = f"name={path.name}, ext={path.suffix or '(none)'}, size={size_kb:.1f}KB"
    if path.suffix.lower() in _TEXT_SAMPLE_EXTENSIONS:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                sample = f.read(_SAMPLE_CHARS).replace("\n", " ")
            description += f", sample=\"{sample}\""
        except Exception:
            pass
    return description


def _load_log(directory: Path) -> list:
    log_path = directory / _LOG_FILENAME
    if not log_path.exists():
        return []
    try:
        return json.loads(log_path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_log(directory: Path, runs: list) -> None:
    log_path = directory / _LOG_FILENAME
    log_path.write_text(json.dumps(runs, indent=2), encoding="utf-8")


@tool
def organize_directory(directory_path: str) -> str:
    """
    Organizes the files directly inside a directory into logical category
    subfolders (e.g. Documents, Images, Invoices), proposed by a reasoning
    model based on filename and content. Shows the full move plan and asks
    for ONE confirmation before moving anything. Does not recurse into
    subdirectories. Use undo_last_organize to reverse the most recent run.
    """
    try:
        directory = Path(directory_path).expanduser().resolve()
        sandbox_error = check_path_allowed(directory)
        if sandbox_error:
            return sandbox_error
        if not directory.is_dir():
            return f"Error: '{directory}' is not a directory."

        files = [p for p in directory.iterdir() if p.is_file() and p.name != _LOG_FILENAME]
        if not files:
            return "Nothing to organize — no files found directly in this directory."

        descriptions = "\n".join(_describe_file(p) for p in files)
        llm = get_llm("reasoning", temperature=0.1)
        response = llm.invoke([
            _ORGANIZE_SYSTEM_PROMPT,
            HumanMessage(content=f"Files to categorize:\n{descriptions}"),
        ])

        raw = response.content.strip().strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
        try:
            categories = json.loads(raw)
        except json.JSONDecodeError:
            return f"Error: the reasoning model returned invalid JSON, aborting. Raw response: {raw[:500]}"

        plan = []
        for path in files:
            category = categories.get(path.name)
            if not category or not isinstance(category, str):
                continue
            dest_dir = directory / category
            dest_path = dest_dir / path.name
            dest_error = check_path_allowed(dest_path)
            if dest_error:
                continue
            plan.append((path, dest_path))

        if not plan:
            return "No valid move plan could be built from the model's response."

        plan_text = "\n".join(f"  {src.name} -> {dst.relative_to(directory)}" for src, dst in plan)
        if not confirm_action(f"Organize {len(plan)} file(s) in '{directory}':\n{plan_text}"):
            return "Cancelled: user did not approve the organize plan."

        moved = []
        errors = []
        for src, dst in plan:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                moved.append((str(src), str(dst)))
            except Exception as e:
                errors.append(f"{src.name}: {e}")

        if moved:
            runs = _load_log(directory)
            runs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "moves": [{"src": s, "dst": d} for s, d in moved],
            })
            _save_log(directory, runs)

        summary = f"Organized {len(moved)} file(s) in '{directory}'."
        if errors:
            summary += f"\n{len(errors)} failed:\n" + "\n".join(errors)
        return summary

    except Exception as e:
        return f"Error organizing directory: {str(e)}"


@tool
def undo_last_organize(directory_path: str) -> str:
    """Reverses the most recent organize_directory run in the given directory, moving files back to where they were."""
    try:
        directory = Path(directory_path).expanduser().resolve()
        sandbox_error = check_path_allowed(directory)
        if sandbox_error:
            return sandbox_error

        runs = _load_log(directory)
        if not runs:
            return f"No organize run recorded for '{directory}' — nothing to undo."

        last_run = runs[-1]
        moves = last_run["moves"]
        plan_text = "\n".join(f"  {m['dst']} -> {m['src']}" for m in moves)
        if not confirm_action(f"Undo the last organize run ({len(moves)} file(s)) in '{directory}':\n{plan_text}"):
            return "Cancelled: user did not approve the undo."

        restored = []
        errors = []
        for m in moves:
            src, dst = Path(m["src"]), Path(m["dst"])
            try:
                if not dst.exists():
                    errors.append(f"{dst.name}: no longer at expected location, skipped")
                    continue
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(src))
                restored.append(m)
            except Exception as e:
                errors.append(f"{dst.name}: {e}")

        runs.pop()
        _save_log(directory, runs)

        summary = f"Restored {len(restored)} file(s)."
        if errors:
            summary += f"\n{len(errors)} failed:\n" + "\n".join(errors)
        return summary

    except Exception as e:
        return f"Error undoing organize: {str(e)}"


file_organizer_tools = [organize_directory, undo_last_organize]
