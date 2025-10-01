# IoT Platform Command Reference: read_pin_status

## Overview
The `read_pin_status` command provides instant GPIO pin monitoring capabilities for IoT dashboards. It features auto-creation of pin status sensors, making it the easiest way to get pin state information without manual configuration.

## Command Format

### Basic Usage (Auto-creation)
```json
{
  "sensor_command": {
    "action": "read_pin_status"
  }
}
```

### With Specific Sensor ID
```json
{
  "sensor_command": {
    "action": "read_pin_status",
    "sensor_id": "my_gpio_monitor"
  }
}
```

## Response Format

### Success Response
```json
{
  "status": "success",
  "action": "read_pin_status",
  "sensor_id": "pin_status",
  "timestamp": 1696147200,
  "data": {
    "total_pins": 15,
    "configured_pins": 12,
    "error_pins": 3,
    "timestamp": 1696147200,
    "readable_time": [2024, 10, 1, 12, 30, 0, 0, 274],
    "pins": {
      "pin_0": {
        "pin_number": 0,
        "mode": "input",
        "value": 1,
        "state": "HIGH",
        "status": "success",
        "configured": true
      },
      "pin_2": {
        "pin_number": 2,
        "mode": "output",
        "value": 0,
        "state": "LOW",
        "status": "success",
        "configured": true
      },
      "pin_4": {
        "pin_number": 4,
        "mode": "input",
        "value": 1,
        "state": "HIGH",
        "status": "success",
        "configured": true
      }
    }
  }
}
```

### Error Response (Sensor Not Found)
```json
{
  "status": "error",
  "error": "Pin status sensor 'my_gpio_monitor' not configured",
  "hint": "Add a pin_status sensor to enable pin monitoring"
}
```

### Error Response (Creation Failed)
```json
{
  "status": "error",
  "error": "Failed to create pin status sensor",
  "action": "read_pin_status"
}
```

## Auto-Creation Feature

### Default Configuration
When `read_pin_status` is called without a pre-configured sensor, it automatically creates one with:

- **Sensor ID**: `pin_status` (or custom ID if specified)
- **Sensor Type**: `pin_status`
- **Default Pins**: `[0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23]`
- **Mode**: `auto` (auto-detects input/output)
- **Alias**: "GPIO Pin Status Monitor"

### ESP32 Default Pins
The default pin list covers commonly used ESP32 GPIO pins:
- **Pin 0**: Boot button (input)
- **Pin 2**: Built-in LED (output)
- **Pins 4-5**: General purpose GPIO
- **Pins 12-19**: General purpose GPIO
- **Pins 21-23**: I2C and general purpose
- **Pin 25-27**: DAC and ADC capable (if configured)

### Platform-Specific Notes
- **ESP32**: Pins 0, 2, 4, 5, 12-19, 21-23 (default list)
- **RP2040**: Pins 0-28 (can be configured manually)
- **Other Platforms**: Adjust pin list based on available GPIO

## Use Cases

### 1. Quick GPIO Status Check
No configuration needed - just send the command:
```json
{"sensor_command": {"action": "read_pin_status"}}
```

### 2. Dashboard Real-time Monitoring
Poll every 5-10 seconds for dashboard updates:
```python
# In your dashboard application
import time
while True:
    response = send_command({"sensor_command": {"action": "read_pin_status"}})
    update_dashboard(response['data'])
    time.sleep(5)
```

### 3. Hardware Debugging
Get instant feedback on GPIO states during development:
```json
// Send from IoT platform console
{"sensor_command": {"action": "read_pin_status"}}

// Review all pin states
// Check for unexpected HIGH/LOW values
// Verify pin configurations
```

### 4. System Health Check
Include pin status in system health monitoring:
```python
def system_health_check():
    pin_status = send_command({"sensor_command": {"action": "read_pin_status"}})
    sensor_data = send_command({"sensor_command": {"action": "read_all_sensors"}})
    
    return {
        "pins": pin_status,
        "sensors": sensor_data,
        "timestamp": time.time()
    }
```

## Comparison with Other Commands

### read_pin_status vs read_sensor
```json
// read_pin_status: Auto-creates if needed, pin-specific response format
{"sensor_command": {"action": "read_pin_status"}}

// read_sensor: Requires pre-configured sensor, generic response format
{"sensor_command": {"action": "read_sensor", "sensor_id": "gpio_monitor"}}
```

### read_pin_status vs pin_command
```json
// read_pin_status: Returns structured data in response, synchronous
{"sensor_command": {"action": "read_pin_status"}}

// pin_command: Publishes to MQTT topic, asynchronous
{"pin_command": {"action": "read_status"}}
```

## Integration Examples

### Python IoT Platform Integration
```python
import requests
import json

def get_device_pin_status(device_id, api_endpoint):
    """Get GPIO pin status from IoT device."""
    command = {
        "device_exec": json.dumps({
            "sensor_command": {
                "action": "read_pin_status"
            },
            "expiry_time": int(time.time()) + 300
        })
    }
    
    response = requests.post(f"{api_endpoint}/command/{device_id}", json=command)
    return response.json()

# Usage
pin_data = get_device_pin_status("device_001", "https://iot.example.com")
print(f"Total pins: {pin_data['data']['total_pins']}")
print(f"Configured pins: {pin_data['data']['configured_pins']}")

for pin_key, pin_info in pin_data['data']['pins'].items():
    if pin_info['status'] == 'success':
        print(f"{pin_key}: {pin_info['state']} (mode: {pin_info['mode']})")
```

