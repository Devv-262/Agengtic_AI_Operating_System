"""
ui/cli.py
---------
Role: Rich-based interactive terminal interface for the Agentic-AI-OS.
Wraps OSAgentSystem with a formatted banner, spinner while the agent is
thinking/acting, and markdown-rendered responses.
"""
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.agent import OSAgentSystem

APP_NAME = "Agentic-AI-OS"
APP_VERSION = "0.2.0"
EXIT_CMDS = {"exit", "quit", "q", ":q"}

console = Console()


def _print_banner() -> None:
    console.print(
        Panel.fit(
            f"[bold cyan]{APP_NAME}[/bold cyan] [dim]v{APP_VERSION}[/dim]\n"
            "[dim]Powered by NVIDIA NIM + OpenRouter (free tier) · LangGraph ReAct agent[/dim]\n\n"
            "Type your command in plain English.\n"
            "Type 'exit' / 'quit' / 'q' to shut down.",
            border_style="cyan",
        )
    )


def run() -> None:
    """Bootstrap the OS Agent and enter the interactive Rich REPL."""
    _print_banner()

    with console.status("[cyan]Initialising agent...", spinner="dots"):
        try:
            agent = OSAgentSystem()
        except Exception as exc:
            console.print(f"[bold red]Failed to initialise the agent:[/bold red] {exc}")
            raise SystemExit(1)

    console.print("[green]Agent ready.[/green]\n")

    while True:
        try:
            user_input = console.input("[bold blue]You[/bold blue] › ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in EXIT_CMDS:
            console.print("[dim]Goodbye![/dim]")
            break

        # Note: deliberately not wrapped in a live spinner — destructive tools
        # (delete/move/shell exec) may pause mid-run to prompt for
        # confirmation via input(), which a Rich Live display would corrupt.
        console.print("[cyan]Thinking...[/cyan]")
        response = agent.process_command(user_input)

        console.print("[bold magenta]Agent[/bold magenta] ›")
        console.print(Markdown(response))
        console.print()


if __name__ == "__main__":
    run()
