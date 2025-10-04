# IoT Platform Sensor Commands

## Overview
All sensor operations (reading sensors, pin status, system info) are now processed through the unified IoT platform command interface. This provides consistent authentication, response handling, and error management.

## Command Structure

All sensor commands are sent via MQTT with the following structure:

```json
{
  "device_exec": {
    "sensor_command": {
      "action": "<action_name>",
      "sensor_id": "<optional_sensor_id>",
      "params": { ... }
    },
    "response_topic": "device/response/<request_id>"
  },
  "sig": { ... },
  "hash": "..."
}
```

## Supported Actions

### 1. Read Pin Status

**Action**: `read_pin_status`

**Description**: Reads the status of all configured GPIO pins. Auto-creates a `pin_status` sensor if it doesn't exist.

**Command**:
```json
{
  "action": "read_pin_status",
  "sensor_id": "pin_status"  // Optional, defaults to "pin_status"
}
```

**Auto-Creation**: 
- If sensor doesn't exist, automatically creates with default pins: `[0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23]`
- Sensor type: `pin_status`
- Mode: `auto` (auto-detects pin configuration)

**Response**:
```json
{
  "status": "success",
  "action": "read_pin_status",
  "sensor_id": "pin_status",
  "data": {
    "timestamp": 1728000000,
    "total_pins": 15,
    "configured_pins": 15,
    "error_pins": 0,
    "pins": {
      "0": {"value": 1, "mode": "IN", "pull": "PULL_UP"},
      "2": {"value": 1, "mode": "OUT", "pull": null},
      ...
    }
  },
  "timestamp": 1728000000
}
```

### 2. Read System Information

**Action**: `read_system_info`

**Description**: Reads system information including memory, CPU, network, and device details. Auto-creates a `system_info` sensor if it doesn't exist.

**Command**:
```json
{
  "action": "read_system_info",
  "sensor_id": "system_info"  // Optional, defaults to "system_info"
}
```

**Auto-Creation**:
- If sensor doesn't exist, automatically creates
- Sensor type: `system_info`
- No inputs required

**Response**:
```json
{
  "status": "success",
  "action": "read_system_info",
  "sensor_id": "system_info",
  "data": {
    "timestamp": 1728000000,
    "platform": "esp32",
    "memory": {
      "free": 45000,
      "allocated": 85000,
      "total": 130000
    },
    "network": {
      "connected": true,
      "ip": "192.168.1.100",
      "ssid": "MyNetwork"
    },
    "uptime_seconds": 3600,
    "firmware_version": "1.0.0"
  },
  "timestamp": 1728000000
}
```

### 3. Read All Sensors

**Action**: `read_all_sensors`

**Description**: Reads data from all enabled sensors on the device.

**Command**:
```json
{
  "action": "read_all_sensors"
}
```

**Response**:
```json
{
  "status": "success",
  "action": "read_all_sensors",
  "count": 3,
  "sensors": [
    {
      "sensor_id": "temp_sensor",
      "sensor_type": "dht22",
      "status": "success",
      "data": {
        "temperature": 25.5,
        "humidity": 60.2
      },
      "timestamp": 1728000000
    },
    {
      "sensor_id": "pin_status",
      "sensor_type": "pin_status",
      "status": "success",
      "data": { ... },
      "timestamp": 1728000000
    },
    {
      "sensor_id": "system_info",
      "sensor_type": "system_info",
      "status": "success",
      "data": { ... },
      "timestamp": 1728000000
    }
  ],
  "timestamp": 1728000000
}
```

### 4. Read Single Sensor

**Action**: `read_sensor`

**Description**: Reads data from a specific sensor.

**Command**:
```json
{
  "action": "read_sensor",
  "sensor_id": "temp_sensor"
}
```

**Response**:
```json
{
  "status": "success",
  "action": "read_sensor",
  "sensor_id": "temp_sensor",
  "data": {
    "temperature": 25.5,
    "humidity": 60.2
  },
  "timestamp": 1728000000
}
```

### 5. Add Sensor

**Action**: `add_sensor`

**Description**: Adds a new sensor configuration.

**Command**:
```json
{
  "action": "add_sensor",
  "sensor_id": "new_sensor",
  "sensor_type": "dht22",
  "inputs": {
    "pin": 4
  },
  "enabled": true,
  "alias": "Temperature Sensor"
}
```

**Response**:
```json
{
  "status": "success",
  "action": "add_sensor",
  "sensor_id": "new_sensor",
  "message": "Sensor added successfully"
}
```

### 6. Update Sensor

**Action**: `update_sensor`

**Description**: Updates an existing sensor configuration.

**Command**:
```json
{
  "action": "update_sensor",
  "sensor_id": "existing_sensor",
  "updates": {
    "enabled": false,
    "alias": "Updated Sensor Name"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "action": "update_sensor",
  "sensor_id": "existing_sensor",
  "message": "Sensor updated successfully"
}
```

### 7. Remove Sensor

**Action**: `remove_sensor`

**Description**: Removes a sensor configuration.

**Command**:
```json
{
  "action": "remove_sensor",
  "sensor_id": "sensor_to_remove"
}
```

**Response**:
```json
{
  "status": "success",
  "action": "remove_sensor",
  "sensor_id": "sensor_to_remove",
  "message": "Sensor removed successfully"
}
```

### 8. List Sensors

**Action**: `list_sensors`

**Description**: Lists all configured sensors with their status.

