from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from mqtt_logger.models import EventLevel, SensorEvent, level_meets_minimum


@dataclass(slots=True)
class FilterSnapshot:
    min_level: EventLevel | None
    sensor_types: set[str]
    sensor_names: set[str]


@dataclass(slots=True)
class FilterState:
    min_level: EventLevel | None = None
    sensor_types: set[str] = field(default_factory=set)
    sensor_names: set[str] = field(default_factory=set)


class ThreadSafeFilters:
    def __init__(
        self,
        min_level: EventLevel | None = None,
        sensor_types: set[str] | None = None,
        sensor_names: set[str] | None = None,
    ) -> None:
        self._lock = Lock()
        self._state = FilterState(
            min_level=min_level,
            sensor_types=sensor_types or set(),
            sensor_names=sensor_names or set(),
        )

    def snapshot(self) -> FilterSnapshot:
        with self._lock:
            return FilterSnapshot(
                min_level=self._state.min_level,
                sensor_types=set(self._state.sensor_types),
                sensor_names=set(self._state.sensor_names),
            )

    def clear_all(self) -> None:
        with self._lock:
            self._state.min_level = None
            self._state.sensor_types.clear()
            self._state.sensor_names.clear()

    def set_min_level(self, min_level: EventLevel | None) -> None:
        with self._lock:
            self._state.min_level = min_level

    def set_sensor_types(self, values: set[str]) -> None:
        with self._lock:
            self._state.sensor_types = {item.strip() for item in values if item.strip()}

    def set_sensor_names(self, values: set[str]) -> None:
        with self._lock:
            self._state.sensor_names = {item.strip() for item in values if item.strip()}

    def matches(self, event: SensorEvent) -> bool:
        with self._lock:
            if not level_meets_minimum(event.level, self._state.min_level):
                return False

            if self._state.sensor_types and event.sensor_type not in self._state.sensor_types:
                return False

            if self._state.sensor_names and event.sensor_name not in self._state.sensor_names:
                return False

            return True
