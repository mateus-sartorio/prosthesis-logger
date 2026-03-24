from mqtt_logger.config import build_config


def test_cli_values_override_env(monkeypatch) -> None:
    monkeypatch.setenv("MQTT_BROKER", "env-broker")
    monkeypatch.setenv("MQTT_PORT", "1884")
    monkeypatch.setenv("MQTT_TOPIC", "env/topic")

    cfg = build_config(
        broker="cli-broker",
        port=1999,
        topic="cli/topic",
        username=None,
        password=None,
        min_level=None,
        sensor_type=None,
        sensor_name=None,
    )

    assert cfg.broker == "cli-broker"
    assert cfg.port == 1999
    assert cfg.topic == "cli/topic"


def test_env_values_apply_when_cli_missing(monkeypatch) -> None:
    monkeypatch.setenv("MQTT_BROKER", "env-broker")
    monkeypatch.setenv("MQTT_PORT", "1884")
    monkeypatch.setenv("MQTT_TOPIC", "env/topic")

    cfg = build_config(
        broker=None,
        port=None,
        topic=None,
        username=None,
        password=None,
        min_level=None,
        sensor_type=None,
        sensor_name=None,
    )

    assert cfg.broker == "env-broker"
    assert cfg.port == 1884
    assert cfg.topic == "env/topic"


def test_alias_env_names_are_supported(monkeypatch) -> None:
    monkeypatch.setenv("MQTT_BROKER", "")
    monkeypatch.setenv("MQTT_TOPIC", "")
    monkeypatch.setenv("MQTT_HOST", "alias-host")
    monkeypatch.setenv("MQTT_PARSED_TOPIC", "alias/parsed")

    cfg = build_config(
        broker=None,
        port=None,
        topic=None,
        username=None,
        password=None,
        min_level=None,
        sensor_type=None,
        sensor_name=None,
    )

    assert cfg.broker == "alias-host"
    assert cfg.topic == "alias/parsed"
