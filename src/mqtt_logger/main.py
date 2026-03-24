from __future__ import annotations

import threading
import time
from queue import Empty, Queue

import typer

from mqtt_logger.config import build_config
from mqtt_logger.filters import ThreadSafeFilters
from mqtt_logger.models import parse_level
from mqtt_logger.mqtt_client import MqttSettings, MqttSubscriber
from mqtt_logger.parser import parse_event_payload
from mqtt_logger.renderer import TerminalRenderer
from mqtt_logger.runtime_controls import ControlAction, RuntimeController

app = typer.Typer(add_completion=False)


def _csv_to_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


@app.command()
def run(
    broker: str | None = typer.Option(None, "--broker", help="MQTT broker host"),
    port: int | None = typer.Option(None, "--port", help="MQTT broker port"),
    topic: str | None = typer.Option(None, "--topic", help="MQTT topic subscription"),
    username: str | None = typer.Option(None, "--username", help="MQTT username"),
    password: str | None = typer.Option(None, "--password", help="MQTT password"),
    min_level: str | None = typer.Option(
        None,
        "--min-level",
        help="Minimum level filter: normal|warning|error",
    ),
    sensor_type: str | None = typer.Option(
        None,
        "--sensor-type",
        help="Sensor type filter, comma separated",
    ),
    sensor_name: str | None = typer.Option(
        None,
        "--sensor-name",
        help="Sensor name filter, comma separated",
    ),
) -> None:
    config = build_config(
        broker=broker,
        port=port,
        topic=topic,
        username=username,
        password=password,
        min_level=min_level,
        sensor_type=sensor_type,
        sensor_name=sensor_name,
    )

    renderer = TerminalRenderer()
    filters = ThreadSafeFilters(
        min_level=config.min_level,
        sensor_types=config.sensor_types,
        sensor_names=config.sensor_names,
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
            renderer.print_system("Message queue full; dropping incoming message", style="bold red")

    def prompt_text(prompt: str) -> str:
        with prompt_lock:
            renderer.print_system("Interactive input mode enabled", style="bold blue")
            return renderer.console.input(f"[bold cyan]{prompt}[/bold cyan]")

    mqtt = MqttSubscriber(
        settings=MqttSettings(
            broker=config.broker,
            port=config.port,
            topic=config.topic,
            username=config.username,
            password=config.password,
            qos=1,
        ),
        on_message=on_message,
        on_system=on_system,
    )

    controller = RuntimeController(action_queue=controls, prompt_text=prompt_text)

    renderer.print_banner(config.broker, config.port, config.topic)
    renderer.print_runtime_help()
    renderer.print_filters(filters.snapshot())

    mqtt.start()
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
        mqtt.stop()
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

        if action.kind == "set_min_level":
            level = parse_level(action.value or "") if action.value else None
            filters.set_min_level(level)
            label = level.value if level else "none"
            renderer.print_system(f"Minimum level set to {label}", style="bold cyan")
            renderer.print_filters(filters.snapshot())
            continue

        if action.kind == "set_sensor_types":
            filters.set_sensor_types(_csv_to_set(action.value))
            renderer.print_system("Updated sensor_type filter", style="bold cyan")
            renderer.print_filters(filters.snapshot())
            continue

        if action.kind == "set_sensor_names":
            filters.set_sensor_names(_csv_to_set(action.value))
            renderer.print_system("Updated sensor_name filter", style="bold cyan")
            renderer.print_filters(filters.snapshot())
            continue


if __name__ == "__main__":
    app()
