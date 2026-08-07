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

- **The Brain (API Layer):** Powered by Groq (Llama 3) or OpenAI for ultra-fast reasoning and function-calling.
- **The Body (Orchestration Layer):** Python + LangChain. This layer handles the Agent loop, deciding which tools to call based on the LLM's reasoning.
- **The Hands (Tool Layer):** Custom Python scripts and system calls that safely interact with the local filesystem and OS.

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

*(Code implementation pending. Setup instructions will be added once the core engine is built.)*

## ⚠️ Security Notice

This agent interacts directly with the local operating system. All destructive tools (like deleting files or running shell commands) will require explicit User Confirmation (Human-in-the-Loop) before execution.
