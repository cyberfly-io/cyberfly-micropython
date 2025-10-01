# CyberFly MicroPython No-Code IoT Device

A complete no-code solution for creating IoT devices with MicroPython. Configure everything via mobile app using BLE - no programming required!

## 🚀 Quick Start

1. **Flash the firmware** to your ESP32/RP2040 device
2. **Copy** `no_code_iot_device.py` as `main.py` to your device
3. **Power on** - device enters BLE setup mode automatically
4. **Use mobile app** to configure WiFi, credentials, and sensors
5. **Done!** Device automatically starts and handles IoT commands

## 📱 BLE Setup Process

### Step 1: Device Discovery
- Device advertises as `CYBERFLY-SETUP`
- Connect to BLE service UUID: `6e400001-b5a3-f393-e0a9-e50e24dcca9e`

### Step 2: Device Configuration
Send device configuration JSON:
```json
{
  "device_id": "my-iot-device",
  "ssid": "MyWiFi",
  "wifi_password": "password123", 
  "network_id": "testnet04",
  "publicKey": "your-public-key",
  "secretKey": "your-secret-key"
}
```

**Response:** Device enters sensor setup mode and returns available sensors:
```json
{
  "status": "sensor_ready",
  "available_sensors": [
    {
      "type": "temp_internal",
      "name": "Internal Temperature", 
      "description": "Built-in temperature sensor",
      "inputs": []
    },
    {
      "type": "digital_out",
      "name": "Digital Output",
      "description": "LED or relay output",
      "inputs": [{"name": "pin_no", "type": "number", "required": true}]
    }
  ],
  "detected_sensors": [
    {
      "sensor_id": "internal_temp",
      "sensor_type": "temp_internal",
      "alias": "Internal Temperature"
    },
    {
      "sensor_id": "boot_button", 
      "sensor_type": "digital_in",
      "inputs": {"pin_no": 0, "pull_up": true},
      "alias": "Boot Button"
    }
  ],
  "hardware_pins": {
    "esp32": [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39],
    "rp2040": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
  }
}
```

### Step 3: Sensor Configuration
Send sensor configuration JSON:
```json
{
  "config_type": "sensors",
  "sensors": [
    {
      "sensor_id": "temp1",
      "sensor_type": "temp_internal",
      "enabled": true,
      "alias": "CPU Temperature"
    },
    {
      "sensor_id": "led1", 
      "sensor_type": "digital_out",
      "inputs": {"pin_no": 2, "initial_value": 0},
      "enabled": true,
      "alias": "Status LED"
    },
    {
      "sensor_id": "button1",
      "sensor_type": "digital_in", 
      "inputs": {"pin_no": 0, "pull_up": true},
      "enabled": true,
      "alias": "Boot Button"
    }
  ]
}
```

**Response:** `{"status": "sensor_saved"}` - Device automatically restarts

## 🔧 Available Sensor Types

### Always Available
- **`temp_internal`** - Internal temperature sensor (ESP32/RP2040)
- **`system_info`** - Memory usage and uptime monitoring

### Basic GPIO Sensors  
- **`digital_in`** - Basic digital input
  - Required: `pin_no` (GPIO number)
  - Optional: `pull_up` (true/false, default: true)
  
- **`digital_out`** - Basic digital output
  - Required: `pin_no` (GPIO number) 
  - Optional: `initial_value` (0/1, default: 0)
  
- **`analog_in`** - Basic analog input
  - Required: `pin_no` (ADC-capable GPIO number)

### Environmental Sensors
- **`dht22`** - Temperature and humidity sensor
  - Required: `pin_no` (GPIO number)
  - Returns: temperature_c, temperature_f, humidity_percent, heat_index_c

- **`ultrasonic`** - Distance measurement (HC-SR04)
  - Required: `trigger_pin`, `echo_pin` (GPIO numbers)
  - Returns: distance_cm, distance_inch, pulse_time_us

