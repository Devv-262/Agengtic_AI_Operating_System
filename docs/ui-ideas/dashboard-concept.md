# UI Idea — Dashboard concept ("Daily AI" reference)

Saved 2026-09-09 as a reference for a future full dashboard UI phase (separate
from the floating bar in `ui/floating_bar.py`, which stays the quick-access
tool). Not being built yet — captured here so it isn't lost before the next
UI phase starts.

> The original reference screenshot (a "Daily AI" product dashboard) is saved
> alongside this file as `dashboard-concept.png`. The layout is also
> documented in full below for quick reference without opening the image.

## Layout

**Left sidebar (dark, ~200px)**
- Brand mark top-left ("Daily AI" style logo + wordmark)
- Nav items with icons: New Chat, Dashboard (active/highlighted), Project
  (expandable), Task, AI Models, Calendar, Analytics, Document, Team
- Bottom of sidebar: Settings, Help & Support, then a user account chip
  (avatar + name + role, e.g. "Lina · AI Executive Assistant")

**Top bar**
- Greeting, personalized: "Good Morning, {user}"
- Centered/prominent search input: "Search task, project, notes"
- Notification bell (with unread dot) + user avatar/name/role on the right

**Stat cards row (4 cards)**
- Task Today, In Progress, Completed, Focus Time
- Each: big number, label, small delta vs. yesterday (up/down arrow + count)

**Center panel — AI chat/assistant** (largest area)
- Header chip: "Get Plus" upsell tag (optional/skip for this project)
- AI assistant identity shown large: avatar + name + role ("Lina, AI
  Assistant"), giving the agent a face/persona
- Conversation as chat bubbles: user messages right-aligned, agent messages
  left-aligned with avatar, agent can post structured content (bulleted
  daily brief: meetings, tasks due, project % complete, overdue items)
- "Thinking..." inline state while the agent is working
- Quick-action chip row above the input: Summarize today / Create a task /
  Plan my day / Generate report — one-click prompts
- Bottom input bar: text field ("Type a message or ask anything..."), plus
  a "+" attach button, mic icon, send button
- Small floating action cluster to the side of the chat (edit/settings-style
  icon buttons) — secondary controls, not core

**Right sidebar (widgets column)**
- Calendar card: "Today · {date}", list of upcoming events with time +
  colored dots, "Add Event" action, "View Calendar" link in header
- Project Progress card: named projects each with a labeled progress bar
  (e.g. Website Redesign 68%, Mobile App 45%, Marketing Campaign 30%)
- Activity Feed card: recent events with icon + text + relative time
  ("You completed User Flow Design · 2h ago")
- AI Suggestion card (accent-colored, stands out): a proactive tip from the
  assistant with a call-to-action button ("Automate Now")

## Why this is relevant to Agentic-AI-OS

This is a *task/productivity dashboard* framing, distinct from the OS-control
framing the current agent has (files, shell, system settings). If a web/full
dashboard UI phase happens later, the useful ideas to borrow are:

- **Persona for the assistant** — the floating bar and CLI are currently
  faceless; giving the agent a name/avatar in a fuller UI is a small but
  real trust/personality win.
- **Quick-action chips** for common one-shot prompts, rather than requiring
  free text every time.
- **Proactive suggestion surface** — the agent volunteering a next action
  ("you could automate X") rather than only responding to input. This maps
  onto Phase 2 (Smart File Organizer) and Phase 3 (Semantic Search) once
  those exist: e.g. "12 files in Downloads look uncategorized — organize
  them?" as a standing suggestion card.
- **Activity feed** as a lightweight audit log of what the agent has done —
  overlaps with the logging item already in `plan.md` Phase 6.
- Stat cards / project progress bars don't map to this project directly
  (no task-management domain here) — skip unless the scope grows to include
  task tracking.

## Scope note

Do not start building this now. Per the user: finish implementing more
features first (see `plan.md`), then come back to UI phases one at a time.
