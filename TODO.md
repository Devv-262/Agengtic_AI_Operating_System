# Agentic-AI-OS — TODO (ordered, detailed)

This is the actionable build order — more granular than `plan.md` (which is
the historical "what's done and why" record). Do these roughly top to
bottom; each section says what it is, why it matters, and how to build it,
including specific library/API choices researched for this project.

Current state: Phases 1-6 (safety, file organizer, semantic search, CLI
auto-pilot, task automation, polish/ops) are done — see `plan.md`. The
floating bar GUI redesign (visual polish, live activity log, multi-hotkey,
app icon) is also done. **Not started**: packaging, voice control, most of
`USE_CASES.md`, multi-agent orchestration.

---

## 1. Package the GUI as a real desktop app (next up)

**Why:** Right now the floating bar only launches via `python -m src.main
--gui` from a terminal. A real double-clickable `.exe` + Start
Menu/Desktop shortcut is what makes this feel like an installed app instead
of a dev tool.

**How:**
1. Add PyInstaller (`pip install pyinstaller`, add to `pyproject.toml`'s
   `dev`/new `build` optional-dependencies group).
2. Write `scripts/build_exe.py` or a `.spec` file that packages
   `ui/floating_bar.py` (or a new thin `src/gui_entry.py` that just calls
   `ui.floating_bar.main()`) as a **windowed** (no console) app, using
   `assets/icon.ico` as the icon (`--icon assets/icon.ico --windowed
   --onefile`, or `--onedir` if `--onefile` proves too slow to start —
   `--onefile` unpacks to a temp dir on every launch, which can make
   startup noticeably slower with heavy deps like this project has).
3. **Expect friction here.** This stack has non-trivial hidden imports:
   - `chromadb` + its bundled `onnxruntime` embedding model — PyInstaller
     often needs `--collect-all chromadb` / `--collect-data
     chromadb` and similar for `onnxruntime` and `tokenizers`, since these
     packages ship data files (ONNX model weights, tokenizer vocab) that
     PyInstaller's static analysis won't find on its own.
   - `PyQt6` generally packages fine, but confirm the app actually shows a
     tray icon and window when run from the built `.exe`, not just when
     run via `python -m`.
   - `keyboard` needs to run with sufficient privileges for global hooks —
     test whether the packaged `.exe` needs "Run as administrator" the
     same way the script sometimes does (see the existing floating-bar
     follow-up note in `plan.md`).
   - Iterate: build, run the `.exe` directly (not through this dev
     environment), see what's missing/broken, add hidden-imports/data
     collection flags, rebuild. Budget for a few iterations — this is the
     normal PyInstaller experience with ML-adjacent dependencies, not a
     sign something's wrong with the code.
4. Once the `.exe` works standalone, create the shortcut:
   - A `.lnk` on the Desktop and/or in the Start Menu pointing at the
     built `.exe`, using `assets/icon.ico` as its icon. Can be done with
     `pywin32`'s `win32com.client` (`Dispatch("WScript.Shell")` →
     `CreateShortcut`) or a small PowerShell snippet
     (`New-Object -ComObject WScript.Shell` → `.CreateShortcut(...)`).
   - Decide whether this is a manual one-time step you run, or an
     "installer" script (`scripts/install_shortcut.py`) — the latter is
     nicer if you ever rebuild the `.exe` and want the shortcut to keep
     pointing at the right place without redoing it by hand.