- **`photoresistor`** - Light level detection (LDR)
  - Required: `pin_no` (ADC-capable GPIO)
  - Optional: `dark_threshold`, `bright_threshold`
  - Returns: light_percent, raw_value, condition

### Motion & User Interface
- **`pir_motion`** - Motion detection sensor
  - Required: `pin_no` (GPIO number)
  - Returns: motion_detected, raw_value, time_since_motion

- **`button`** - Enhanced button with debouncing
  - Required: `pin_no` (GPIO number)
  - Optional: `pull_up` (true/false), `debounce_ms` (0-1000)
  - Returns: pressed, press_count, raw_value, time_since_change

- **`rotary_encoder`** - Position/rotation tracking
  - Required: `clk_pin`, `dt_pin` (GPIO numbers)
  - Returns: position, clk_state, dt_state

### Analog Sensors with Calibration
- **`potentiometer`** - Variable resistor with scaling
  - Required: `pin_no` (ADC-capable GPIO)
  - Optional: `min_value`, `max_value`, `units`
  - Returns: value, percent, raw_value, units

- **`voltage`** - Voltage measurement with calibration
  - Required: `pin_no` (ADC-capable GPIO)
  - Optional: `reference_voltage` (default: 3.3), `voltage_divider_ratio` (default: 1.0)
  - Returns: voltage, measured_voltage, raw_value, voltage_percent

### Legacy Aliases (for compatibility)
- **`light_sensor`** → `photoresistor`
- **`distance_sensor`** → `ultrasonic` 
- **`motion_sensor`** → `pir_motion`

### Auto-Detected Sensors
The system automatically detects and suggests:
- **Boot button** (GPIO 0 on most boards)
- **Built-in LED** (GPIO 2 on ESP32, GPIO 25 on RP2040)

## 📊 IoT Platform Integration

Once configured, the device automatically handles these commands from the IoT platform:

### Read Sensor Data
```json
// Read all sensors
{"sensor_command": {"action": "read"}}

// Read specific sensor
{"sensor_command": {"action": "read", "sensor_id": "temp1"}}
```

### Control Output Devices
```json
// Toggle LED
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "led1", 
    "params": {"execute_action": "toggle"}
  }
}

// Set LED state
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "led1",
    "params": {
      "execute_action": "set_output",
      "execute_params": {"value": 1}
    }
  }
}
```

### Get Device Status
```json
{"sensor_command": {"action": "status"}}
```

## 🔄 Automatic Features

- **Auto-publish**: Sensor data published every 60 seconds
- **Auto-reconnect**: Handles WiFi/MQTT disconnections  
- **Auto-recovery**: Restarts on critical errors
- **Memory management**: Automatic garbage collection
- **Command processing**: All sensor commands handled automatically

## 🛠️ Hardware Setup Examples

### ESP32 Basic Setup
```
• Internal temp sensor (always available)
• Boot button on GPIO 0 (auto-detected)  
• Status LED on GPIO 2 (auto-detected)
• Additional sensors on available GPIOs
```

### RP2040 Basic Setup  
```
• Internal temp sensor (always available)
• Boot button on GPIO 0 (auto-detected)
• Built-in LED on GPIO 25 (auto-detected)
• Additional sensors on available GPIOs
```

### Smart Home Sensor Configuration
```json
{
  "config_type": "sensors",
  "sensors": [
    {
      "sensor_id": "environment",
      "sensor_type": "dht22",
      "inputs": {"pin_no": 4},
      "enabled": true,
      "alias": "Temperature & Humidity"
    },
    {
      "sensor_id": "motion_security",
      "sensor_type": "pir_motion",
      "inputs": {"pin_no": 12},
      "enabled": true,
      "alias": "Motion Detector"
    },
    {
      "sensor_id": "ambient_light",
      "sensor_type": "photoresistor",
      "inputs": {"pin_no": 36},
      "enabled": true,
      "alias": "Light Sensor"
    },
    {
      "sensor_id": "distance_parking",
      "sensor_type": "ultrasonic",
      "inputs": {"trigger_pin": 5, "echo_pin": 18},
      "enabled": true,
      "alias": "Parking Sensor"
    }
  ]
}
```

