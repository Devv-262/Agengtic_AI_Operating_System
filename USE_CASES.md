# Agentic-AI-OS — Use Cases

A running list of things this agent should be able to do — some already built, most as ideas for what to add next. Organized by category, one line each.

## File Management ✅ built
- "Clean up my Downloads folder" — sort into logical categories, not just by extension
- "Undo that last cleanup"
- "Move all invoices from this month into a Finance folder"
- "Delete every file in this folder older than a year" (with confirmation)
- "Rename these files to match a pattern"

## Search & Discovery ✅ built
- "Find the PDF about machine learning I downloaded last week"
- "Where's that spreadsheet with the Q3 numbers?"
- "Show me every file that mentions this client's name"
- "What did I write about in my notes last month?"

## Documents ✅ built
- "Summarize this contract and tell me the payment terms"
- "What's the total due on this invoice?"
- "Compare these two PDFs and tell me what changed"
- "Extract every email address mentioned in this document"
- "Turn this messy report into bullet points"

## Shell / CLI Automation ✅ built
- "Find all files over 1GB and list them"
- "Show me what's using the most disk space in this folder"
- "Kill whatever process is using port 3000"
- "Check if Python and Node are installed and what versions"

## System Control ✅ built (partial)
- "Turn on dark mode"
- "Set volume to 30%"
- "What OS/version am I running?"
- "Toggle Wi-Fi off" — not yet
- "Put the display to sleep in 10 minutes" — not yet
- "Show me current CPU/RAM/battery usage" — not yet

## Task Automation / Chaining ✅ built (partial)
- "Resize all images in this folder to 1080p and zip them"
- "Extract this archive and organize what's inside"
- "Convert all these .docx files to PDF" — not yet
- "Batch-rename and watermark these photos" — not yet
- "Back up this folder to another drive on a schedule" — not yet

## Productivity & Daily Use — ideas
- "What do I have due today?" (reads a to-do/notes file, summarizes)
- "Draft a reply to this email" (given pasted/read content)
- "Take these meeting notes and turn them into action items"
- "Remind me about X in an hour" (local scheduled notification)
- "Read me the headlines from my saved articles folder"

## Developer-Focused — ideas
- "Run the test suite and tell me what failed"
- "Summarize what changed in the last 5 commits"
- "Find every TODO comment in this project"
- "Set up a new Python virtual environment and install these packages"
- "Check my code for obvious security issues before I commit"

## Media & Creative — ideas
- "Convert this video to a GIF"
- "Transcribe this voice memo"
- "Generate thumbnails for all videos in this folder"
- "Strip metadata/EXIF data from these photos before I share them"

## Privacy & Security — ideas
- "Find files that might contain sensitive info (SSNs, API keys, passwords)"
- "Show me what apps have access to my webcam/microphone"
- "Check if any of my saved passwords appear in a known breach" (needs explicit opt-in, external API)
- "Securely delete this file" (multi-pass overwrite, not just move to trash)

## Cross-App / Integration — ideas
- "Add this to my calendar"
- "Send this file to [contact] via email"
- "Save this webpage as a PDF into my Research folder"
- "Sync my notes folder with a cloud backup"

## Proactive / Ambient — ideas (needs the agent running in the background, not just on-demand)
- Notice a folder getting cluttered and suggest organizing it
- Notice a large duplicate file and suggest removing it
- Notice disk space getting low and suggest what's safe to clean up
- Weekly digest: "here's what changed on your desktop this week"

---
Not a commitment list — see `plan.md` for what's actually scheduled to be built next. This file is just a brainstorm to pull from.
