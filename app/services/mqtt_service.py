from __future__ import annotations
from paho.mqtt.enums import CallbackAPIVersion

from dataclasses import dataclass
from typing import Callable

import paho.mqtt.client as mqtt


@dataclass(slots=True)
class MqttSettings:
    broker: str
    port: int
    logs_topic: str
    command_logs_topic: str
    keepalive: int = 60
    username: str | None = None
    password: str | None = None
    qos: int = 1
    tls_enabled: bool = False


class MqttService:
    def __init__(
        self,
        settings: MqttSettings,
        on_message: Callable[[str, str], None],
        on_system: Callable[[str], None],
    ) -> None:
        self._settings = settings
        self._on_message = on_message
        self._on_system = on_system

        self._client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        if settings.username:
            self._client.username_pw_set(settings.username, settings.password)

        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_mqtt_message

        self._configure_tls()

    def start(self) -> None:
        self._client.connect_async(
            host=self._settings.broker,
            port=self._settings.port,
            keepalive=self._settings.keepalive,
        )
        self._client.loop_start()

    def stop(self) -> None:
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            # Cleanup should never crash shutdown.
            pass

    def _on_connect(self, client: mqtt.Client, *_args) -> None:
        client.subscribe(self._settings.logs_topic, qos=self._settings.qos)
        self._on_system(f"Connected and subscribed to {self._settings.logs_topic!r} with qos={self._settings.qos}")

        client.subscribe(self._settings.command_logs_topic, qos=self._settings.qos)
        self._on_system(f"Connected and subscribed to {self._settings.command_logs_topic!r} with qos={self._settings.qos}")

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata,
        _disconnect_flags,
        reason_code,
        _properties,
    ) -> None:
        if reason_code == 0:
            self._on_system("Disconnected from broker")
        else:
            self._on_system(f"Disconnected unexpectedly (reason_code={reason_code})")

    def _configure_tls(self) -> None:
        """
        Configure TLS settings based on MQTT_TLS environment variable and port.

        TLS is enabled if MQTT_TLS environment variable is set to 'true'
        """
        if self._settings.tls_enabled:
            self._client.tls_set()

    def _on_mqtt_message(
        self, _client: mqtt.Client, _userdata, message: mqtt.MQTTMessage
    ) -> None:
        payload = message.payload.decode("utf-8", errors="replace")
        self._on_message(message.topic, payload)