### Industrial Monitoring Configuration
```json
{
  "config_type": "sensors",
  "sensors": [
    {
      "sensor_id": "machine_voltage",
      "sensor_type": "voltage",
      "inputs": {"pin_no": 35, "voltage_divider_ratio": 5.0},
      "enabled": true,
      "alias": "Machine Voltage"
    },
    {
      "sensor_id": "control_knob",
      "sensor_type": "potentiometer",
      "inputs": {"pin_no": 39, "min_value": 0, "max_value": 1000, "units": "rpm"},
      "enabled": true,
      "alias": "Speed Control"
    },
    {
      "sensor_id": "emergency_stop",
      "sensor_type": "button",
      "inputs": {"pin_no": 0, "pull_up": true, "debounce_ms": 100},
      "enabled": true,
      "alias": "Emergency Stop"
    }
  ]
}
```

### Garden Monitoring System
```json
{
  "config_type": "sensors",
  "sensors": [
    {
      "sensor_id": "soil_moisture",
      "sensor_type": "analog_in",
      "inputs": {"pin_no": 32},
      "enabled": true,
      "alias": "Soil Moisture"
    },
    {
      "sensor_id": "garden_temp_humid",
      "sensor_type": "dht22",
      "inputs": {"pin_no": 4},
      "enabled": true,
      "alias": "Garden Climate"
    },
    {
      "sensor_id": "sunlight_level",
      "sensor_type": "photoresistor",
      "inputs": {"pin_no": 36},
      "enabled": true,
      "alias": "Sunlight Level"
    },
    {
      "sensor_id": "water_pump",
      "sensor_type": "digital_out",
      "inputs": {"pin_no": 13},
      "enabled": true,
      "alias": "Water Pump"
    }
  ]
}
```

### GPIO Pin Reference
- **ESP32 ADC Pins**: 32, 33, 34, 35, 36, 39 (for analog sensors)
- **ESP32 Digital Pins**: 0, 2, 4, 5, 12-19, 21-23, 25-27
- **RP2040 ADC Pins**: 26, 27, 28 (for analog sensors)  
- **RP2040 Digital Pins**: 0-28 (all pins can be digital)

## 🔒 Security

- All communications use signed JSON with device keypairs
- BLE provisioning automatically times out after 5 minutes
- Device credentials stored securely in flash memory
- Command authentication via platform keys

## 🚨 Troubleshooting

### Device Not Advertising
- Hold boot button for 3+ seconds to force setup mode
- Check power supply and firmware flash
- Verify BLE is enabled in firmware build

### Setup Timeout
- Default 5 minute timeout for BLE provisioning
- Device will restart and try again
- Check mobile app BLE permissions

### Sensor Not Working
- Verify GPIO pin numbers for your board
- Check sensor wiring and power
- Use IoT platform status command to diagnose

### WiFi Connection Issues
- Verify SSID and password during setup
- Check 2.4GHz network (5GHz not supported)
- Device will retry connection automatically

## 📱 Mobile App Requirements

The mobile app should implement:
1. **BLE scanning** for `CYBERFLY-SETUP` devices
2. **Two-step configuration** (device + sensors)  
3. **Sensor type selection** with input validation
4. **GPIO pin picker** based on board type
5. **Setup progress** indication
6. **Error handling** with user feedback

## 🔗 Integration

This no-code solution works with:
- **CyberFly IoT Platform** - Full sensor management UI
- **Custom platforms** - Standard MQTT/JSON protocol
- **Mobile apps** - BLE provisioning protocol  
- **Web dashboards** - Real-time sensor data
- **Automation systems** - Command/response interface

Start building IoT devices without writing any code!