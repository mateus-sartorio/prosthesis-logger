from __future__ import annotations
import json
from datetime import datetime

from app.models.gait_mode import GaitMode
from app.models.log_level import LogLevel
from app.models.power_state import PowerState
from app.models.sensor_event import ParseError, SensorEvent


ParsedResult = tuple[list[SensorEvent], ParseError | None]


def parse_event_payload(topic: str, payload: str) -> ParsedResult:
    if(topic == "prothesis/actions/parsed"):
        now = datetime.now()

        try:
            command_value = int(payload.strip())
        except ValueError:
            return [], ParseError(
                reason=f"invalid command; expected an integer and got: {payload!r}",
                topic=topic,
                raw_payload=payload,
                timestamp=now,
            )

        gait_mode = GaitMode.parse_mode(command_value)
        if gait_mode is not None:
            return ([SensorEvent(
                level=LogLevel.INFO,
                sensor_name="Action",
                message=f"Gait mode changed to {gait_mode.label}({command_value}).",
                timestamp=now,
                topic=topic,
            )], None)

        power_state = PowerState.parse_state(command_value)
        if power_state is not None:
            return ([SensorEvent(
                level=LogLevel.INFO,
                sensor_name="Action",
                message=f"Power state changed to {power_state.label}({command_value}).",
                timestamp=now,
                topic=topic,
            )], None)

        valid_values = ", ".join(
            str(int(value)) for value in (*GaitMode, *PowerState)
        )
        return [], ParseError(
            reason=(
                "invalid command; expected one of "
                f"{valid_values} and got: {command_value}"
            ),
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    now = datetime.now()

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        return [], ParseError(
            reason=f"invalid json: {exc.msg}",
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    if isinstance(parsed, list):
        return _parse_sensor_readings(parsed, topic, payload, now)

    if not isinstance(parsed, dict):
        return [], ParseError(
            reason="json root must be an object or an array of readings",
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    value = parsed.get("value")
    if isinstance(value, list):
        return _parse_sensor_readings(value, topic, payload, now)

    missing = [
        key for key in ("level", "sensor_name") if key not in parsed
    ]
    if missing:
        return [], ParseError(
            reason=f"missing required fields: {', '.join(missing)}",
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    level_value = str(parsed.get("level", ""))
    sensor_name = str(parsed.get("sensor_name", "")).strip()
    message = str(parsed.get("message", "")).strip()

    level = LogLevel.parse_level(level_value)
    if level is None:
        return [], ParseError(
            reason=(
                "invalid level; expected one of INFO/WARNING/ERROR "
                f"and got: {level_value!r}"
            ),
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    if not sensor_name:
        return [], ParseError(
            reason="sensor_name must be non-empty",
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    return (
        [SensorEvent(
            level=level,
            sensor_name=sensor_name,
            message=message,
            timestamp=now,
            topic=topic,
        )],
        None,
    )


def _parse_sensor_readings(
    readings: list,
    topic: str,
    payload: str,
    now: datetime,
) -> ParsedResult:
    if not readings:
        return [], ParseError(
            reason="readings array is empty",
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    for index, reading in enumerate(readings):
        if not isinstance(reading, dict):
            return [], ParseError(
                reason=f"reading at index {index} must be an object",
                topic=topic,
                raw_payload=payload,
                timestamp=now,
            )

    events = [
        SensorEvent(
            level=LogLevel.INFO,
            sensor_name="Prosthesis",
            message=" ".join(f"{key}={value}" for key, value in reading.items()),
            timestamp=now,
            topic=topic,
        )
        for reading in readings
    ]

    return events, None
