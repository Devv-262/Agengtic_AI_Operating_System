# Agentic-AI-OS — Technical Guide

A teaching-oriented walkthrough of how this codebase actually works: the
stack, the architecture, what each file does, the important functions to
read, and the patterns worth learning from this project specifically. Read
this alongside the actual files — file paths and function names below are
exact, not paraphrased, so you can jump straight to the source.

---

## 1. The stack, and why each piece was chosen

| Layer | Tech | Why |
|---|---|---|
| LLM access | `langchain-openai`'s `ChatOpenAI` | Both NVIDIA NIM and OpenRouter expose an OpenAI-compatible `/v1/chat/completions` API, so one client class works for both — just point `base_url`/`api_key`/`model` at whichever provider |
| Agent loop | `langgraph` (`create_react_agent`) | Implements the ReAct (Reasoning + Acting) pattern: the LLM decides which tool to call, the tool runs, the result goes back to the LLM, repeat until it has a final answer. LangGraph is the orchestration layer underneath LangChain that actually runs this loop as a graph |
| Tool definitions | `langchain_core.tools`'s `@tool` decorator | Turns a plain Python function into something the LLM can be told about (name, docstring, parameter schema) and call |
| Terminal UI | `rich` | Styled console output (panels, colored prompts, markdown rendering) without hand-rolling ANSI codes |
| Desktop UI | `PyQt6` | Native floating window + system tray icon + global hotkey integration |
| Vector search | `chromadb` | Local, no-server vector database; ships a bundled ONNX embedding model so semantic search works without any LLM API call |
| Document parsing | `pypdf`, `python-docx` | Text extraction from PDF/DOCX |
| Image tools | `Pillow` | Resizing, and generating `assets/icon.png`/`icon.ico` |

**The core mental model:** an LLM by itself can only produce text. To make
it *do things* (read a file, run a command, resize an image), you give it a
list of Python functions it's allowed to call (\"tools\"), described well
enough (via docstrings and type hints) that it can decide when to call
each one and with what arguments. The LLM never runs code directly — it
outputs a structured \"call this function with these arguments\" message,
your code actually calls the function, and the result is fed back to the
LLM as more conversation. That whole loop — think, call a tool, observe
the result, think again — is what LangGraph's `create_react_agent` runs
for you.

---

## 2. Architecture, three layers (as the README also describes it)

```
User input (typed or, later, voice)
        │
        ▼
┌─────────────────────────────────────────────┐
│  UI layer            ui/cli.py               │
│                       ui/floating_bar.py      │
│  Turns user input into a call to             │
│  OSAgentSystem.process_command() /            │
│  .stream_command()                            │
└───────────────────────┬───────────────────────┘
                         ▼
┌─────────────────────────────────────────────┐
│  The Body            src/agent.py             │
│  OSAgentSystem wraps a LangGraph              │
│  create_react_agent — the ReAct loop that     │
│  decides which tool to call, when             │
└───────────────────────┬───────────────────────┘
                         ▼
┌─────────────────────────────────────────────┐
│  The Brain            src/llm_provider.py     │
│  get_llm(task) returns a NIM-backed model     │
│  with an automatic OpenRouter fallback        │
└───────────────────────┬───────────────────────┘
                         ▼
┌─────────────────────────────────────────────┐
│  The Hands            tools/*.py              │
│  Actual Python functions: file I/O, shell,    │
│  system settings, search, document parsing    │
└─────────────────────────────────────────────┘
```

---

## 3. Request lifecycle — trace one command end to end

Say you type "what OS am I running?" into the floating bar. Here's exactly
what happens, in order:

1. **`ui/floating_bar.py`**, `FloatingBar._submit()` reads the text from
   the `QLineEdit`, disables the input, and creates an `AgentWorker`
   (a `QThread` subclass) with that text.
2. `AgentWorker.run()` calls `self.agent.stream_command(self.command)` —
   `self.agent` is the `OSAgentSystem` instance built once at startup in
   `main()`.