5. Update `README.md`'s setup instructions once this exists — "double-click
   the desktop icon" becomes the primary way to run it, with `python -m
   src.main --gui` as the dev-mode alternative.

---

## 2. Voice control (cloud STT + local wake word)

**Why:** "Hey [name], open X" / "turn on dark mode" by voice, per your
original ask. Decision already made: **local wake-word detection** (so the
app isn't burning API calls or bandwidth 24/7 just listening) **+ cloud
speech-to-text** (only sends audio after the wake word fires, keeping local
compute light).

**How, in order:**
1. **Local wake-word engine.** Two real options:
   - `openWakeWord` — fully open-source, pip-installable, ships pretrained
     wake words and supports training a custom one (e.g. your actual
     chosen name) with a modest number of samples. No account/API key
     needed. Best default choice.
   - Picovoice `Porcupine` — very low CPU, polished, but the free tier is
     account-gated and has usage limits; only worth it if openWakeWord's
     accuracy turns out to be a problem.
   - Start with `openWakeWord`. It needs a continuously-open microphone
     stream (`sounddevice` or `pyaudio` for capture) running on its own
     background thread — mirror the pattern already used for the global
     hotkey (`keyboard.add_hotkey` runs on its own thread and emits a Qt
     signal into the main thread; do the same here: a `QThread` that reads
     the mic stream, runs the wake-word model on rolling audio chunks, and
     `pyqtSignal`-emits when it fires).
2. **Cloud STT after wake-word fires.** Record a few seconds of audio (or
   record until a short silence is detected — simpler to start with a
   fixed window, e.g. 4-5 seconds, and improve later), then send it to a
   speech-to-text API. Options, cheapest/simplest first:
   - Groq's Whisper-compatible endpoint — very fast, has a free tier, and
     since this project is already OpenAI-SDK-shaped (`ChatOpenAI`-style
     clients), a Whisper-compatible transcription endpoint slots in
     naturally. Verify current pricing/limits before committing (things
     move fast, same lesson as the NIM model deprecation from this
     session — check live docs, don't trust older training data).
   - OpenAI's own Whisper API — reliable, not free, simplest to integrate
     if a small paid cost is fine.
   - Fully local Whisper (e.g. `faster-whisper`) — only revisit this if
     cloud STT turns out to be too laggy/expensive; you already decided
     against fully-local for the session, noting it here in case that
     changes.
3. **Wire the transcribed text into the existing pipeline.** This is the
   easy part — once you have text, it's exactly the same path as typing
   into the floating bar: call `OSAgentSystem.stream_command(text)`. No
   new agent-side code needed, just a new input source feeding the same
   `AgentWorker`.
4. **New tool: `launch_app`.** This is what makes "open American Truck
   Simulator" work. Add `tools/app_launcher.py`:
   - Windows: resolving an app name to something runnable is the real
     work. Practical approach — search the Start Menu shortcut folders
     (`%APPDATA%\Microsoft\Windows\Start Menu\Programs` and the
     all-users equivalent) for a `.lnk` whose name fuzzy-matches the
     request, and run that. This covers almost everything a user would
     say by name, including Steam games (Steam creates Start Menu
     shortcuts) without needing per-app configuration.
   - Fall back to `os.startfile(path)` (Windows-only, stdlib) once a path
     is resolved — simpler and safer than shelling out to `start`.
   - Gate it like other tools: no destructive-confirmation needed (opening
     an app isn't destructive), but log it via the existing activity-log
     pipeline so it's visible what got launched.
5. Add a status affordance in the floating bar for "listening for wake
   word" vs "idle" vs "recording" — reuse the existing status-dot pattern
   in `ui/floating_bar.py` (`_set_status`), just add the new states.

**Privacy note to keep in mind while building this:** local wake-word
detection means audio is *not* sent anywhere until the wake word fires —
make that explicit somewhere visible (README, and maybe a tray tooltip),
since "always listening" is the kind of thing that should never be a
surprise to the person running it.

---

## 3. Extended use-case tools (`USE_CASES.md`), suggested build order

Not all of `USE_CASES.md` needs building — some ideas are speculative.
Suggested priority order, cheapest/most self-contained first:

1. **`launch_app`** — covered above, do it alongside voice control since
   voice control's main demo case depends on it.
2. **Developer-focused tools** (`tools/dev_tools.py`) — cheap to build,
   reuses `execute_command`/`generate_shell_command` patterns already in
   place:
   - "Run the test suite and tell me what failed" → a tool that runs
     `pytest` (or whatever the target project uses) and returns a parsed
     summary, not raw output.
   - "Summarize what changed in the last N commits" → `git log`, feed the
     diff/log text to `think_deeply` for the summary.
   - "Find every TODO comment in this project" → simple recursive grep,
     no LLM needed.
3. **`send_email`** (`tools/communication.py`) — needs real credentials:
   - Simplest: SMTP with an app password (Gmail, Outlook, etc.) via
     Python's stdlib `smtplib` — no new dependency, works with any
     provider that supports SMTP.
   - More capable but more setup: Gmail API via OAuth — only worth it if
     you need to *read* mail too, not just send.
   - Treat this as a **confirmation-gated tool** like `delete_file` — sending
     something on your behalf is at least as consequential as deleting a
     file, arguably more (it's externally visible and can't be undone).
4. **Media tools** (`tools/media.py`) — build once voice control exists,
   since "transcribe this voice memo" reuses the STT client from step 2 of
   the voice-control section above (call it directly on an existing audio
   file instead of a live mic stream). Video→GIF and thumbnailing need
   `ffmpeg` as an external dependency (document the install step) or
   `moviepy` as a Python wrapper around it.
5. **`send_sms`** — Twilio is the standard choice; only build this if it's
   actually going to get used, since it requires a funded Twilio account
   (not free) and phone number provisioning. Lower priority than email.
6. **Privacy/security tools** — "find files that might contain sensitive
   info" is a pattern-matching tool over `semantic_search`'s existing
   indexing (regex for SSN/API-key-shaped strings, reuse
   `document_reader.extract_text`), genuinely useful and self-contained.
   "Check breached passwords" needs an external API (e.g.
   Have I Been Pwned's API) and real thought about what's sent
   externally — lower priority, higher care needed.
7. **Proactive/ambient suggestions** — save for last. This needs the app
   running persistently in the background (already true once it's a
   packaged `.exe` with a tray icon) plus a lightweight periodic scan
   (e.g. a `QTimer` that runs every N minutes, checks disk space /
   clutter heuristics, and surfaces a tray notification). Depends on
   Smart File Organizer and Semantic Search already existing (they do),
   so this is technically buildable now, but it's the most "ambient
   product design" item on the list — worth doing once everything else
   feels solid, not as a novelty first.

---

## 4. Multi-agent orchestration (router + specialized sub-agents)

**Why:** per your stated preference — instead of one agent with every tool,
a supervisor classifies the request and delegates to a scoped sub-agent
(e.g. "files", "communications", "system", "automation") that only has the
tools/permissions for its domain. This is a real architecture change, save
it for after the tool surface above actually exists — routing is much
easier to design correctly once you know what the domains and their tools
actually are, rather than guessing upfront.

**How (when you get here):**
- LangGraph supports this natively via a supervisor graph: a router node
  (an LLM call classifying the request into a domain) that conditionally
  routes to one of several sub-agent subgraphs, each built the same way
  `os_agent` is built today in `src/agent.py` (`create_react_agent` with a
  *scoped* tool list instead of `ALL_TOOLS`).
- `tools/__init__.py` already groups tools by module (`file_manager_tools`,
  `system_controller_tools`, etc.) — that grouping becomes the natural
  permission boundary for each sub-agent, so this is less of a rewrite
  than it sounds; the grouping work is already done.
- The confirmation gate, path sandbox, and command blocklist
  (`tools/_confirm.py`, `tools/_safety.py`) don't change — they're
  per-tool, not per-agent, so they keep working unmodified under a
  multi-agent setup.

---

## 5. Full dashboard UI

Lowest priority, already noted in `plan.md` and `docs/ui-ideas/dashboard-concept.md`.
Only worth doing once proactive suggestions (section 3, item 7) actually
have something to show — a dashboard with nothing to display is just
empty chrome.
