# Agentic-AI-OS — Implementation Plan

Status snapshot and what's left, grouped by priority. Check off as completed.

## Done

- [x] Multi-provider LLM routing: NVIDIA NIM primary, OpenRouter free-tier fallback (`src/llm_provider.py`)
- [x] Task-specific models: agent (tool-calling), reasoning, coder (`src/config.py`)
- [x] LangGraph ReAct agent wired to the real tool package (`src/agent.py`)
- [x] File tools: list/read/move/delete (`tools/file_manager.py`)
- [x] Shell execution tool (`tools/shell_executor.py`)
- [x] System controller: volume (Windows/macOS/Linux), dark mode (Windows/macOS) (`tools/system_controller.py`)
- [x] Document reader: TXT/PDF/DOCX (`tools/document_reader.py`)
- [x] Reasoning tools: `think_deeply`, `generate_shell_command` (`tools/reasoning.py`)
- [x] Human-in-the-loop confirmation gate on destructive tools (`tools/_confirm.py`)
- [x] Rich-based interactive CLI (`ui/cli.py`)
- [x] Unit tests for the confirmation gate (`tests/test_tools.py`)
- [x] PyQt6 floating desktop bar (Spotlight-style, global hotkey, system tray) (`ui/floating_bar.py`), with the confirmation gate made pluggable so it can use a Qt dialog instead of stdin

## Phase 1 — Safety hardening (do before wiring anything more powerful)

- [ ] **Path sandboxing for file tools.** `delete_file`/`move_file`/`read_file` currently resolve and act on *any* path the model names, including system directories. Add an allowlist of roots (e.g. user's home, Desktop, Downloads, Documents) that tools refuse to operate outside of without an explicit override flag.
- [ ] **Shell command guardrails.** `execute_command` has no blocklist — confirmation is the only gate, and a rushed "y" approves anything. Add a pattern blocklist for obviously destructive commands (`rm -rf /`, `format`, `del /s /q C:\`, fork bombs, etc.) that refuse even with confirmation, and show the exact command text prominently before the prompt (already does, but consider a diff-style highlight for `move_file` destinations).
- [ ] **Confirmation UX under Rich.** Currently `input()` runs mid-agent-invoke inside the CLI loop with no live spinner conflict, but there's no visual distinction between "agent talking" and "agent asking permission" — worth a distinct prompt style.
- [ ] Rate-limit / retry handling for both NIM and OpenRouter (free tiers throttle); currently a failure just falls through to the OpenRouter fallback once, then raises.

## Phase 2 — Smart File Organizer

- [ ] `organize_directory` tool/workflow: list a directory, read a sample of each file (name + first N chars / metadata), ask the reasoning model to propose a category, then batch-move with a single confirmation showing the full move plan (not one confirmation per file).
- [ ] Undo support — log the last organize run's moves so "undo that" is possible.

## Phase 3 — Semantic Desktop Search

- [ ] Stand up the vector store the README already promises (`memory/vector_store/`) — pick FAISS or ChromaDB (local, no server).
- [ ] Indexing tool: walk a directory, extract text (reuse `document_reader`), embed, store with file path + mtime metadata. Needs an embedding model — check if NIM or OpenRouter expose a free embeddings endpoint, else use a small local sentence-transformers model.
- [ ] `semantic_search` tool: embed the query, similarity-search the store, return top-N file paths + snippets for the agent to reason over.
- [ ] Incremental re-index (skip unchanged files by mtime) so this doesn't become a full re-scan every time.

## Phase 4 — CLI Auto-Pilot hardening

- [ ] Currently `generate_shell_command` → `execute_command` is a two-step chain but nothing stops the agent from writing a raw command itself and skipping the coder model. Consider making `execute_command` reject commands that weren't produced by `generate_shell_command` in the same turn, or just accept this is a soft guideline.
- [ ] Cross-platform command translation check — `generate_shell_command` takes a `target_shell` param but nothing auto-detects the host OS and defaults it; wire it to `platform.system()`.

## Phase 5 — Task Automation (chaining)

- [ ] Image tools: resize/convert (Pillow), so "resize all images in this folder to 1080p" works.
- [ ] Archive tool: zip/unzip a set of paths.
- [ ] These are individually simple tools — the "chaining" itself is just the ReAct loop calling them in sequence, so no new orchestration layer needed, just the missing tools.

## Phase 6 — Polish / ops

- [ ] Test coverage for `system_controller.py`, `document_reader.py`, `reasoning.py` (only file_manager/shell_executor are tested today).
- [ ] Logging (structured, to a file) instead of print-only, so failed tool calls are diagnosable after the fact.
- [ ] `pyproject.toml` + console-script entry point (`agentic-os` command) instead of `python -m src.main`.
- [ ] CI: GitHub Actions running `pytest` on push.
- [ ] Conversation persistence: `OSAgentSystem` uses a static `thread_id` but no LangGraph checkpointer is configured, so history doesn't survive a restart. Add `MemorySaver` (or a SQLite checkpointer) if multi-session memory matters.

## Follow-ups on the floating bar

- [ ] `keyboard` global-hotkey hook can require running as admin on some Windows setups — verify and document, or switch to a lower-privilege alternative if it's flaky.
- [ ] No visual "confirmation pending" state in the bar itself — a destructive-action confirm currently pops a separate `QMessageBox`; consider inlining it into the bar UI instead.
- [ ] No history/multi-turn view in the floating bar (single input → single output, unlike the CLI's scrolling transcript).

## Future UI idea (not scheduled yet)

- [ ] Full dashboard UI, separate from the floating bar — see
  `docs/ui-ideas/dashboard-concept.md` for a saved reference layout (chat
  panel with assistant persona, quick-action chips, calendar/progress/
  activity-feed widgets, proactive "AI suggestion" card). Revisit once more
  core features (Phases 1-5) are built — proactive suggestions in
  particular depend on the Smart File Organizer and Semantic Search
  actually existing first.

## Explicitly out of scope for now

- macOS/Linux dark-mode-equivalent parity beyond what's already stubbed for shell-based platforms is low priority given primary dev target is Windows.
