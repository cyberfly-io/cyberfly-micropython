"""
Configuration Validator for CyberFly MicroPython
Validates BLE setup configurations before sending to device
"""

import json
import sys

class ConfigValidator:
    """Validates device and sensor configurations"""
    
    # Available sensor types with their requirements
    SENSOR_TYPES = {
        # Always available sensors
        'temp_internal': {
            'name': 'Internal Temperature',
            'description': 'Built-in temperature sensor',
            'required_inputs': [],
            'optional_inputs': []
        },
        'system_info': {
            'name': 'System Information',
            'description': 'Memory usage and uptime',
            'required_inputs': [],
            'optional_inputs': []
        },
        
        # Basic GPIO sensors
        'digital_in': {
            'name': 'Digital Input',
            'description': 'Button, switch, or digital sensor',
            'required_inputs': ['pin_no'],
            'optional_inputs': ['pull_up']
        },
        'digital_out': {
            'name': 'Digital Output', 
            'description': 'LED, relay, or digital actuator',
            'required_inputs': ['pin_no'],
            'optional_inputs': ['initial_value', 'active_high']
        },
        'analog_in': {
            'name': 'Analog Input',
            'description': 'Basic analog sensor',
            'required_inputs': ['pin_no'],
            'optional_inputs': []
        },
        
        # Environmental sensors
        'dht11': {
            'name': 'DHT11 Sensor',
            'description': 'Temperature and humidity (basic)',
            'required_inputs': ['pin_no'],
            'optional_inputs': []
        },
        'dht22': {
            'name': 'DHT22 Sensor',
            'description': 'Temperature and humidity (precise)',
            'required_inputs': ['pin_no'],
            'optional_inputs': []
        },
        'ds18b20': {
            'name': 'DS18B20 Temperature',
            'description': 'Waterproof 1-Wire temperature probe',
            'required_inputs': ['pin_no'],
            'optional_inputs': ['sensor_id', 'unit']
        },
        
        # Motion and detection sensors
        'pir': {
            'name': 'PIR Motion',
            'description': 'Passive infrared motion detection',
            'required_inputs': ['pin_no'],
            'optional_inputs': []
        },
        'pir_motion': {
            'name': 'PIR Motion Sensor',
            'description': 'Passive infrared motion detection',
            'required_inputs': ['pin_no'],
            'optional_inputs': []
        },
        'din': {
            'name': 'Digital Input Generic',
            'description': 'Generic digital input',
            'required_inputs': ['pin_no'],
            'optional_inputs': []
        },
        'hall': {
            'name': 'Hall Effect',
            'description': 'Magnetic field detection',
            'required_inputs': ['pin_no'],
            'optional_inputs': []
        },
        'water': {
            'name': 'Water Sensor',
            'description': 'Water/rain detection',
            'required_inputs': ['pin_no'],
            'optional_inputs': []
        },
        'dout': {
            'name': 'Digital Output Generic',
            'description': 'Generic digital output',
            'required_inputs': ['pin_no'],
            'optional_inputs': ['active_high', 'initial_value']
        },
        
        # Distance sensors
        'ultrasonic': {
            'name': 'Ultrasonic Distance',
            'description': 'HC-SR04 distance measurement',
            'required_inputs': ['trigger_pin', 'echo_pin'],
            'optional_inputs': []
        },
        'hc_sr04': {
            'name': 'HC-SR04 Enhanced',
            'description': 'Enhanced ultrasonic with thresholds',
            'required_inputs': ['trigger_pin', 'echo_pin'],
            'optional_inputs': ['max_distance', 'threshold_distance']
        },
        
        # Analog sensors with calibration
        'photoresistor': {
            'name': 'Light Sensor (LDR)',
            'description': 'Photoresistor light detection',
            'required_inputs': ['pin_no'],
            'optional_inputs': ['dark_threshold', 'bright_threshold']
        },
        'potentiometer': {
            'name': 'Potentiometer',
            'description': 'Variable resistor with calibration',
            'required_inputs': ['pin_no'],
            'optional_inputs': ['min_value', 'max_value', 'units']
        },
        'voltage': {
            'name': 'Voltage Sensor',
            'description': 'Voltage measurement with calibration',
            'required_inputs': ['pin_no'],
            'optional_inputs': ['reference_voltage', 'voltage_divider_ratio']
        },
        
        # User interface sensors
        'button': {
            'name': 'Enhanced Button',
            'description': 'Button with press counting and debouncing',
            'required_inputs': ['pin_no'],
            'optional_inputs': ['pull_up', 'debounce_ms']
        },
        'rotary_encoder': {
            'name': 'Rotary Encoder',
            'description': 'Position/rotation tracking',
            'required_inputs': ['clk_pin', 'dt_pin'],
            'optional_inputs': []
        },
        
        # I2C Environmental sensors
        'bmp280': {
            'name': 'BMP280',
            'description': 'Pressure, temperature, altitude',
            'required_inputs': [],
            'optional_inputs': ['address', 'sea_level_pressure', 'i2c_bus']
        },
        'bme280': {
            'name': 'BME280',
            'description': 'Pressure, temperature, humidity',
            'required_inputs': [],
            'optional_inputs': ['address', 'sea_level_pressure', 'i2c_bus']
        },
        'bme680': {
            'name': 'BME680',
            'description': 'Environmental sensor with gas',
            'required_inputs': [],
            'optional_inputs': ['address', 'sea_level_pressure', 'i2c_bus']
        },
        'sht31d': {
            'name': 'SHT31-D',
            'description': 'Precision temperature and humidity',
            'required_inputs': [],
            'optional_inputs': ['address', 'heater', 'i2c_bus']
        },
        
        # I2C Light and color sensors
        'bh1750': {
            'name': 'BH1750',
            'description': 'Ambient light sensor (lux)',
            'required_inputs': [],
            'optional_inputs': ['address', 'i2c_bus']
        },
        'tcs34725': {
            'name': 'TCS34725',
            'description': 'RGB color sensor',
            'required_inputs': [],
            'optional_inputs': ['address', 'gain', 'integration_time', 'i2c_bus']
        },
        
        # I2C Air quality sensors
        'ccs811': {
            'name': 'CCS811',
            'description': 'Air quality (CO2, TVOC)',
            'required_inputs': [],
            'optional_inputs': ['address', 'temperature_offset', 'baseline', 'i2c_bus']
        },
        
        # I2C Distance sensors
        'vl53l0x': {
            'name': 'VL53L0X',
            'description': 'Time-of-flight distance',
            'required_inputs': [],
            'optional_inputs': ['address', 'measurement_timing_budget', 'signal_rate_limit', 'i2c_bus']
        },
        
        # I2C Advanced sensors
        'ads1115': {
            'name': 'ADS1115',
            'description': '4-channel 16-bit ADC',
            'required_inputs': [],
            'optional_inputs': ['address', 'channel', 'gain', 'data_rate', 'i2c_bus']
        },
        'mpu6050': {
            'name': 'MPU6050',
            'description': '6-axis accelerometer + gyroscope',
            'required_inputs': [],
            'optional_inputs': ['address', 'i2c_bus']
        },
        
        # Display modules
        'lcd1602': {
            'name': 'LCD 16x2',
            'description': 'I2C LCD display',
            'required_inputs': [],
            'optional_inputs': ['address', 'columns', 'rows', 'text', 'auto_linebreaks', 'i2c_bus']
        },
        'ht16k33': {
            'name': 'HT16K33',
            'description': '4-digit 7-segment display',
            'required_inputs': [],
            'optional_inputs': ['address', 'text', 'align_right', 'i2c_bus']
        },
        
        # Legacy aliases
        'light_sensor': {
            'name': 'Light Sensor (Legacy)',
            'description': 'Alias for photoresistor',
            'required_inputs': ['pin_no'],
            'optional_inputs': ['dark_threshold', 'bright_threshold']
        },
        'distance_sensor': {
            'name': 'Distance Sensor (Legacy)',
            'description': 'Alias for ultrasonic',
            'required_inputs': ['trigger_pin', 'echo_pin'],
            'optional_inputs': []
        },
        'motion_sensor': {
            'name': 'Motion Sensor (Legacy)',
            'description': 'Alias for pir_motion',
            'required_inputs': ['pin_no'],
            'optional_inputs': []
        }
    }
    
    # Valid GPIO pins by platform
    GPIO_PINS = {
        'esp32': [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39],
        'rp2040': list(range(29))  # GPIO 0-28
    }
    
    # ADC-capable pins
    ADC_PINS = {
        'esp32': [32, 33, 34, 35, 36, 39],
        'rp2040': [26, 27, 28]
    }
    
    def validate_device_config(self, config):
        """Validate device configuration JSON"""
        errors = []
        
        # Required fields
        required_fields = ['device_id', 'ssid', 'wifi_password', 'network_id', 'publicKey', 'secretKey']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
            elif not config[field] or not isinstance(config[field], str):
                errors.append(f"Field '{field}' must be a non-empty string")
        
        # Device ID validation
        if 'device_id' in config:
            device_id = config['device_id']
            if len(device_id) < 3 or len(device_id) > 50:
                errors.append("Device ID must be 3-50 characters long")
            if not device_id.replace('-', '').replace('_', '').isalnum():
                errors.append("Device ID can only contain letters, numbers, hyphens, and underscores")
        
        # Network ID validation
        if 'network_id' in config:
            valid_networks = ['testnet04', 'mainnet01']
            if config['network_id'] not in valid_networks:
                errors.append(f"Network ID must be one of: {', '.join(valid_networks)}")
        
        return errors
    
    def validate_sensor_config(self, config, platform='esp32'):
        """Validate sensor configuration JSON"""
        errors = []
        
        if 'config_type' not in config or config['config_type'] != 'sensors':
            errors.append("Missing or invalid config_type (must be 'sensors')")
        
        if 'sensors' not in config:
            errors.append("Missing 'sensors' array")
            return errors
        
        if not isinstance(config['sensors'], list):
            errors.append("'sensors' must be an array")
            return errors
        
        if len(config['sensors']) == 0:
            errors.append("At least one sensor must be configured")
        
        used_pins = set()
        sensor_ids = set()
        
        for i, sensor in enumerate(config['sensors']):
            sensor_errors = self._validate_single_sensor(sensor, i, platform, used_pins, sensor_ids)
            errors.extend(sensor_errors)
        
        return errors
    
    def _validate_single_sensor(self, sensor, index, platform, used_pins, sensor_ids):
        """Validate a single sensor configuration"""
        errors = []
        
        # Required fields
        required_fields = ['sensor_id', 'sensor_type', 'enabled']
        for field in required_fields:
            if field not in sensor:
                errors.append(f"Sensor {index}: Missing required field '{field}'")
        
        # Sensor ID validation
        if 'sensor_id' in sensor:
            sensor_id = sensor['sensor_id']
            if sensor_id in sensor_ids:
                errors.append(f"Sensor {index}: Duplicate sensor_id '{sensor_id}'")
            sensor_ids.add(sensor_id)
            
            if not sensor_id or len(sensor_id) < 2:
                errors.append(f"Sensor {index}: sensor_id must be at least 2 characters")
            if not sensor_id.replace('_', '').isalnum():
                errors.append(f"Sensor {index}: sensor_id can only contain letters, numbers, and underscores")
        
        # Sensor type validation
        if 'sensor_type' in sensor:
            sensor_type = sensor['sensor_type']
            if sensor_type not in self.SENSOR_TYPES:
                valid_types = ', '.join(self.SENSOR_TYPES.keys())
                errors.append(f"Sensor {index}: Invalid sensor_type '{sensor_type}'. Valid types: {valid_types}")
            else:
                # Validate inputs for this sensor type
                input_errors = self._validate_sensor_inputs(sensor, index, sensor_type, platform, used_pins)
                errors.extend(input_errors)
        
        # Enabled field validation
        if 'enabled' in sensor and not isinstance(sensor['enabled'], bool):
            errors.append(f"Sensor {index}: 'enabled' must be true or false")
        
        # Alias validation
        if 'alias' in sensor and (not sensor['alias'] or len(sensor['alias']) > 50):
            errors.append(f"Sensor {index}: 'alias' must be 1-50 characters if provided")
        
        return errors
    
    def _validate_sensor_inputs(self, sensor, index, sensor_type, platform, used_pins):
        """Validate sensor inputs based on type"""
        errors = []
        
        sensor_def = self.SENSOR_TYPES[sensor_type]
        inputs = sensor.get('inputs', {})
        
        # Check required inputs
        for required_input in sensor_def['required_inputs']:
            if required_input not in inputs:
                errors.append(f"Sensor {index}: Missing required input '{required_input}' for type '{sensor_type}'")
        
        # Validate GPIO pins (single pin sensors)
        pin_fields = ['pin_no', 'trigger_pin', 'echo_pin', 'clk_pin', 'dt_pin']
        for pin_field in pin_fields:
            if pin_field in inputs:
                pin_no = inputs[pin_field]
                
                # Pin number validation
                if not isinstance(pin_no, int):
                    errors.append(f"Sensor {index}: {pin_field} must be an integer")
                elif pin_no not in self.GPIO_PINS[platform]:
                    errors.append(f"Sensor {index}: GPIO {pin_no} ({pin_field}) is not valid for {platform}")
                elif pin_no in used_pins:
                    errors.append(f"Sensor {index}: GPIO {pin_no} ({pin_field}) is already used by another sensor")
                else:
                    used_pins.add(pin_no)
                    
                    # Check ADC requirement for analog sensors
                    adc_required_types = ['analog_in', 'photoresistor', 'potentiometer', 'voltage']
                    if sensor_type in adc_required_types and pin_field == 'pin_no':
                        if pin_no not in self.ADC_PINS[platform]:
                            adc_pins = ', '.join(map(str, self.ADC_PINS[platform]))
                            errors.append(f"Sensor {index}: GPIO {pin_no} doesn't support ADC. Use one of: {adc_pins}")
        
        # Validate boolean inputs
        boolean_fields = ['pull_up']
        for bool_field in boolean_fields:
            if bool_field in inputs and not isinstance(inputs[bool_field], bool):
                errors.append(f"Sensor {index}: {bool_field} must be true or false")
        
        # Validate numeric inputs
        if 'initial_value' in inputs:
            val = inputs['initial_value']
            if not isinstance(val, int) or val not in [0, 1]:
                errors.append(f"Sensor {index}: initial_value must be 0 or 1")
        
        if 'debounce_ms' in inputs:
            val = inputs['debounce_ms']
            if not isinstance(val, (int, float)) or val < 0 or val > 1000:
                errors.append(f"Sensor {index}: debounce_ms must be a number between 0 and 1000")
        
        # Validate threshold values
        threshold_fields = ['dark_threshold', 'bright_threshold']
        for threshold_field in threshold_fields:
            if threshold_field in inputs:
                val = inputs[threshold_field]
                if not isinstance(val, (int, float)) or val < 0 or val > 65535:
                    errors.append(f"Sensor {index}: {threshold_field} must be a number between 0 and 65535")
        
        # Validate calibration values
        calibration_fields = ['min_value', 'max_value', 'reference_voltage', 'voltage_divider_ratio']
        for cal_field in calibration_fields:
            if cal_field in inputs:
                val = inputs[cal_field]
                if not isinstance(val, (int, float)):
                    errors.append(f"Sensor {index}: {cal_field} must be a number")
                elif cal_field == 'reference_voltage' and (val <= 0 or val > 5.0):
                    errors.append(f"Sensor {index}: reference_voltage must be between 0 and 5.0 volts")
                elif cal_field == 'voltage_divider_ratio' and val <= 0:
                    errors.append(f"Sensor {index}: voltage_divider_ratio must be greater than 0")
        
        # Validate string inputs
        if 'units' in inputs:
            units = inputs['units']
            if not isinstance(units, str) or len(units) > 20:
                errors.append(f"Sensor {index}: units must be a string with maximum 20 characters")
        
        return errors
    
    def validate_json_string(self, json_str):
        """Validate JSON string format"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

# Example usage and testing
def main():
    """Example validation usage"""
    validator = ConfigValidator()
    
    # Test device configuration
    print("=== Testing Device Configuration ===")
    device_config = {
        "device_id": "my-iot-device",
        "ssid": "MyWiFi",
        "wifi_password": "password123",
        "network_id": "testnet04", 
        "publicKey": "your-public-key",
        "secretKey": "your-secret-key"
    }
    
    errors = validator.validate_device_config(device_config)
    if errors:
        print("Device config errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Device configuration is valid")
    
    # Test sensor configuration
    print("\n=== Testing Sensor Configuration ===")
    sensor_config = {
        "config_type": "sensors",
        "sensors": [
            {
                "sensor_id": "temp1",
                "sensor_type": "temp_internal",
                "enabled": True,
                "alias": "CPU Temperature"
            },
            {
                "sensor_id": "led1",
                "sensor_type": "digital_out", 
                "inputs": {"pin_no": 2, "initial_value": 0},
                "enabled": True,
                "alias": "Status LED"
            },
            {
                "sensor_id": "button1",
                "sensor_type": "digital_in",
                "inputs": {"pin_no": 0, "pull_up": True},
                "enabled": True,
                "alias": "Boot Button"
            }
        ]
    }
    
    errors = validator.validate_sensor_config(sensor_config, 'esp32')
    if errors:
        print("Sensor config errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Sensor configuration is valid")
    
    # Test invalid configuration
    print("\n=== Testing Invalid Configuration ===")
    invalid_config = {
        "config_type": "sensors",
        "sensors": [
            {
                "sensor_id": "led1",
                "sensor_type": "digital_out",
                "inputs": {"pin_no": 2},
                "enabled": True
            },
            {
                "sensor_id": "led1",  # Duplicate ID
                "sensor_type": "digital_out", 
                "inputs": {"pin_no": 2},  # Duplicate pin
                "enabled": True
            }
        ]
    }
    
    errors = validator.validate_sensor_config(invalid_config, 'esp32')
    print("Expected errors found:")
    for error in errors:
        print(f"  - {error}")

if __name__ == "__main__":
    main()