from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from mqtt_logger.models import EventLevel, parse_level


@dataclass(slots=True)
class AppConfig:
    broker: str
    port: int
    topic: str
    username: str | None
    password: str | None
    min_level: EventLevel | None
    sensor_types: set[str]
    sensor_names: set[str]


def _split_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def _normalize_level(value: str | None) -> EventLevel | None:
    if not value:
        return None
    return parse_level(value)


def _pick_value(cli_value: str | None, env_keys: tuple[str, ...], default: str) -> str:
    if cli_value:
        return cli_value
    for key in env_keys:
        value = os.getenv(key)
        if value:
            return value
    return default


def build_config(
    broker: str | None,
    port: int | None,
    topic: str | None,
    username: str | None,
    password: str | None,
    min_level: str | None,
    sensor_type: str | None,
    sensor_name: str | None,
) -> AppConfig:
    dotenv_path = find_dotenv(filename=".env", usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path)
    else:
        project_root_env = Path(__file__).resolve().parents[2] / ".env"
        if project_root_env.exists():
            load_dotenv(dotenv_path=project_root_env)

    broker_value = _pick_value(broker, ("MQTT_BROKER", "MQTT_HOST"), "localhost")
    port_value = port if port is not None else int(os.getenv("MQTT_PORT", "1883"))
    topic_value = _pick_value(topic, ("MQTT_TOPIC", "MQTT_PARSED_TOPIC"), "#")

    username_value = username if username is not None else os.getenv("MQTT_USERNAME")
    password_value = password if password is not None else os.getenv("MQTT_PASSWORD")

    min_level_value = _normalize_level(min_level if min_level is not None else os.getenv("MQTT_MIN_LEVEL"))

    sensor_types_value = _split_csv(sensor_type if sensor_type is not None else os.getenv("MQTT_SENSOR_TYPE"))
    sensor_names_value = _split_csv(sensor_name if sensor_name is not None else os.getenv("MQTT_SENSOR_NAME"))

    return AppConfig(
        broker=broker_value,
        port=port_value,
        topic=topic_value,
        username=username_value,
        password=password_value,
        min_level=min_level_value,
        sensor_types=sensor_types_value,
        sensor_names=sensor_names_value,
    )
