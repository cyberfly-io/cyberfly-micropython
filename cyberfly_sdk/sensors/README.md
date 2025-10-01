# CyberFly MicroPython Sensor System

This sensor management system provides a unified interface for handling sensors in MicroPython IoT devices, similar to the cyberfly-python-client-sdk.

## Features

- **Sensor Management**: Add, remove, enable/disable sensors
- **Unified Reading Interface**: Read individual sensors or all sensors at once  
- **Command Processing**: Handle sensor commands from IoT platform
- **Configuration Persistence**: Save/load sensor configurations
- **Output Control**: Execute actions on output sensors (LEDs, relays, etc.)
- **Memory Efficient**: Optimized for MicroPython constraints

## Supported Sensor Types

### Built-in Sensors
- `temp_internal` - Internal temperature sensor (ESP32/RP2040)
- `digital_in` - Digital input (buttons, switches)
- `digital_out` - Digital output (LEDs, relays)
- `analog_in` - Analog input (potentiometers, light sensors)
- `system_info` - System information (memory, uptime)
- `mock_dht` - Mock DHT sensor for testing

### Adding Custom Sensors
Create new sensor classes in `sensors/base_sensors.py` inheriting from `BaseSensor`:

```python
class CustomSensor(BaseSensor):
    def __init__(self, inputs):
        super().__init__(inputs)
        # Initialize hardware
        
    def read(self):
        # Return sensor data as dict
        return {"value": 123}
```

## Usage

### Basic Setup

```python
from cyberflySdk import CyberflyClient

# Initialize client (normally done via BLE provisioning)
client = CyberflyClient(device_id="my-device", ...)

# Add sensors
client.add_sensor("temp1", "temp_internal", {}, alias="CPU Temperature")
client.add_sensor("led1", "digital_out", {"pin_no": 2}, alias="Status LED")
client.add_sensor("button1", "digital_in", {"pin_no": 0}, alias="Boot Button")

# Read sensors
reading = client.read_sensor("temp1")
all_readings = client.read_all_sensors()

# Control outputs
client.execute_sensor_action("led1", "toggle")
client.execute_sensor_action("led1", "set_output", {"value": 1})
```

### IoT Platform Commands

The system automatically handles these command formats from the IoT platform:

```json
// Read specific sensor
{"sensor_command": {"action": "read", "sensor_id": "temp1"}}

// Read all sensors  
{"sensor_command": {"action": "read"}}

// Get sensor status
{"sensor_command": {"action": "status"}}

// Execute action on output sensor
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "led1", 
    "params": {
      "execute_action": "toggle"
    }
  }
}
```

### Configuration Persistence

Sensor configurations are automatically saved to the device config file and restored on boot:

```json
{
  "device_id": "my-device",
  "sensors": [
    {
      "sensor_id": "temp1",
      "sensor_type": "temp_internal", 
      "inputs": {},
      "enabled": true,
      "alias": "CPU Temperature"
    }
  ]
}
```

## Hardware Setup Examples

### ESP32 Digital I/O
```python
# Button on GPIO 0 with pull-up
client.add_sensor("button", "digital_in", {"pin_no": 0, "pull_up": True})

# LED on GPIO 2  
client.add_sensor("led", "digital_out", {"pin_no": 2, "initial_value": 0})
```

### ESP32 Analog Input
```python
# Potentiometer on GPIO 36
client.add_sensor("pot", "analog_in", {"pin_no": 36})
```

### RP2040 Setup
```python
# Button on GPIO 0
client.add_sensor("button", "digital_in", {"pin_no": 0})

# LED on GPIO 25 (built-in LED)
client.add_sensor("led", "digital_out", {"pin_no": 25})
```

## Memory Considerations

- Sensors use `__slots__` for memory efficiency
- Automatic garbage collection in main loop
- Lazy loading of sensor implementations
- Optional caching of sensor readings

## Error Handling

All sensor operations return structured error information:

```python
reading = client.read_sensor("invalid_sensor")
# Returns: {"status": "error", "error": "Sensor not found", ...}
```

## Integration with Existing Modules

The sensor system works alongside the existing module system. Both can be used together for maximum flexibility.