3. **`src/agent.py`**, `OSAgentSystem.stream_command()` calls
   `self.agent.stream(inputs, config=self.config, stream_mode="updates")`
   — `self.agent` here is the LangGraph-compiled graph (`os_agent`, built
   at module level from `create_react_agent(...)`). `stream_mode="updates"`
   means: yield a dict every time a graph node finishes, rather than
   waiting for the whole run to complete.
4. Internally, LangGraph's ReAct graph has (at minimum) two nodes: an
   `"agent"` node (calls the LLM) and a `"tools"` node (executes whatever
   tool calls the LLM asked for). The loop is: agent node runs → if the
   LLM's response includes tool calls, route to the tools node → tools
   node runs each tool and produces `ToolMessage`s → route back to the
   agent node with those results appended to the conversation → repeat
   until the LLM responds with no tool calls, meaning it's done.
5. For "what OS am I running?", the first agent-node pass produces an
   `AIMessage` whose `tool_calls` includes `get_system_info` (defined in
   `tools/system_controller.py`). `stream_command()`'s loop notices this
   and yields `{"type": "tool_call", "name": "get_system_info", "args": {}}`.
6. The tools node actually calls `get_system_info()`, which returns a
   plain string (`"Operating System: Windows 10"`). LangGraph wraps this
   in a `ToolMessage`. `stream_command()` yields
   `{"type": "tool_result", "name": "get_system_info", "result": "..."}`.
7. The agent node runs again with that result in context, and this time
   the LLM responds with plain text and no further tool calls — an
   `AIMessage` with `.content` set and no `tool_calls`.
   `stream_command()` yields `{"type": "final", "content": "..."}`.
8. Back in **`ui/floating_bar.py`**: each yielded dict was connected to
   `AgentWorker.log_event`, a `pyqtSignal(dict)`, which
   `FloatingBar._on_log_event()` receives and turns into a colored line in
   the "Activity" panel (`self.activity_log`). When the generator is
   exhausted, `AgentWorker.finished_with_result` fires with the final text,
   which `FloatingBar._on_result()` puts into the response box.

**Why a generator (`yield`) instead of returning a list?** The whole point
is the UI can show progress *as it happens*, not just at the end — a
generator lets the caller (`AgentWorker.run()`) process each event the
moment it's produced, rather than waiting for the entire multi-step tool
chain to finish before seeing anything.

---

## 4. File-by-file: what to actually read, and in what order

Read these in this order — each builds on the last.

### `src/config.py`
Pure configuration, no logic. Everything is `os.getenv("X", default)` —
notice the pattern: **every tunable default lives here as a plain string
or number**, never hardcoded elsewhere in the codebase. That's why fixing
the NIM model deprecation earlier only required editing this one file
(plus docs) — nothing downstream cared what the actual model string was.

### `src/llm_provider.py`
The whole file is ~50 lines and worth reading in full. The key line:
```python
return primary.with_fallbacks([fallback])
```
`.with_fallbacks()` is a LangChain `Runnable` method: it returns a new
runnable that tries `primary` first, and if that raises an exception,
tries `fallback` instead, transparently. This is *the* pattern to learn
here — it's how the whole "NIM primary, OpenRouter backup" resilience
works, and it required zero custom retry/error-handling code, because
LangChain already has this concept built in.

### `src/agent.py`
Two things to study closely:
1. **`SYSTEM_PROMPT`** — this is the entire "personality" and behavioral
   contract of the agent (which tool to prefer for what, when confirmation
   is expected, tone). If you ever want the agent to behave differently,
   this is almost always where the change belongs — before you reach for
   new code, check whether a prompt instruction would do it.
2. **`OSAgentSystem.process_command()` vs `.stream_command()`** — same
   underlying agent, two different consumption patterns. `process_command`
   (`self.agent.invoke(...)`) is simpler: give it input, block until done,
   get the final answer. `stream_command` (`self.agent.stream(...)`) gives
   you the same computation but exposes every intermediate step. The CLI
   (`ui/cli.py`) uses the simple one; the floating bar (`ui/floating_bar.py`)
   uses the streaming one because it has a UI element (the activity log)
   that benefits from progress visibility. **Lesson: pick your consumption
   API based on what the caller actually needs to show, not out of habit.**

