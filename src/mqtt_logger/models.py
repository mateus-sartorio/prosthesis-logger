from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventLevel(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    ERROR = "error"


_LEVEL_ORDER: dict[EventLevel, int] = {
    EventLevel.NORMAL: 0,
    EventLevel.WARNING: 1,
    EventLevel.ERROR: 2,
}


@dataclass(slots=True)
class SensorEvent:
    level: EventLevel
    sensor_type: str
    sensor_name: str
    timestamp: datetime
    topic: str
    raw_payload: str
    message: str = ""


@dataclass(slots=True)
class ParseError:
    reason: str
    topic: str
    raw_payload: str
    timestamp: datetime


def parse_level(value: str) -> EventLevel | None:
    lowered = value.strip().lower()
    for level in EventLevel:
        if level.value == lowered:
            return level
    return None


def level_meets_minimum(level: EventLevel, minimum: EventLevel | None) -> bool:
    if minimum is None:
        return True
    return _LEVEL_ORDER[level] >= _LEVEL_ORDER[minimum]
