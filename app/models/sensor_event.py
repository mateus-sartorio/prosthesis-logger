from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models.log_level import LogLevel


@dataclass(slots=True)
class SensorEvent:
    level: LogLevel
    timestamp: datetime
    sensor_name: str
    topic: str
    message: str = ""


@dataclass(slots=True)
class ParseError:
    reason: str
    topic: str
    raw_payload: str
    timestamp: datetime


def level_meets_minimum(level: LogLevel, minimum: LogLevel | None) -> bool:
    if minimum is None:
        return True
    return level.value >= minimum.value
