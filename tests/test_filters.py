from datetime import datetime

from mqtt_logger.filters import ThreadSafeFilters
from mqtt_logger.models import EventLevel, SensorEvent


def _event(level: EventLevel, sensor_type: str = "temperature", sensor_name: str = "temp-01") -> SensorEvent:
    return SensorEvent(
        level=level,
        sensor_type=sensor_type,
        sensor_name=sensor_name,
        timestamp=datetime.now(),
        topic="sensors/logs",
        raw_payload="{}",
    )


def test_no_filters_matches_everything() -> None:
    filters = ThreadSafeFilters()

    assert filters.matches(_event(EventLevel.NORMAL))
    assert filters.matches(_event(EventLevel.WARNING))
    assert filters.matches(_event(EventLevel.ERROR))


def test_min_level_is_severity_based() -> None:
    filters = ThreadSafeFilters(min_level=EventLevel.WARNING)

    assert not filters.matches(_event(EventLevel.NORMAL))
    assert filters.matches(_event(EventLevel.WARNING))
    assert filters.matches(_event(EventLevel.ERROR))


def test_and_logic_between_filters() -> None:
    filters = ThreadSafeFilters(
        min_level=EventLevel.NORMAL,
        sensor_types={"temperature"},
        sensor_names={"temp-01"},
    )

    assert filters.matches(_event(EventLevel.WARNING, "temperature", "temp-01"))
    assert not filters.matches(_event(EventLevel.WARNING, "pressure", "temp-01"))
    assert not filters.matches(_event(EventLevel.WARNING, "temperature", "temp-02"))