**Command**:
```json
{
  "action": "list_sensors"
}
```

**Response**:
```json
{
  "status": "success",
  "action": "list_sensors",
  "count": 3,
  "sensors": [
    {
      "sensor_id": "temp_sensor",
      "sensor_type": "dht22",
      "enabled": true,
      "alias": "Temperature Sensor"
    },
    {
      "sensor_id": "pin_status",
      "sensor_type": "pin_status",
      "enabled": true,
      "alias": "GPIO Pin Status Monitor"
    },
    {
      "sensor_id": "system_info",
      "sensor_type": "system_info",
      "enabled": true,
      "alias": "System Information Monitor"
    }
  ]
}
```

## Auto-Creation Feature

Special sensors are auto-created on first use for convenience:

| Sensor ID | Sensor Type | Triggers | Default Configuration |
|-----------|-------------|----------|----------------------|
| `pin_status` | `pin_status` | `read_pin_status` action | Pins: [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23], Mode: auto |
| `system_info` | `system_info` | `read_system_info` action | No inputs required |

**Benefits**:
- No manual sensor creation needed for common monitoring tasks
- Sensors are automatically persisted to config
- Can be customized after auto-creation via `update_sensor`

## Error Responses

### Sensor Not Found
```json
{
  "status": "error",
  "action": "read_sensor",
  "sensor_id": "unknown_sensor",
  "error": "Sensor 'unknown_sensor' not found"
}
```

### Auto-Creation Failed
```json
{
  "status": "error",
  "action": "read_pin_status",
  "error": "Failed to create pin status sensor"
}
```

### Sensor Manager Not Available
```json
{
  "error": "Sensor manager not available"
}
```

### Read Failed
```json
{
  "status": "error",
  "action": "read_sensor",
  "sensor_id": "temp_sensor",
  "error": "Failed to read sensor: DHT22 read timeout"
}
```

## Implementation Details

### Command Processing Flow

1. **MQTT Message Received** → `on_received()`
2. **Authentication Check** → `auth.validate_expiry()` + `auth.check_auth()`
3. **Sensor Command Detection** → Check for `device_exec.sensor_command`
4. **Command Processing** → `process_sensor_command()`
5. **Action Routing**:
   - `read_pin_status` → Auto-create + read pin status sensor
   - `read_system_info` → Auto-create + read system info sensor
   - `read_all_sensors` → Read all enabled sensors
   - Other actions → Forward to `SensorManager.process_command()`
6. **Response** → Sign and publish to `response_topic`

### Code Location

**File**: `cyberfly_sdk/cyberflySdk.py`

**Method**: `process_sensor_command()` (lines ~290-380)

**Key Logic**:
```python
def process_sensor_command(self, command):
    action = command.get('action')
    
    # Special actions with auto-creation
    if action == 'read_pin_status':
        # Auto-create pin_status sensor if needed
        # Read and return formatted response
    
    elif action == 'read_system_info':
        # Auto-create system_info sensor if needed
        # Read and return formatted response
    
    elif action == 'read_all_sensors':
        # Read all sensors and return
    
    # Standard sensor CRUD operations
    else:
        return self.sensor_manager.process_command(command)
```

## Usage Examples

### Dashboard Monitoring

**Get Pin Status**:
```python
# IoT Platform sends:
{
  "sensor_command": {
    "action": "read_pin_status"
  }
}

# Device responds with pin states for dashboard display
```

**Get System Info**:
```python
# IoT Platform sends:
{
  "sensor_command": {
    "action": "read_system_info"
  }
}

# Device responds with memory, CPU, network info
```

**Get All Sensor Data**:
```python
# IoT Platform sends:
{
  "sensor_command": {
    "action": "read_all_sensors"
  }
}

# Device responds with data from all sensors
```

### Sensor Configuration

**Add Temperature Sensor**:
```python
{
  "sensor_command": {
    "action": "add_sensor",
    "sensor_id": "dht_living_room",
    "sensor_type": "dht22",
    "inputs": {"pin": 4},
    "alias": "Living Room Temperature"
  }
}
```

**Update Sensor**:
```python
{
  "sensor_command": {
    "action": "update_sensor",
    "sensor_id": "dht_living_room",
    "updates": {
      "enabled": false
    }
  }
}
```

## Benefits of Unified Command Interface

1. **Consistent Authentication**: All sensor operations go through the same auth flow
2. **Response Topics**: Automatic response handling with signed payloads
3. **Error Handling**: Consistent error response format
4. **Auto-Creation**: Common sensors created automatically on first use
5. **Persistence**: Auto-created sensors saved to config automatically
6. **Extensibility**: Easy to add new sensor actions without changing protocol

## Migration from Direct Methods

**Before** (Direct method calls):
```python
# Not accessible from IoT platform
client.publish_pin_status()
client.publish_all_sensor_readings()
```

**After** (IoT platform commands):
```python
# Sent from IoT platform via MQTT
{
  "sensor_command": {
    "action": "read_pin_status"  # or "read_all_sensors"
  }
}
```

**Benefits**:
- Remote control from dashboard
- Authenticated and signed
- Automatic response routing
- Consistent with other sensor operations

## Related Documentation

- `SENSOR_COMMANDS.md` - Detailed sensor manager commands
- `cyberfly_sdk/sensors/README.md` - Available sensor types
- `BLE_PROVISION.md` - Device provisioning flow
