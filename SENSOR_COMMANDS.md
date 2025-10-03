# Sensor Command Support

## Overview
The device firmware now supports dynamic sensor configuration commands received from the IoT platform. The `SensorManager` handles persistence and lifecycle management, while `CyberflyClient.process_sensor_command()` forwards validated commands received over MQTT.

## Command Reference

All commands must include an `action` field. Successful responses return `{ "status": "success", ... }`. Errors return `{ "status": "error", "error": "message" }`.

### Add Sensor
```json
{
  "action": "add_sensor",
  "config": {
    "sensor_id": "soil_temp",
    "sensor_type": "analog_input",
    "inputs": { "pin": 34, "scale": 0.1 },
    "enabled": true,
    "alias": "Soil Temperature"
  }
}
```
- Creates the sensor if it does not exist.
- Replaces existing configuration if the `sensor_id` already exists.

### Update Sensor
```json
{
  "action": "update_sensor",
  "config": {
    "sensor_id": "soil_temp",
    "enabled": false,
    "alias": "Soil Temp (disabled)"
  }
}
```
- Merges updates onto the current configuration (`inputs`, `enabled`, `alias`, `sensor_type`).

### Remove Sensor
```json
{
  "action": "remove_sensor",
  "sensor_id": "soil_temp"
}
```
- Deletes both the runtime instance and its persisted configuration.

### List Sensors
```json
{
  "action": "list_sensors"
}
```
- Returns all persisted configurations with `sensors` (array) and `count` keys.

### Existing Commands
The previous commands remain available:
- `read_sensor`
- `read_all_sensors`
- `read_pin_status`
- `enable_sensor`
- `disable_sensor`

## Persistence
- The manager persists configurations via `sensor_configs.json` by default.
- When `CyberflyClient` is used, a config save hook mirrors the data into the main device configuration stored by `config.save_config`.
- Configurations are reloaded on boot from either the config hook or the JSON file.

## Notes & Assumptions
- Sensor type strings must match entries in the sensor factory (`_create_sensor`). Unknown types return an error.
- `inputs` can be any dictionary understood by the concrete sensor implementation.
- Commands are processed only after authentication checks in `CyberflyClient.on_received` succeed.
- Currently there is no bulk transaction command; multiple sensors should be sent as individual commands.
