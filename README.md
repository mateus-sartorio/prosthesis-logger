# Prothesis MQTT Terminal Logger

A Python terminal app that listens to MQTT messages and renders beautiful logs with:

- Colors by severity (`normal`, `warning`, `error`)
- Timestamps
- Runtime filtering by level, sensor type, and sensor name

## Message format

The MQTT payload must be JSON encoded as string:

```json
{
  "level": "warning",
  "sensor_type": "temperature",
  "sensor_name": "temp-01"
}
```

## Installation

```bash
pip install -e .
```

## Run

```bash
mqtt-log-listener --broker localhost --port 1883 --topic sensors/logs
```

No filters are applied if you omit filter flags.

## Optional startup filters

```bash
mqtt-log-listener \
  --broker localhost \
  --topic sensors/logs \
  --min-level warning \
  --sensor-type temperature \
  --sensor-name temp-01
```

## Runtime controls

- `h` show shortcuts help
- `0` clear minimum level
- `1` set minimum level = normal
- `2` set minimum level = warning
- `3` set minimum level = error
- `t` set sensor type filter (comma separated)
- `n` set sensor name filter (comma separated)
- `c` clear all filters
- `q` quit

## Env fallback

You can use `.env` variables:

- `MQTT_BROKER`
- `MQTT_PORT`
- `MQTT_TOPIC`
- `MQTT_USERNAME`
- `MQTT_PASSWORD`
- `MQTT_MIN_LEVEL`
- `MQTT_SENSOR_TYPE`
- `MQTT_SENSOR_NAME`

CLI values override env values.