### `tools/_confirm.py` and `tools/_safety.py`
The human-in-the-loop and sandboxing patterns. Notice `_confirm.py`'s
`set_confirm_handler()` — this is a simple but important pattern called
**dependency injection via a module-level swap point**: `confirm_action()`
doesn't know or care whether it's running under the CLI (which uses
`input()`) or the GUI (which needs a Qt dialog) — whichever UI starts up
calls `set_confirm_handler()` once with its own implementation, and every
tool that calls `confirm_action()` automatically gets the right behavior.
This is *much* simpler than threading a "confirmation strategy" object
through every single tool function's parameters.

`_safety.py`'s `check_path_allowed()` and `check_command_blocked()` are
called at the *top* of every tool that touches the filesystem or a shell —
notice they return `Optional[str]` (`None` = allowed, a string = the error
to show). This "return an error message or None" pattern shows up
throughout the tools — it's simpler than raising exceptions for expected,
recoverable failure cases (an LLM asking to touch a forbidden path isn't a
bug, it's a normal thing to gracefully decline).

### One representative tool file: `tools/file_manager.py`
Every tool follows the same shape:
```python
@tool
def some_tool(param: type) -> str:
    """Docstring — this is what the LLM reads to decide when to call this."""
    try:
        ...
        return "human-readable result string"
    except Exception as e:
        return f"Error: {str(e)}"
```
**Important: tools never raise exceptions back to the agent loop** — they
catch everything and return an error *string* instead. The LLM sees that
string like any other tool result and can react to it (e.g. try something
else, or tell the user it failed) — a raised Python exception would just
crash the request instead of giving the LLM a chance to recover or explain.

### `tools/reasoning.py`
This is where you can see the "task-specific model" idea in action —
`think_deeply` and `generate_shell_command` each call `get_llm()` with a
*different* `task` argument (`"reasoning"`, `"coder"`) than the main agent
loop (`"agent"`). Same provider/fallback machinery, different model
string, because different sub-tasks benefit from different models (see
`src/config.py`'s `MODELS` dict and the README's model table for the
reasoning behind each choice).

### `tools/file_organizer.py` and `tools/semantic_search.py`
Worth reading for the "batch confirmation, not per-item" pattern: both
build a *complete plan* first (which files go where; which files to
index), show the user the whole plan in one `confirm_action()` call, and
only then execute it. Compare this to `move_file`/`delete_file` in
`file_manager.py`, which confirm once per call because each call already
*is* one discrete action. The lesson: batch the confirmation at whatever
level matches the user's actual mental model of "one decision" — five
separate lower-level file moves that are all part of "organize this
folder" should be one confirmation, not five.

### `ui/floating_bar.py`
The most PyQt-specific file, and the one with the trickiest concurrency.
Three things worth understanding:

1. **Why work happens on a `QThread`.** Qt has one UI thread; anything
   that blocks it (like waiting on a network call to an LLM) freezes the
   whole window. `AgentWorker(QThread)` runs `stream_command()` on a
   separate thread, and communicates results back via `pyqtSignal`s
   (`log_event`, `finished_with_result`) — Qt automatically marshals
   signal emissions across threads safely, so `self.log_event.emit(event)`
   from the worker thread safely triggers `_on_log_event()` on the main
   thread.

2. **`ConfirmBridge` and `Qt.ConnectionType.BlockingQueuedConnection`.**
   This is the subtlest piece of code in the whole project. A tool
   (running on the worker thread) needs to show a confirmation dialog —
   but dialogs must be created on the main/UI thread. `ConfirmBridge.confirm()`
   emits `ask_signal`, and because the signal is connected with
   `BlockingQueuedConnection`, the *emitting* thread (the worker) blocks
   until the *connected slot* (`_ask()`, which shows the actual
   `QMessageBox`, running on the main thread) finishes. This is what lets
   `confirm_action()` — a plain synchronous function that tools call and
   expect a `bool` back — work correctly even though the actual dialog has
   to happen on a different thread. If you ever need "block one thread
   until the main/UI thread does something and gives you a result," this
   is the pattern.

3. **The global hotkey callback also crosses threads.** The `keyboard`
   library's `add_hotkey()` runs your callback on its own internal thread
   — `_register_hotkeys()` passes `bar.toggle_visibility.emit` directly as
   that callback. Since `toggle_visibility` is a `pyqtSignal`, emitting it
   from a non-Qt thread still safely queues the connected slot
   (`FloatingBar._toggle`) to run on the main thread. No `BlockingQueuedConnection`
   needed here (unlike the confirm case) because nothing needs to wait for
   a return value — it's fire-and-forget.

### `ui/cli.py`
Much simpler than the GUI — no threading needed because a terminal REPL is
naturally single-threaded and blocking is fine (the user is just waiting
for a response either way). Notice it *does* still use the pluggable
confirm-handler pattern (`_cli_confirm_handler`, installed via
`set_confirm_handler`), just with a plain `console.input()` instead of a
Qt dialog — same tool code, different presentation.

---

## 5. Key concepts glossary (LangChain/LangGraph terms used in this codebase)

- **Tool** — a Python function decorated with `@tool` (from
  `langchain_core.tools`), exposing its name/docstring/typed parameters to
  the LLM as something it can choose to call.
- **ReAct agent** — the reasoning pattern this whole project runs on:
  Reason (LLM decides what to do) → Act (a tool actually does it) →
  Observe (the result goes back to the LLM) → repeat. `create_react_agent`
  from `langgraph.prebuilt` builds this as a compiled graph for you.
- **Runnable** — LangChain's base abstraction for "something that can be
  invoked/streamed/batched." `ChatOpenAI` instances, and the whole
  compiled agent graph, are all `Runnable`s — that's why `.invoke()`,
  `.stream()`, and `.with_fallbacks()` all work the same way regardless of
  whether you're calling a raw LLM or the entire agent.
- **Checkpointer** (`MemorySaver`, used in `src/agent.py`) — LangGraph's
  mechanism for persisting conversation state between separate `.invoke()`/
  `.stream()` calls, keyed by a `thread_id`. Without one, every call is
  stateless no matter what `config` you pass — this was a real bug fixed
  during Phase 6 (see `plan.md`).
- **`stream_mode="updates"`** — one of several ways to consume
  `.stream()`; yields only what changed at each graph node, as opposed to
  `"values"` (the full accumulated state after each step) — `"updates"` is
  the natural fit here because `stream_command()` only cares about *new*
  tool calls/results/messages, not the whole growing conversation history
  each time.
- **Fallback chain** (`.with_fallbacks([...])`) — try one `Runnable`,
  transparently fall through to the next on any exception. Used for the
  NIM → OpenRouter resilience.
- **`pyqtSignal`/slot** — Qt's cross-thread-safe event mechanism. Any time
  you see `SomeClass.something = pyqtSignal(...)` plus `.emit(...)`
  somewhere and `.connect(...)` somewhere else, that's this pattern: a
  decoupled way for one part of the code to say "this happened" without
  needing to know who's listening or what thread they're on.

---

## 6. If you want to keep learning by extending this codebase

The fastest way to internalize this architecture is to add one new tool
yourself, end to end:
1. Write a new `@tool`-decorated function in a new or existing file under
   `tools/`.
2. Add it to that module's `..._tools` list, and to `ALL_TOOLS` in
   `tools/__init__.py`.
3. Optionally mention it in `SYSTEM_PROMPT` in `src/agent.py` if it needs
   specific usage guidance.
4. Write a test for it in `tests/` following the pattern in any existing
   `test_*.py` file (mock `confirm_action`/`get_llm` where relevant, use
   `tmp_path` for filesystem tests).
5. Run it for real: `python -m src.main` (CLI) and ask for something that
   should trigger it.

That loop — tool function → register it → test it → try it live — is the
entire extension mechanism for this whole project. Everything else
(the LLM routing, the confirmation gate, the sandboxing, the UI) is
infrastructure that every tool gets "for free" just by being a well-formed
`@tool` function.
