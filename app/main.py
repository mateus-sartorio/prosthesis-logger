from __future__ import annotations

import threading
import time
from queue import Empty, Queue

import typer

from app.models.log_level import LogLevel
from app.settings import Settings
from app.filters import ThreadSafeFilters
from app.services.mqtt_service import MqttSettings, MqttService
from app.parser import parse_event_payload
from app.renderer import TerminalRenderer
from app.runtime_controls import ControlAction, RuntimeController
from app.utils import split_comma_separated_value

app = typer.Typer(add_completion=False)


@app.command()
def main(
    mqtt_broker: str | None = typer.Option(
        None, "--mqtt_broker", help="MQTT broker host"
    ),
    mqtt_port: int | None = typer.Option(None, "--mqtt_port", help="MQTT broker port"),
    mqtt_topic: str | None = typer.Option(
        None, "--mqtt_topic", help="MQTT topic subscription"
    ),
    mqtt_username: str | None = typer.Option(
        None, "--mqtt_username", help="MQTT username"
    ),
    mqtt_password: str | None = typer.Option(
        None, "--mqtt_password", help="MQTT password"
    ),
    min_log_level: str | None = typer.Option(
        None,
        "--min-log-level",
        help="Minimum log level filter: INFO|WARNING|ERROR",
    ),
    sensor_names: str | None = typer.Option(
        None,
        "--sensor-names",
        help="Sensor name filter, comma separated",
    ),
) -> None:
    settings = Settings(
        mqtt_host=mqtt_broker,
        mqtt_port=mqtt_port,
        mqtt_username=mqtt_username,
        mqtt_password=mqtt_password,
        mqtt_topic=mqtt_topic,
        mqtt_qos=1,
        mqtt_client_id=None,
        min_log_level=LogLevel.parse_level(min_log_level) if min_log_level else None,
        sensor_names=split_comma_separated_value(sensor_names) if sensor_names is not None else None,
    )

    renderer = TerminalRenderer()

    filters = ThreadSafeFilters(
        min_log_level=settings.min_log_level,
        sensor_names=settings.sensor_names,
    )

    raw_messages: Queue[tuple[str, str]] = Queue(maxsize=2000)
    controls: Queue[ControlAction] = Queue(maxsize=100)
    stop_event = threading.Event()
    prompt_lock = threading.Lock()

    def on_system(text: str) -> None:
        renderer.print_system(text)

    def on_message(topic_name: str, payload: str) -> None:
        try:
            raw_messages.put_nowait((topic_name, payload))
        except Exception:
            renderer.print_system(
                "Message queue full; dropping incoming message", style="bold red"
            )

    def prompt_text(prompt: str) -> str:
        with prompt_lock:
            renderer.print_system("Interactive input mode enabled", style="bold blue")
            return renderer.console.input(f"[bold cyan]{prompt}[/bold cyan]")

    mqtt_service = MqttService(
        settings=MqttSettings(
            broker=settings.mqtt_host,
            port=settings.mqtt_port,
            topic=settings.mqtt_topic,
            username=settings.mqtt_username,
            password=settings.mqtt_password,
            qos=settings.mqtt_qos,
        ),
        on_message=on_message,
        on_system=on_system,
    )

    controller = RuntimeController(action_queue=controls, prompt_text=prompt_text)

    renderer.print_banner(settings.mqtt_host, settings.mqtt_port, settings.mqtt_topic)
    renderer.print_runtime_help()
    renderer.print_filters(filters.snapshot())

    mqtt_service.start()
    controller.start()

    try:
        while not stop_event.is_set():
            _drain_controls(controls, filters, renderer, stop_event)

            try:
                topic_name, payload = raw_messages.get(timeout=0.2)
            except Empty:
                continue

            event, parse_error = parse_event_payload(topic=topic_name, payload=payload)
            if parse_error is not None:
                renderer.print_parse_error(parse_error)
                continue

            if event is None:
                continue

            if filters.matches(event):
                with prompt_lock:
                    renderer.print_event(event)
    except KeyboardInterrupt:
        renderer.print_system("Interrupted by user", style="bold yellow")
    finally:
        stop_event.set()
        controller.stop()
        mqtt_service.stop()
        time.sleep(0.1)
        renderer.print_system("Logger stopped", style="bold yellow")


def _drain_controls(
    controls: Queue[ControlAction],
    filters: ThreadSafeFilters,
    renderer: TerminalRenderer,
    stop_event: threading.Event,
) -> None:
    while True:
        try:
            action = controls.get_nowait()
        except Empty:
            return

        if action.kind == "help":
            renderer.print_runtime_help()
            continue

        if action.kind == "quit":
            stop_event.set()
            continue

        if action.kind == "clear":
            filters.clear_all()
            renderer.print_system("All filters cleared", style="bold green")
            renderer.print_filters(filters.snapshot())
            continue

        if action.kind == "set_min_log_level":
            level = LogLevel.parse_level(action.value or "") if action.value else None
            filters.set_min_log_level(level)
            label = level.value if level else "none"
            renderer.print_system(
                f"Minimum log level set to {label}", style="bold cyan"
            )
            renderer.print_filters(filters.snapshot())
            continue

        if action.kind == "set_sensor_names":
            filters.set_sensor_names(split_comma_separated_value(action.value))
            renderer.print_system("Updated sensor_name filter", style="bold cyan")
            renderer.print_filters(filters.snapshot())
            continue


if __name__ == "__main__":
    app()
