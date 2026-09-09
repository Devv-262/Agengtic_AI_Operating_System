# Agentic AI Operating System

An intelligent, API-driven Agentic Operating System that bridges the gap between natural language and local OS-level operations. 

This project serves as a "Personal AI OS Agent," capable of executing complex workflows, organizing files, and securely controlling the local system using Large Language Models (LLMs) equipped with function-calling capabilities.

## 🚀 Key Features

1. **Smart File Organizer** ✅
   - `organize_directory` proposes a logical category-folder plan (LLM analysis of filename + content), moves everything under a single confirmation, and supports `undo_last_organize`.
2. **Semantic Desktop Search** ✅
   - `index_directory` + `semantic_search` find files by meaning, not just exact keyword (e.g. "the PDF about machine learning I downloaded last week"), backed by a local ChromaDB index with on-device embeddings.
3. **CLI Auto-Pilot** ✅
   - `generate_shell_command` translates natural language into PowerShell/bash, `execute_command` runs it — behind a destructive-pattern blocklist and a confirmation prompt.
4. **Local Document Summarizer** ✅
   - `read_document` ingests local PDFs, DOCX, and TXT files; `think_deeply` answers questions over the extracted text.
5. **System Automation & Control** ✅
   - `set_volume` / `set_dark_mode` adjust system settings. `resize_images`, `create_archive`, and `extract_archive` chain naturally through the ReAct loop for batch tasks (e.g. "resize these images and zip them").

## 🧠 Architecture Overview

Since this system avoids heavy local hardware dependencies (no local GPU required), the architecture is split into three layers:

- **The Brain (API Layer):** NVIDIA NIM as the primary provider, with automatic fallback to OpenRouter if NIM is unavailable. Three task-specific models are routed by job:
  | Task | Model | Why |
  |---|---|---|
  | Agent loop / tool-calling | `nvidia/nemotron-3-super-120b-a12b` | NVIDIA-tuned for agentic reasoning, planning, and tool calling — the loop driver needs reliable structured function calls |
  | Deep reasoning / summarization / semantic ranking | `nvidia/nemotron-3-ultra-550b-a55b` | Largest Nemotron 3 tier, strong at nuanced instruction-following and long-document Q&A; called as a tool (`think_deeply`), not the loop driver, so its higher latency is acceptable |
  | Shell/CLI command generation | `qwen/qwen2.5-coder-32b-instruct` | Best free-tier model for English → PowerShell/bash |

  The OpenRouter fallback for all three defaults to `openrouter/free` — OpenRouter's own router alias that auto-picks an available free tool-calling-capable model — rather than a pinned free model, since OpenRouter's free-tier roster is volatile (whole free model families have gone dark before) and a pinned fallback can itself silently die, defeating the point of having one.

  All models are overridable via `.env` (see `.env.example`). If NIM starts returning a `410`/"model not found" error, see `plan.md`'s "Operational note" section for how to find and swap in a current model ID.
- **The Body (Orchestration Layer):** Python + LangGraph `create_react_agent`. This layer handles the Agent loop, deciding which tools to call based on the LLM's reasoning.
- **The Hands (Tool Layer):** Custom Python scripts and system calls that safely interact with the local filesystem and OS. Destructive tools (`delete_file`, `move_file`, `execute_command`) always prompt for human confirmation before acting.

## 📂 Project Structure

```text
Agentic-AI-OS/
│
├── src/
│   ├── main.py                 # Main entry point for the OS Agent interface
│   ├── agent.py                # Core LangChain Agent logic and prompt definitions
│   └── config.py               # API keys and environment configurations
│
├── tools/
│   ├── __init__.py
│   ├── file_manager.py         # Tools for reading, moving, and deleting files
│   ├── file_organizer.py       # Smart File Organizer + undo
│   ├── semantic_search.py      # Semantic Desktop Search (index + search)
│   ├── task_automation.py      # Image resize, zip/unzip archives
│   ├── system_controller.py    # Tools for modifying OS settings and volumes
│   ├── document_reader.py      # Tools for parsing PDFs and local text
│   ├── shell_executor.py       # Safe subprocess execution wrapper
│   ├── reasoning.py            # think_deeply / generate_shell_command specialist-model tools
│   ├── _safety.py              # Path sandbox + shell command blocklist
│   └── _confirm.py             # Pluggable human-in-the-loop confirmation gate
│
├── memory/
│   └── vector_store/           # Local ChromaDB index for semantic file search (gitignored)
│
├── ui/
│   ├── cli.py                  # Rich-based Terminal interface implementation
│   └── floating_bar.py         # PyQt6 Spotlight-style floating desktop bar
│
├── docs/
│   └── ui-ideas/                # Saved UI concepts for future phases
│
├── tests/
│   ├── test_tools.py            # Unit tests for OS-level tool safety
│   ├── test_file_organizer.py   # Unit tests for the Smart File Organizer
│   ├── test_semantic_search.py  # Unit tests for Semantic Desktop Search
│   ├── test_reasoning.py        # Unit tests for OS-aware shell command generation
│   └── test_task_automation.py  # Unit tests for image resize / zip / unzip
│
├── .github/workflows/
│   └── tests.yml                 # CI: runs pytest on push/PR to main
│
├── plan.md                      # Implementation roadmap / what's left
├── pyproject.toml                # Packaging + `agentic-os` console-script entry point
├── requirements.txt              # Python dependencies (LangChain, Rich, ChromaDB, etc.)
└── .env.example                  # Template for environment variables (API keys)
```

## 🛠️ Setup Instructions

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add at least one of `NIM_API_KEY` (get one free at [build.nvidia.com](https://build.nvidia.com)) or `OPENROUTER_API_KEY` (free at [openrouter.ai/keys](https://openrouter.ai/keys)). Having both gives you automatic failover.
3. Run the agent:
   - Terminal CLI: `python -m src.main`
   - Floating desktop bar: `python -m src.main --gui` — runs in the system tray, press **Ctrl+Space** to open/close it. Right-click the tray icon to quit.
   - Alternatively, `pip install -e .` once to get an `agentic-os` command on your PATH (equivalent to `python -m src.main`; pass `--gui` the same way).
4. Logs are written to `logs/agentic_ai_os.log` (rotating, gitignored) if you need to debug a failure after the fact.

## ⚠️ Security Notice

This agent interacts directly with the local operating system.

- All destructive tools (deleting/moving/organizing files, running shell commands) require explicit User Confirmation (Human-in-the-Loop) before execution.
- File tools are sandboxed to the user's home directory tree by default (`ALLOWED_ROOTS` / `ENABLE_PATH_SANDBOX` in `.env`).
- `execute_command` hard-refuses known-destructive shell patterns (`rm -rf`, `format`, fork bombs, raw device writes) — this is a stronger guarantee than confirmation, since it can't be approved by mistake.
