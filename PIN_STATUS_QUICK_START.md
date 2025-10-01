# Quick Start: GPIO Pin Status Dashboard

## Basic Setup (5 Minutes)

### 1. Add Pin Status Sensor
```python
from cyberflySdk import CyberflyClient

client = CyberflyClient(
    device_id="my_device",
    key_pair={"publicKey": "...", "secretKey": "..."},
    ssid="WiFi_SSID",
    wifi_password="password",
    network_id="testnet04"
)

# Monitor common GPIO pins
client.add_sensor(
    sensor_id="gpio_status",
    sensor_type="pin_status",
    inputs={
        "pins": [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23],
        "mode": "auto"  # Auto-detect input/output
    },
    alias="GPIO Monitor"
)
```

### 2. Publish to Dashboard
```python
# Manual publish
client.publish_pin_status()

# Or publish complete dashboard
client.publish_dashboard_summary()

# Or in main loop
while True:
    client.check_msg()
    client.publish_pin_status()  # Every iteration
    time.sleep(10)  # Every 10 seconds
```

## Configuration Options

### Monitor Single Pin
```python
client.add_sensor(
    sensor_id="led_pin",
    sensor_type="pin_status",
    inputs={"pin_no": 2},  # Single pin
    alias="Built-in LED"
)
```

### Input Pins with Pull-up
```python
client.add_sensor(
    sensor_id="buttons",
    sensor_type="pin_status",
    inputs={
        "pins": [0, 35, 36],
        "mode": "input",
        "pull_mode": "up"  # Enable pull-up resistors
    },
    alias="Button Inputs"
)
```

### Output Pins Only
```python
client.add_sensor(
    sensor_id="outputs",
    sensor_type="pin_status",
    inputs={
        "pins": [2, 4, 16, 17],
        "mode": "output"  # Only output pins
    },
    alias="Output Controls"
)
```

## Dashboard Commands

### From IoT Platform
```json
## Dashboard Commands

### From IoT Platform
```json
// Read pin status (auto-creates sensor with default pins if needed)
{"sensor_command": {"action": "read_pin_status"}}

// Read specific pin status sensor
{"sensor_command": {"action": "read_pin_status", "sensor_id": "gpio_monitor"}}

// Traditional sensor read (requires sensor to be pre-configured)
{"sensor_command": {"action": "read_sensor", "sensor_id": "gpio_status"}}

// Publish to dashboard topic
{"pin_command": {"action": "read_status"}}

// Complete dashboard update
{"pin_command": {"action": "dashboard_update"}}
```

### Auto-Creation Feature
The `read_pin_status` command automatically creates a pin status sensor if one doesn't exist:
- **Default Sensor ID**: `pin_status`
- **Default Pins**: [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23]
- **Default Mode**: `auto` (auto-detect input/output)
- **No Configuration Needed**: Just send the command!
```

## Data Format

### Pin Status Response
```json
{
    "total_pins": 15,
    "configured_pins": 12,
    "error_pins": 3,
    "timestamp": 1696147200,
    "pins": {
        "pin_0": {
            "pin_number": 0,
            "mode": "input",
            "value": 1,
            "state": "HIGH",
            "status": "success"
        },
        "pin_2": {
            "pin_number": 2,
            "mode": "output",
            "value": 0,
            "state": "LOW",
            "status": "success"
        }
    }
}
```

## Common Use Cases

### ESP32 Development Board
```python
# Monitor common ESP32 pins
pins = [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33]
client.add_sensor(
    sensor_id="esp32_gpio",
    sensor_type="pin_status",
    inputs={"pins": pins, "mode": "auto"},
    alias="ESP32 GPIO"
)
```

### Raspberry Pi Pico
```python
# Monitor Pico GPIO pins
pins = list(range(0, 29))  # GP0-GP28
client.add_sensor(
    sensor_id="pico_gpio",
    sensor_type="pin_status",
    inputs={"pins": pins, "mode": "auto"},
    alias="Pico GPIO"
)
```

### LED Status Monitoring
```python
# Monitor LED outputs
client.add_sensor(
    sensor_id="leds",
    sensor_type="pin_status",
    inputs={
        "pins": [2, 4, 16],  # LED pins
        "mode": "output"
    },
    alias="LED Status"
)
```

### Button Monitoring
```python
# Monitor button inputs
client.add_sensor(
    sensor_id="buttons",
    sensor_type="pin_status",
    inputs={
        "pins": [0, 35],  # Boot button + custom button
        "mode": "input",
        "pull_mode": "up"
    },
    alias="Button Status"
)
```

## Auto-Publish Pattern

```python
import time

# Main loop with auto-publish
last_pin_publish = time.time()
pin_interval = 10  # seconds

while True:
    client.check_msg()
    
    if time.time() - last_pin_publish >= pin_interval:
        client.publish_pin_status()
        last_pin_publish = time.time()
    
    time.sleep(0.1)
```

## Troubleshooting

### Pin Not Available
```python
# Check pin status in reading
reading = client.read_sensor("gpio_status")
for pin_key, pin_info in reading['data']['pins'].items():
    if 'error' in pin_info:
        print(f"{pin_key}: {pin_info['error']}")
```

### Configuration Errors
```python
# Check configured vs error pins
reading = client.read_sensor("gpio_status")
print(f"Configured: {reading['data']['configured_pins']}")
print(f"Errors: {reading['data']['error_pins']}")
```

## BLE Provisioning

Pin status sensor can be configured via BLE:
```json
{
    "config_type": "sensors",
    "sensors": [
        {
            "sensor_id": "gpio_monitor",
            "sensor_type": "pin_status",
            "inputs": {
                "pins": [0, 2, 4, 5, 12, 13, 14, 15],
                "mode": "auto"
            },
            "enabled": true,
            "alias": "GPIO Status"
        }
    ]
}
```

## Tips

1. **Start Small**: Begin with 5-10 pins, expand as needed
2. **Auto Mode**: Use "auto" mode for initial testing
3. **Pull Resistors**: Use pull-up for buttons, none for outputs
4. **Publish Rate**: 10-30 seconds is good for monitoring
5. **Error Handling**: Check error_pins count to identify issues

## See Also
- Full example: `examples/pin_status_dashboard.py`
- Documentation: `NO_CODE_SETUP.md`
- Implementation details: `PIN_STATUS_IMPLEMENTATION.md`