"""
main.py
Entry point for the CrowdWisdomTrading Ad Creation AI Agent pipeline.
Run: python main.py
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_banner():
    banner = Text()
    banner.append("CrowdWisdomTrading\n", style="bold yellow")
    banner.append("Daily Ads AI Agent Pipeline\n", style="bold white")
    banner.append("─" * 40 + "\n", style="dim")
    banner.append("Agent 1: Meta Ads Research (Apify)\n", style="cyan")
    banner.append("Agent 2: Marketing Insight Extractor\n", style="cyan")
    banner.append("Agent 3: Ad Script Writer (GDrive)\n", style="cyan")
    banner.append("Agent 4: Video Creator (HF + ElevenLabs)\n", style="cyan")
    banner.append("Renderer: Remotion MP4 Output\n", style="cyan")
    console.print(Panel(banner, border_style="yellow", padding=(1, 4)))


def check_env():
    """Validate env vars before starting. Exit with helpful messages if missing."""
    from config.settings import settings

    missing = settings.validate()
    if missing:
        console.print(
            f"\n[red]✗ Missing required environment variables:[/red] {', '.join(missing)}\n"
            "Copy [bold].env.example[/bold] → [bold].env[/bold] and fill in your keys.\n",
        )
        sys.exit(1)

    console.print("[green]✓ Environment variables validated[/green]")

    # Warn about optional keys
    optionals = {
        "ELEVENLABS_API_KEY": settings.ELEVENLABS_API_KEY,
        "HF_API_TOKEN": settings.HF_API_TOKEN,
        "GDRIVE_FILE_ID": settings.GDRIVE_FILE_ID,
    }
    for name, val in optionals.items():
        if not val:
            console.print(f"[yellow]⚠ {name} not set — will use fallback/placeholder[/yellow]")


def ensure_output_dirs():
    from config.settings import settings
    for d in [
        settings.JSON_DIR,
        settings.SCRIPTS_DIR,
        settings.AUDIO_DIR,
        settings.IMAGES_DIR,
        settings.VIDEOS_DIR,
        settings.LOGS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
    console.print("[green]✓ Output directories ready[/green]")


def main():
    print_banner()
    check_env()
    ensure_output_dirs()

    console.print("\n[bold yellow]Starting pipeline...[/bold yellow]\n")

    from flows.ad_creation_flow import AdCreationFlow

    flow = AdCreationFlow()
    try:
        flow.kickoff()

        console.print(
            Panel(
                f"[bold green]✓ Pipeline complete![/bold green]\n\n"
                f"Video: [cyan]{flow.state.video_path}[/cyan]\n"
                f"Check [cyan]output/pipeline_summary.json[/cyan] for all asset paths.",
                title="Done",
                border_style="green",
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Pipeline failed: {e}[/red]")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()