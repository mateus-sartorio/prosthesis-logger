from mqtt_logger.models import EventLevel
from mqtt_logger.parser import parse_event_payload


def test_parse_valid_event() -> None:
    event, parse_error = parse_event_payload(
        topic="sensors/logs",
        payload='{"level": "warning", "sensor_type": "temperature", "sensor_name": "temp-01", "message": "high temperature detected"}',
    )

    assert parse_error is None
    assert event is not None
    assert event.level == EventLevel.WARNING
    assert event.sensor_type == "temperature"
    assert event.sensor_name == "temp-01"
    assert event.message == "high temperature detected"


def test_parse_accepts_missing_message_field() -> None:
    event, parse_error = parse_event_payload(
        topic="sensors/logs",
        payload='{"level": "warning", "sensor_type": "temperature", "sensor_name": "temp-01"}',
    )

    assert parse_error is None
    assert event is not None
    assert event.message == ""


def test_parse_rejects_invalid_json() -> None:
    event, parse_error = parse_event_payload(topic="sensors/logs", payload="not json")

    assert event is None
    assert parse_error is not None
    assert "invalid json" in parse_error.reason


def test_parse_rejects_missing_field() -> None:
    event, parse_error = parse_event_payload(
        topic="sensors/logs",
        payload='{"level": "normal", "sensor_type": "temperature"}',
    )

    assert event is None
    assert parse_error is not None
    assert "missing required fields" in parse_error.reason
