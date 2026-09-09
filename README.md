# Agentic AI Operating System

An intelligent, API-driven Agentic Operating System that bridges the gap between natural language and local OS-level operations. 

This project serves as a "Personal AI OS Agent," capable of executing complex workflows, organizing files, and securely controlling the local system using Large Language Models (LLMs) equipped with function-calling capabilities.

## 🚀 Key Features (Planned)

1. **Smart File Organizer** 
   - Uses context and LLM analysis to sort files (e.g., Downloads, Documents) logically, moving beyond simple file-extension matching.
2. **Semantic Desktop Search** 
   - Employs a local vector database to find files based on their meaning or content (e.g., "Find the invoice from last month about server costs").
3. **CLI Auto-Pilot** 
   - Translates natural language requests into complex bash/PowerShell commands and runs them in a secure sandbox.
4. **Local Document Summarizer** 
   - Ingests local PDFs, DOCX, and TXT files for instantaneous summarization and Q&A.
5. **System Automation & Control** 
   - Adjusts system settings (volume, dark mode) and chains scripts together to automate repetitive desktop workflows.

## 🧠 Architecture Overview

Since this system avoids heavy local hardware dependencies (no local GPU required), the architecture is split into three layers:

- **The Brain (API Layer):** NVIDIA NIM as the primary provider, with automatic fallback to free OpenRouter models if NIM is unavailable. Three task-specific models are routed by job:
  | Task | Model | Why |
  |---|---|---|
  | Agent loop / tool-calling | `meta/llama-3.3-70b-instruct` | Most reliable structured tool-calling among the free options |
  | Deep reasoning / summarization / semantic ranking | `nvidia/llama-3.1-nemotron-70b-instruct` | Strong at nuanced instruction-following and long-document Q&A; called as a tool (`think_deeply`), not the loop driver |
  | Shell/CLI command generation | `qwen/qwen2.5-coder-32b-instruct` | Best free-tier model for English → PowerShell/bash |

  All models are overridable via `.env` (see `.env.example`).
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
│   ├── file_manager.py         # Tools for reading, moving, and organizing files
│   ├── system_controller.py    # Tools for modifying OS settings and volumes
│   ├── document_reader.py      # Tools for parsing PDFs and local text
│   └── shell_executor.py       # Safe subprocess execution wrapper
│
├── memory/
│   └── vector_store/           # Local ChromaDB/FAISS for semantic file search
│
├── ui/
│   └── cli.py                  # Rich-based Terminal interface implementation
│
├── tests/
│   └── test_tools.py           # Unit tests for OS-level tool safety
│
├── requirements.txt            # Python dependencies (LangChain, Rich, etc.)
└── .env.example                # Template for environment variables (API keys)
```

## 🛠️ Setup Instructions

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add at least one of `NIM_API_KEY` (get one free at [build.nvidia.com](https://build.nvidia.com)) or `OPENROUTER_API_KEY` (free at [openrouter.ai/keys](https://openrouter.ai/keys)). Having both gives you automatic failover.
3. Run the agent: `python -m src.main`

## ⚠️ Security Notice

This agent interacts directly with the local operating system. All destructive tools (like deleting files or running shell commands) will require explicit User Confirmation (Human-in-the-Loop) before execution.
