from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from app.models.log_level import LogLevel
from app.models.sensor_event import SensorEvent, level_meets_minimum


@dataclass(slots=True)
class FilterSnapshot:
    min_log_level: LogLevel | None
    sensor_names: set[str]


@dataclass(slots=True)
class FilterState:
    min_log_level: LogLevel | None = None
    sensor_names: set[str] = field(default_factory=set)


class ThreadSafeFilters:
    def __init__(
        self,
        min_log_level: LogLevel | None = None,
        sensor_names: set[str] | None = None,
    ) -> None:
        self._lock = Lock()
        self._state = FilterState(
            min_log_level=min_log_level,
            sensor_names=sensor_names or set(),
        )

    def snapshot(self) -> FilterSnapshot:
        with self._lock:
            return FilterSnapshot(
                min_log_level=self._state.min_log_level,
                sensor_names=set(self._state.sensor_names),
            )

    def clear_all(self) -> None:
        with self._lock:
            self._state.min_log_level = None
            self._state.sensor_names.clear()

    def set_min_log_level(self, min_log_level: LogLevel | None) -> None:
        with self._lock:
            self._state.min_log_level = min_log_level

    def set_sensor_names(self, values: set[str]) -> None:
        with self._lock:
            self._state.sensor_names = {item.strip() for item in values if item.strip()}

    def matches(self, event: SensorEvent) -> bool:
        with self._lock:
            if not level_meets_minimum(event.level, self._state.min_log_level):
                return False

            if self._state.sensor_names and event.sensor_name not in self._state.sensor_names:
                return False

            return True