### JavaScript Dashboard Integration
```javascript
// Fetch pin status
async function fetchPinStatus(deviceId) {
    const command = {
        sensor_command: {
            action: "read_pin_status"
        }
    };
    
    const response = await fetch(`/api/device/${deviceId}/command`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(command)
    });
    
    return await response.json();
}

// Update dashboard
async function updatePinDisplay(deviceId) {
    const pinData = await fetchPinStatus(deviceId);
    
    if (pinData.status === 'success') {
        const pins = pinData.data.pins;
        
        for (const [pinKey, pinInfo] of Object.entries(pins)) {
            if (pinInfo.configured && pinInfo.status === 'success') {
                updatePinIndicator(pinInfo.pin_number, pinInfo.state, pinInfo.mode);
            }
        }
    }
}

// Auto-refresh every 5 seconds
setInterval(() => updatePinDisplay('device_001'), 5000);
```

### Node-RED Integration
```json
[
    {
        "id": "read_pin_status",
        "type": "function",
        "name": "Read Pin Status",
        "func": "msg.payload = {\n    sensor_command: {\n        action: \"read_pin_status\"\n    }\n};\nreturn msg;",
        "outputs": 1
    },
    {
        "id": "process_response",
        "type": "function",
        "name": "Process Pin Data",
        "func": "if (msg.payload.status === 'success') {\n    const pins = msg.payload.data.pins;\n    const highPins = [];\n    const lowPins = [];\n    \n    for (const [key, info] of Object.entries(pins)) {\n        if (info.configured && info.status === 'success') {\n            if (info.value === 1) {\n                highPins.push(info.pin_number);\n            } else {\n                lowPins.push(info.pin_number);\n            }\n        }\n    }\n    \n    msg.payload = {\n        high: highPins,\n        low: lowPins,\n        total: msg.payload.data.total_pins,\n        configured: msg.payload.data.configured_pins\n    };\n}\nreturn msg;",
        "outputs": 1
    }
]
```

## Best Practices

### 1. Polling Frequency
- **Development**: 1-5 seconds for real-time debugging
- **Production**: 10-30 seconds for monitoring
- **Background**: 60+ seconds for status checks

### 2. Error Handling
```python
def safe_read_pin_status(client):
    """Safely read pin status with error handling."""
    try:
        response = client.send_command({
            "sensor_command": {"action": "read_pin_status"}
        })
        
        if response.get('status') == 'success':
            return response['data']
        else:
            print(f"Error: {response.get('error')}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None
```

### 3. Custom Pin Configuration
For specific needs, pre-configure the pin sensor:
```python
# Pre-configure specific pins instead of using defaults
client.add_sensor(
    sensor_id="custom_pins",
    sensor_type="pin_status",
    inputs={
        "pins": [2, 4, 16, 17, 25, 26, 27],  # Custom pin list
        "mode": "auto"
    },
    alias="Custom GPIO Monitor"
)

# Then use with specific sensor_id
command = {
    "sensor_command": {
        "action": "read_pin_status",
        "sensor_id": "custom_pins"
    }
}
```

### 4. Response Caching
Cache responses to reduce device load:
```python
class PinStatusCache:
    def __init__(self, ttl=10):
        self.cache = None
        self.cache_time = 0
        self.ttl = ttl
    
    def get(self, client):
        now = time.time()
        if self.cache is None or (now - self.cache_time) > self.ttl:
            self.cache = client.send_command({
                "sensor_command": {"action": "read_pin_status"}
            })
            self.cache_time = now
        return self.cache
```

## Troubleshooting

### Issue: Auto-creation fails
**Cause**: Insufficient memory or pin conflicts  
**Solution**: Pre-configure sensor with fewer pins

### Issue: Some pins show errors
**Cause**: Pins in use by other peripherals (I2C, SPI, etc.)  
**Solution**: Remove conflicting pins from configuration

### Issue: Unexpected pin states
**Cause**: External hardware, pull resistors, or previous configuration  
**Solution**: Verify hardware connections and use appropriate pull_mode

### Issue: Slow response times
**Cause**: Too many pins configured  
**Solution**: Reduce pin count or increase polling interval

## Related Commands

- `read_sensor` - Generic sensor reading (requires pre-configuration)
- `read_all_sensors` - Read all configured sensors
- `pin_command: read_status` - Publish pin status to MQTT topic
- `pin_command: dashboard_update` - Publish complete dashboard data

## See Also

- **Quick Start Guide**: `PIN_STATUS_QUICK_START.md`
- **Implementation Details**: `PIN_STATUS_IMPLEMENTATION.md`
- **Setup Documentation**: `NO_CODE_SETUP.md`
- **Example Code**: `examples/pin_status_dashboard.py`