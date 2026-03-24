from __future__ import annotations

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from mqtt_logger.filters import FilterSnapshot
from mqtt_logger.models import EventLevel, ParseError, SensorEvent


class TerminalRenderer:
    def __init__(self) -> None:
        self.console = Console()

    def _level_style(self, level: EventLevel) -> str:
        if level == EventLevel.NORMAL:
            return "bold bright_cyan"
        if level == EventLevel.WARNING:
            return "bold yellow"
        return "bold white on red"

    def print_banner(self, broker: str, port: int, topic: str) -> None:
        table = Table.grid(expand=True)
        table.add_column(justify="left")
        table.add_column(justify="right")
        table.add_row("[bold green]MQTT Terminal Logger[/bold green]", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row(f"Broker: [cyan]{broker}:{port}[/cyan]", f"Topic: [magenta]{topic}[/magenta]")
        self.console.print(Panel(table, border_style="green"))

    def print_runtime_help(self) -> None:
        self.console.print(
            Panel(
                "[bold]Runtime keys[/bold]\n"
                "[cyan]h[/cyan] help | [cyan]0/1/2/3[/cyan] min level | "
                "[cyan]t[/cyan] set sensor type | [cyan]n[/cyan] set sensor name | "
                "[cyan]c[/cyan] clear filters | [cyan]q[/cyan] quit",
                border_style="blue",
                title="Controls",
            )
        )

    def print_filters(self, snapshot: FilterSnapshot) -> None:
        level = snapshot.min_level.value if snapshot.min_level else "none"
        types = ", ".join(sorted(snapshot.sensor_types)) if snapshot.sensor_types else "none"
        names = ", ".join(sorted(snapshot.sensor_names)) if snapshot.sensor_names else "none"
        self.console.print(
            Panel(
                f"[bold]Active filters[/bold]\n"
                f"min_level: [yellow]{level}[/yellow]\n"
                f"sensor_types: [yellow]{types}[/yellow]\n"
                f"sensor_names: [yellow]{names}[/yellow]",
                border_style="cyan",
                title="Filter Panel",
            )
        )

    def print_event(self, event: SensorEvent) -> None:
        ts = event.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        prefix = Text(f"[{ts}] ")
        level = Text(event.level.value.upper(), style=self._level_style(event.level))
        details = Text(f"  {event.sensor_type}/{event.sensor_name}  ")
        topic = Text(f"topic={event.topic}", style="dim")
        message = Text(f"  {event.message}") if event.message else Text()
        self.console.print(prefix.append_text(level).append_text(details).append_text(topic).append_text(message))

    def print_parse_error(self, parse_error: ParseError) -> None:
        ts = parse_error.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.console.print(
            f"[dim][{ts}][/dim] [bold red]PARSE_ERROR[/bold red] "
            f"{parse_error.reason} [dim]topic={parse_error.topic} payload={parse_error.raw_payload!r}[/dim]"
        )

    def print_system(self, message: str, style: str = "bold green") -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.console.print(f"[dim][{ts}][/dim] [{style}]{message}[/{style}]")
