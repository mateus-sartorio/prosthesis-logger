from __future__ import annotations
from dataclasses import dataclass
import os

from app.models.log_level import LogLevel
from app.utils import split_comma_separated_value


@dataclass(slots=True, init=False)
class Settings:
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str | None
    mqtt_password: str | None
    mqtt_topic: str
    mqtt_qos: int
    mqtt_client_id: str
    min_log_level: LogLevel | None
    sensor_names: set[str] | None

    def __init__(
        self,
        mqtt_host: str | None,
        mqtt_port: int | None,
        mqtt_username: str | None,
        mqtt_password: str | None,
        mqtt_topic: str | None,
        mqtt_qos: int,
        mqtt_client_id: str | None,
        min_log_level: LogLevel | None,
        sensor_names: set[str] | None,
    ) -> None:
        self.mqtt_host = mqtt_host or os.getenv("MQTT_HOST", "localhost")
        self.mqtt_port = mqtt_port or int(os.getenv("MQTT_PORT", "1883"))
        self.mqtt_username = mqtt_username or os.getenv("MQTT_USERNAME") or None
        self.mqtt_password = mqtt_password or os.getenv("MQTT_PASSWORD") or None
        self.mqtt_topic = mqtt_topic or os.getenv("MQTT_TOPIC", "prothesis/logs/parsed")
        self.mqtt_qos = mqtt_qos or int(os.getenv("MQTT_QOS", "1"))
        self.mqtt_client_id = mqtt_client_id or os.getenv("MQTT_CLIENT_ID", "prothesis-logger")
        self.min_log_level = min_log_level if min_log_level is not None else LogLevel.parse_level(os.getenv("MIN_LOG_LEVEL", "INFO"))
        self.sensor_names = sensor_names