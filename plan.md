# Agentic-AI-OS — Implementation Plan

Status snapshot and what's left, grouped by priority. Check off as completed.

## Done

- [x] Multi-provider LLM routing: NVIDIA NIM primary, OpenRouter free-tier fallback (`src/llm_provider.py`)
- [x] Task-specific models: agent (tool-calling), reasoning, coder (`src/config.py`). Updated 2026-09-10 after NVIDIA retired `meta/llama-3.3-70b-instruct` (confirmed via a live `410` end-of-life error) — agent now uses `nvidia/nemotron-3-super-120b-a12b`, reasoning uses `nvidia/nemotron-3-ultra-550b-a55b` (the prior `nvidia/llama-3.1-nemotron-70b-instruct` was also no longer in NVIDIA's current catalog); all three OpenRouter fallbacks switched from pinned free model IDs to the `openrouter/free` router alias for resilience against OpenRouter's free-tier churn. See the operational note below.
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

## Phase 1 — Safety hardening (do before wiring anything more powerful) ✅

- [x] **Path sandboxing for file tools.** `check_path_allowed()` in `tools/_safety.py`, wired into `list_directory`/`read_file`/`move_file`/`delete_file`/`read_document`. Defaults to the user's whole home directory (`ALLOWED_ROOTS` overridable via `.env`); toggle with `ENABLE_PATH_SANDBOX`.
- [x] **Shell command guardrails.** `check_command_blocked()` in `tools/_safety.py` hard-refuses known-destructive patterns (`rm -rf`, `format`, fork bombs, raw device writes, etc.) *before* confirmation is even asked — a rushed "y" can't approve these.
- [x] **Confirmation UX under Rich.** `ui/cli.py` now installs a distinct red-bordered `Panel` confirmation prompt via `set_confirm_handler`, visually separated from normal agent replies.
- [x] Rate-limit / retry handling — `max_retries=2` + `timeout=30s` on both the NIM and OpenRouter `ChatOpenAI` clients in `src/llm_provider.py`, absorbing transient 429s/5xxs before falling through to the fallback provider.

## Phase 2 — Smart File Organizer ✅

- [x] `organize_directory` tool (`tools/file_organizer.py`): lists the files directly in a directory, samples content for text-like extensions, asks the reasoning model for a filename → category-folder JSON plan, then moves everything under ONE batch confirmation showing the full plan.
- [x] Undo support — `undo_last_organize` reverses the most recent run using a per-directory JSON log (`.agentic_ai_os_organize_log.json`).

## Phase 3 — Semantic Desktop Search ✅

- [x] Vector store: ChromaDB `PersistentClient` at `memory/vector_store/` (gitignored — machine-local), using its bundled ONNX MiniLM embedding function so indexing/search need no LLM API call or key.
- [x] `index_directory` tool (`tools/semantic_search.py`): walks a directory (recursive by default), extracts text via the now-shared `document_reader.extract_text()`, stores content + `{path, name, mtime}` metadata.
- [x] `semantic_search` tool: similarity-search the collection, returns top-N `path (relevance score) + snippet`, with an optional `directory_filter`.
- [x] Incremental re-index — skips files whose `mtime` metadata hasn't changed since the last index.
- [ ] NIM/OpenRouter-backed embeddings as an alternative to the local ONNX model weren't pursued — the local model is free, offline-capable, and avoids a third failure mode (embedding API down) on top of the two LLM providers. Revisit only if embedding quality turns out to matter more than availability.

## Phase 4 — CLI Auto-Pilot hardening ✅

- [x] Decided against hard-enforcing `generate_shell_command` → `execute_command` — a same-turn tracking mechanism would be fragile (e.g. what counts as "the same turn" across a multi-step plan) and would block legitimate direct commands the agent already knows are safe. Kept as a system-prompt guideline instead (see `src/agent.py`).
- [x] Cross-platform command translation — `generate_shell_command`'s `target_shell` now defaults to `None` and auto-detects via `platform.system()` (PowerShell on Windows, bash on macOS/Linux) instead of being hardcoded to `"powershell"`.

## Phase 5 — Task Automation (chaining) ✅

- [x] Image tool: `resize_images` (`tools/task_automation.py`, Pillow) — resizes every image in a directory to a max dimension (aspect-ratio preserved), writing into a `resized/` subfolder rather than overwriting originals.
- [x] Archive tools: `create_archive` (zip a list of files/folders) and `extract_archive` (unzip, with a zip-slip path-traversal guard).
- [x] Confirmed the "chaining" itself needs no new orchestration — the ReAct loop already calls `resize_images` then `create_archive` in sequence for a combined request.

## Phase 6 — Polish / ops ✅

- [x] Test coverage for `system_controller.py` (`tests/test_system_controller.py`), `document_reader.py` (`tests/test_document_reader.py`), `reasoning.py` (`tests/test_reasoning.py`).
- [x] Logging — `src/logging_config.py` sets up a rotating file handler (`logs/agentic_ai_os.log`, INFO+) plus a console handler (WARNING+), called from `main.py` and both UI entry points. `OSAgentSystem.process_command` now logs the full traceback on failure via `logger.exception(...)`.
- [x] `pyproject.toml` + console-script entry point — `agentic-os` command via `pip install -e .` (added `src/__init__.py` and `ui/__init__.py` so `src`/`tools`/`ui` are regular packages setuptools can discover). `requirements.txt` remains for the plain `pip install -r` workflow.
- [x] CI: `.github/workflows/tests.yml` runs `pytest` on push/PR to `main` (ubuntu-latest; Windows-only deps like `pycaw` are skipped automatically via their `sys_platform` markers, and no test imports `ui.floating_bar` so the headless runner never needs a display).
- [x] Conversation persistence (in-process) — `MemorySaver` checkpointer wired into `create_react_agent` in `src/agent.py`, so the agent now actually remembers earlier turns within a running session (previously each `process_command` call was stateless despite the `thread_id` config existing — no checkpointer meant nothing was ever stored against it). Does **not** persist across process restarts; a SQLite/file-backed checkpointer would be the next step if that's wanted.

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

## Operational note — NIM/OpenRouter model IDs can go stale

Both providers' model catalogs change over time (NVIDIA has retired NIM
models with a hard 410 end-of-life; OpenRouter's free tier has gone dark
for entire model families before, e.g. Llama and Qwen free tiers in early
August 2026). If the agent starts failing with a 410 or a persistent
"model not found"-style error:

- Check `docs.api.nvidia.com/nim/reference/llm-apis` for the current NIM
  model list and swap the relevant `MODEL_*_NIM` env var(s) — no code
  change needed, these are plain env-overridable string defaults in
  `src/config.py`.
- The OpenRouter fallback defaults to `openrouter/free` (OpenRouter's
  router alias, auto-selects an available free tool-calling-capable
  model) specifically to avoid this class of failure on the fallback
  path; only override `MODEL_*_OPENROUTER` to a pinned model if you need
  deterministic behavior for a specific reason.

## Explicitly out of scope for now

- macOS/Linux dark-mode-equivalent parity beyond what's already stubbed for shell-based platforms is low priority given primary dev target is Windows.
