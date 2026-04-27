from __future__ import annotations
import json
from datetime import datetime

from app.models.log_level import LogLevel
from app.models.sensor_event import ParseError, SensorEvent


ParsedResult = tuple[SensorEvent | None, ParseError | None]


def parse_event_payload(topic: str, payload: str) -> ParsedResult:
    now = datetime.now()
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        return None, ParseError(
            reason=f"invalid json: {exc.msg}",
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    if not isinstance(parsed, dict):
        return None, ParseError(
            reason="json root must be an object",
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    missing = [
        key for key in ("level", "sensor_name") if key not in parsed
    ]
    if missing:
        return None, ParseError(
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
        return None, ParseError(
            reason=(
                "invalid level; expected one of INFO/WARNING/ERROR "
                f"and got: {level_value!r}"
            ),
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    if not sensor_name:
        return None, ParseError(
            reason="sensor_name must be non-empty",
            topic=topic,
            raw_payload=payload,
            timestamp=now,
        )

    return (
        SensorEvent(
            level=level,
            sensor_name=sensor_name,
            message=message,
            timestamp=now,
            topic=topic,
        ),
        None,
    )
