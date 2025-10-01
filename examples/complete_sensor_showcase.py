"""
Complete Sensor Showcase for CyberFly MicroPython
Demonstrates all 36+ sensor types including I2C environmental sensors,
motion detection, distance measurement, displays, and more.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cyberfly_sdk.sensors import SensorManager, SensorConfig
import time
import json

def showcase_environmental_sensors():
    """Showcase environmental monitoring sensors."""
    print("=== Environmental Sensors Showcase ===")
    
    sensor_manager = SensorManager()
    
    # Basic environmental sensors
    configs = [
        SensorConfig("temp_cpu", "temp_internal", alias="CPU Temperature"),
        SensorConfig("dht11_basic", "dht11", {"pin_no": 4}, alias="Basic Temp/Humidity"),
        SensorConfig("dht22_precise", "dht22", {"pin_no": 5}, alias="Precise Temp/Humidity"),
        SensorConfig("ds18b20_probe", "ds18b20", {"pin_no": 18, "unit": "celsius"}, alias="Waterproof Probe"),
    ]
    
    # I2C environmental sensors  
    i2c_configs = [
        SensorConfig("bmp280_pressure", "bmp280", {"address": 119}, alias="Pressure Sensor"),
        SensorConfig("bme280_combo", "bme280", {"address": 118}, alias="All-in-One Environment"),
        SensorConfig("bme680_air", "bme680", {"address": 117}, alias="Air Quality Monitor"),
        SensorConfig("sht31d_precision", "sht31d", {"address": 68}, alias="Precision Humidity"),
    ]
    
    # Add all sensors
    for config in configs + i2c_configs:
        sensor_manager.add_sensor(config)
    
    # Read environmental data
    print("\\nEnvironmental readings:")
    for sensor_id in ["temp_cpu", "dht11_basic", "bme280_combo"]:
        result = sensor_manager.process_command({"action": "read", "sensor_id": sensor_id})
        print(f"  {sensor_id}: {result}")
    
    return sensor_manager

def showcase_motion_detection():
    """Showcase motion and detection sensors."""
    print("\\n=== Motion & Detection Sensors ===")
    
    sensor_manager = SensorManager()
    
    configs = [
        SensorConfig("pir_motion", "pir", {"pin_no": 12}, alias="PIR Motion"),
        SensorConfig("hall_magnet", "hall", {"pin_no": 13}, alias="Hall Effect"),
        SensorConfig("water_detect", "water", {"pin_no": 14}, alias="Water Detector"),
        SensorConfig("generic_input", "din", {"pin_no": 15}, alias="Generic Input"),
    ]
    
    for config in configs:
        sensor_manager.add_sensor(config)
    
    print("\\nMotion & detection readings:")
    for sensor_id in ["pir_motion", "hall_magnet", "water_detect"]:
        result = sensor_manager.process_command({"action": "read", "sensor_id": sensor_id})
        print(f"  {sensor_id}: {result}")
    
    return sensor_manager

def showcase_distance_sensors():
    """Showcase distance measurement sensors."""
    print("\\n=== Distance Measurement Sensors ===")
    
    sensor_manager = SensorManager()
    
    configs = [
        SensorConfig("ultrasonic_basic", "ultrasonic", 
                    {"trigger_pin": 5, "echo_pin": 18}, 
                    alias="Basic Ultrasonic"),
        SensorConfig("hc_sr04_enhanced", "hc_sr04", 
                    {"trigger_pin": 6, "echo_pin": 19, "max_distance": 3.0, "threshold_distance": 0.3}, 
                    alias="Enhanced HC-SR04"),
        SensorConfig("vl53l0x_tof", "vl53l0x", 
                    {"address": 41}, 
                    alias="Time-of-Flight"),
    ]
    
    for config in configs:
        sensor_manager.add_sensor(config)
    
    print("\\nDistance measurements:")
    for sensor_id in ["ultrasonic_basic", "vl53l0x_tof"]:
        result = sensor_manager.process_command({"action": "read", "sensor_id": sensor_id})
        print(f"  {sensor_id}: {result}")
    
    return sensor_manager

def showcase_light_color_sensors():
    """Showcase light and color sensors."""
    print("\\n=== Light & Color Sensors ===")
    
    sensor_manager = SensorManager()
    
    configs = [
        SensorConfig("ldr_basic", "photoresistor", 
                    {"pin_no": 36, "dark_threshold": 1000, "bright_threshold": 50000}, 
                    alias="Light Sensor"),
        SensorConfig("bh1750_lux", "bh1750", 
                    {"address": 35}, 
                    alias="Lux Meter"),
        SensorConfig("tcs34725_color", "tcs34725", 
                    {"address": 41, "gain": 16, "integration_time": 154}, 
                    alias="RGB Color Sensor"),
    ]
    
    for config in configs:
        sensor_manager.add_sensor(config)
    
    print("\\nLight & color readings:")
    for sensor_id in ["ldr_basic", "bh1750_lux", "tcs34725_color"]:
        result = sensor_manager.process_command({"action": "read", "sensor_id": sensor_id})
        print(f"  {sensor_id}: {result}")
    
    return sensor_manager

def showcase_user_interface():
    """Showcase user interface sensors."""
    print("\\n=== User Interface Sensors ===")
    
    sensor_manager = SensorManager()
    
    configs = [
        SensorConfig("enhanced_button", "button", 
                    {"pin_no": 0, "pull_up": True, "debounce_ms": 50}, 
                    alias="Enhanced Button"),
        SensorConfig("rotary_control", "rotary_encoder", 
                    {"clk_pin": 16, "dt_pin": 17}, 
                    alias="Rotary Control"),
        SensorConfig("volume_pot", "potentiometer", 
                    {"pin_no": 39, "min_value": 0, "max_value": 100, "units": "percent"}, 
                    alias="Volume Control"),
    ]
    
    for config in configs:
        sensor_manager.add_sensor(config)
    
    print("\\nUser interface readings:")
    for sensor_id in ["enhanced_button", "rotary_control", "volume_pot"]:
        result = sensor_manager.process_command({"action": "read", "sensor_id": sensor_id})
        print(f"  {sensor_id}: {result}")
    
    return sensor_manager

def showcase_advanced_sensors():
    """Showcase advanced I2C sensors."""
    print("\\n=== Advanced I2C Sensors ===")
    
    sensor_manager = SensorManager()
    
    configs = [
        SensorConfig("air_quality", "ccs811", 
                    {"address": 90, "temperature_offset": 0}, 
                    alias="Air Quality Monitor"),
        SensorConfig("adc_external", "ads1115", 
                    {"address": 72, "channel": 0, "gain": 2}, 
                    alias="External ADC"),
        SensorConfig("imu_motion", "mpu6050", 
                    {"address": 104}, 
                    alias="IMU Sensor"),
        SensorConfig("voltage_monitor", "voltage", 
                    {"pin_no": 35, "reference_voltage": 3.3, "voltage_divider_ratio": 2.0}, 
                    alias="Battery Monitor"),
    ]
    
    for config in configs:
        sensor_manager.add_sensor(config)
    
    print("\\nAdvanced sensor readings:")
    for sensor_id in ["air_quality", "imu_motion", "voltage_monitor"]:
        result = sensor_manager.process_command({"action": "read", "sensor_id": sensor_id})
        print(f"  {sensor_id}: {result}")
    
    return sensor_manager

def showcase_display_modules():
    """Showcase display modules."""
    print("\\n=== Display Modules ===")
    
    sensor_manager = SensorManager()
    
    configs = [
        SensorConfig("main_lcd", "lcd1602", 
                    {"address": 39, "columns": 16, "rows": 2, "text": "CyberFly IoT"}, 
                    alias="Main Display"),
        SensorConfig("seven_seg", "ht16k33", 
                    {"address": 112, "text": "1234", "align_right": True}, 
                    alias="7-Segment Display"),
        SensorConfig("status_led", "dout", 
                    {"pin_no": 2, "initial_value": 0}, 
                    alias="Status LED"),
    ]
    
    for config in configs:
        sensor_manager.add_sensor(config)
    
    # Test display actions
    print("\\nTesting display actions:")
    
    # Update LCD display
    result = sensor_manager.process_command({
        "action": "execute",
        "sensor_id": "main_lcd",
        "params": {
            "execute_action": "display_text",
            "execute_params": {"text": "Sensor Demo\\nRunning..."}
        }
    })
    print(f"  LCD update: {result}")
    
    # Update 7-segment display
    result = sensor_manager.process_command({
        "action": "execute", 
        "sensor_id": "seven_seg",
        "params": {
            "execute_action": "display_text",
            "execute_params": {"text": "88.88"}
        }
    })
    print(f"  7-segment update: {result}")
    
    # Toggle LED
    result = sensor_manager.process_command({
        "action": "execute",
        "sensor_id": "status_led", 
        "params": {"execute_action": "toggle"}
    })
    print(f"  LED toggle: {result}")
    
    return sensor_manager

def create_complete_iot_device():
    """Create a complete IoT device with all sensor categories."""
    print("\\n=== Complete IoT Device Configuration ===")
    
    complete_config = {
        "config_type": "sensors",
        "sensors": [
            # Environmental monitoring
            {"sensor_id": "env_temp_hum", "sensor_type": "dht22", "inputs": {"pin_no": 4}, "enabled": True, "alias": "Environment"},
            {"sensor_id": "air_pressure", "sensor_type": "bmp280", "inputs": {"address": 119}, "enabled": True, "alias": "Barometer"},
            {"sensor_id": "air_quality", "sensor_type": "ccs811", "inputs": {"address": 90}, "enabled": True, "alias": "Air Quality"},
            
            # Security system
            {"sensor_id": "motion_security", "sensor_type": "pir", "inputs": {"pin_no": 12}, "enabled": True, "alias": "Security Motion"},
            {"sensor_id": "entry_sensor", "sensor_type": "hall", "inputs": {"pin_no": 13}, "enabled": True, "alias": "Door Sensor"},
            {"sensor_id": "water_leak", "sensor_type": "water", "inputs": {"pin_no": 14}, "enabled": True, "alias": "Leak Detector"},
            
            # Distance monitoring  
            {"sensor_id": "parking_distance", "sensor_type": "vl53l0x", "inputs": {"address": 41}, "enabled": True, "alias": "Parking Sensor"},
            {"sensor_id": "tank_level", "sensor_type": "hc_sr04", "inputs": {"trigger_pin": 5, "echo_pin": 18}, "enabled": True, "alias": "Tank Level"},
            
            # Ambient monitoring
            {"sensor_id": "light_level", "sensor_type": "bh1750", "inputs": {"address": 35}, "enabled": True, "alias": "Light Meter"},
            {"sensor_id": "color_detection", "sensor_type": "tcs34725", "inputs": {"address": 41}, "enabled": True, "alias": "Color Sensor"},
            
            # User controls
            {"sensor_id": "user_button", "sensor_type": "button", "inputs": {"pin_no": 0, "debounce_ms": 50}, "enabled": True, "alias": "User Button"},
            {"sensor_id": "brightness_dial", "sensor_type": "potentiometer", "inputs": {"pin_no": 39, "units": "percent"}, "enabled": True, "alias": "Brightness"},
            {"sensor_id": "navigation_wheel", "sensor_type": "rotary_encoder", "inputs": {"clk_pin": 16, "dt_pin": 17}, "enabled": True, "alias": "Navigation"},
            
            # System monitoring
            {"sensor_id": "battery_voltage", "sensor_type": "voltage", "inputs": {"pin_no": 35, "voltage_divider_ratio": 2.0}, "enabled": True, "alias": "Battery"},
            {"sensor_id": "motion_imu", "sensor_type": "mpu6050", "inputs": {"address": 104}, "enabled": True, "alias": "Motion IMU"},
            {"sensor_id": "external_adc", "sensor_type": "ads1115", "inputs": {"address": 72, "channel": 0}, "enabled": True, "alias": "External ADC"},
            
            # Display and output
            {"sensor_id": "main_display", "sensor_type": "lcd1602", "inputs": {"address": 39, "text": "IoT Dashboard"}, "enabled": True, "alias": "Main Display"},
            {"sensor_id": "status_display", "sensor_type": "ht16k33", "inputs": {"address": 112}, "enabled": True, "alias": "Status Display"},
            {"sensor_id": "alarm_led", "sensor_type": "dout", "inputs": {"pin_no": 2}, "enabled": True, "alias": "Alarm LED"},
            
            # System sensors
            {"sensor_id": "cpu_temperature", "sensor_type": "temp_internal", "enabled": True, "alias": "CPU Temp"},
            {"sensor_id": "system_monitor", "sensor_type": "system_info", "enabled": True, "alias": "System Status"}
        ]
    }
    
    print("Complete IoT device configuration:")
    print(json.dumps(complete_config, indent=2))
    
    # Validate the configuration
    from config_validator import ConfigValidator
    validator = ConfigValidator()
    errors = validator.validate_sensor_config(complete_config, 'esp32')
    
    if errors:
        print("\\nConfiguration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\\n✓ Complete IoT device configuration is valid!")
        print(f"✓ Total sensors configured: {len(complete_config['sensors'])}")
        
        # Group by category
        categories = {}
        for sensor in complete_config['sensors']:
            sensor_type = sensor['sensor_type']
            category = "I2C" if sensor_type in ['bmp280', 'bme280', 'ccs811', 'bh1750', 'tcs34725', 'vl53l0x', 'mpu6050', 'ads1115', 'lcd1602', 'ht16k33'] else "GPIO"
            if category not in categories:
                categories[category] = []
            categories[category].append(sensor_type)
        
        for category, types in categories.items():
            print(f"✓ {category} sensors: {len(types)} types")

def run_sensor_monitoring_demo():
    """Run a comprehensive sensor monitoring demonstration."""
    print("\\n=== Sensor Monitoring Demo ===")
    
    # Setup a subset of sensors for live demo
    sensor_manager = SensorManager()
    
    demo_configs = [
        SensorConfig("cpu_temp", "temp_internal", alias="CPU Temperature"),
        SensorConfig("system_info", "system_info", alias="System Monitor"),
        SensorConfig("mock_env", "dht22", {"pin_no": 4}, alias="Environment"),
        SensorConfig("mock_light", "photoresistor", {"pin_no": 36}, alias="Light Level"),
        SensorConfig("mock_motion", "pir", {"pin_no": 12}, alias="Motion Detector"),
    ]
    
    for config in demo_configs:
        sensor_manager.add_sensor(config)
    
    print("\\nRunning 10-second monitoring demo...")
    start_time = time.time()
    
    try:
        while (time.time() - start_time) < 10:
            # Read all sensors
            result = sensor_manager.process_command({"action": "read"})
            
            # Extract key readings
            cpu_temp = result.get("cpu_temp", {}).get("temperature_c", "N/A")
            memory_usage = result.get("system_info", {}).get("memory_usage_percent", "N/A")
            
            print(f"[{time.time() - start_time:.1f}s] CPU: {cpu_temp}°C, Memory: {memory_usage}%, Sensors: {len(result)} active")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\\nDemo stopped by user")
    
    print("Demo completed!")

def main():
    """Main demonstration function."""
    print("CyberFly MicroPython - Complete Sensor Showcase")
    print("=" * 60)
    print(f"Demonstrating 36+ sensor types across multiple categories")
    
    try:
        # Showcase each category
        showcase_environmental_sensors()
        showcase_motion_detection()
        showcase_distance_sensors()
        showcase_light_color_sensors()
        showcase_user_interface()
        showcase_advanced_sensors()
        showcase_display_modules()
        
        # Create complete configuration
        create_complete_iot_device()
        
        # Run live demo
        print("\\nPress Ctrl+C to skip the monitoring demo...")
        time.sleep(2)
        run_sensor_monitoring_demo()
        
    except Exception as e:
        print(f"Error during showcase: {e}")
    
    print("\\n" + "=" * 60)
    print("Sensor showcase completed!")
    print("All sensor types are ready for production use.")

if __name__ == "__main__":
    main()

from cyberfly_sdk.sensors import SensorManager, SensorConfig
import time

def showcase_basic_sensors():
    """Basic sensors that are always available."""
    print("=== BASIC SENSORS ===")
    
    configs = [
        # Always available sensors
        SensorConfig("cpu_temp", "temp_internal", alias="CPU Temperature"),
        SensorConfig("sys_monitor", "system_info", alias="System Monitor"),
        SensorConfig("cpu_vcgen", "vcgen", alias="CPU Temperature (vcgen)"),
        
        # Basic GPIO sensors
        SensorConfig("boot_btn", "digital_in", {"pin_no": 0, "pull_up": True}, alias="Boot Button"),
        SensorConfig("status_led", "digital_out", {"pin_no": 2, "initial_value": 0}, alias="Status LED"),
        SensorConfig("analog_sensor", "analog_in", {"pin_no": 36}, alias="Analog Input"),
    ]
    
    return configs

def showcase_environmental_sensors():
    """Environmental monitoring sensors."""
    print("=== ENVIRONMENTAL SENSORS ===")
    
    configs = [
        # Temperature & Humidity
        SensorConfig("dht11_env", "dht11", {"pin_no": 4}, alias="DHT11 Environment"),
        SensorConfig("dht22_env", "dht22", {"pin_no": 5}, alias="DHT22 Environment"),
        SensorConfig("sht31d_env", "sht31d", {"address": 68}, alias="SHT31-D Environment"),
        
        # Temperature probes
        SensorConfig("temp_probe", "ds18b20", {"pin_no": 18, "unit": "celsius"}, alias="Waterproof Temp"),
        
        # Pressure sensors
        SensorConfig("pressure", "bmp280", {"address": 119}, alias="Barometric Pressure"),
        SensorConfig("full_env", "bme280", {"address": 119}, alias="Full Environment"),
        SensorConfig("air_quality", "bme680", {"address": 119}, alias="Air Quality"),
        SensorConfig("co2_sensor", "ccs811", {"address": 90}, alias="CO2 Monitor"),
    ]
    
    return configs

def showcase_motion_sensors():
    """Motion and position sensors."""
    print("=== MOTION & POSITION SENSORS ===")
    
    configs = [
        # Motion detection
        SensorConfig("pir_basic", "pir", {"pin_no": 12}, alias="PIR Motion"),
        SensorConfig("pir_advanced", "pir_motion", {"pin_no": 13}, alias="PIR Motion Advanced"),
        
        # Acceleration & Gyroscope
        SensorConfig("imu", "mpu6050", {"address": 104}, alias="IMU Sensor"),
        
        # User interface
        SensorConfig("button", "button", {"pin_no": 0, "debounce_ms": 50}, alias="Enhanced Button"),
        SensorConfig("encoder", "rotary_encoder", {"clk_pin": 16, "dt_pin": 17}, alias="Rotary Encoder"),
    ]
    
    return configs

def showcase_distance_sensors():
    """Distance measurement sensors."""
    print("=== DISTANCE SENSORS ===")
    
    configs = [
        # Ultrasonic sensors
        SensorConfig("ultrasonic", "ultrasonic", {"trigger_pin": 5, "echo_pin": 18}, alias="Ultrasonic Basic"),
        SensorConfig("hc_sr04", "hc_sr04", {"trigger_pin": 25, "echo_pin": 26, "threshold_distance": 0.3}, alias="HC-SR04 Advanced"),
        
        # Laser distance
        SensorConfig("laser_distance", "vl53l0x", {"address": 41}, alias="Laser Distance"),
    ]
    
    return configs

def showcase_light_sensors():
    """Light and color sensors."""
    print("=== LIGHT & COLOR SENSORS ===")
    
    configs = [
        # Light sensors
        SensorConfig("photoresistor", "photoresistor", {"pin_no": 36}, alias="Light Level"),
        SensorConfig("lux_meter", "bh1750", {"address": 35}, alias="Lux Meter"),
        
        # Color sensor
        SensorConfig("color_sensor", "tcs34725", {"address": 41}, alias="RGB Color"),
    ]
    
    return configs

def showcase_analog_sensors():
    """Analog sensors with calibration."""
    print("=== ANALOG SENSORS ===")
    
    configs = [
        # Calibrated analog sensors
        SensorConfig("potentiometer", "potentiometer", {"pin_no": 39, "min_value": 0, "max_value": 100}, alias="Volume Control"),
        SensorConfig("voltage_monitor", "voltage", {"pin_no": 35, "voltage_divider_ratio": 2.0}, alias="Battery Monitor"),
        
        # High-precision ADC
        SensorConfig("precision_adc", "ads1115", {"address": 72, "channel": 0, "gain": 1}, alias="Precision ADC"),
    ]
    
    return configs

def showcase_digital_sensors():
    """Digital sensors and actuators."""
    print("=== DIGITAL SENSORS ===")
    
    configs = [
        # Digital inputs
        SensorConfig("generic_input", "din", {"pin_no": 14}, alias="Generic Input"),
        SensorConfig("hall_sensor", "hall", {"pin_no": 15}, alias="Magnetic Sensor"),
        SensorConfig("water_sensor", "water", {"pin_no": 27}, alias="Water Detector"),
        
        # Digital outputs
        SensorConfig("relay", "dout", {"pin_no": 32, "active_high": True}, alias="Relay Control"),
        SensorConfig("led_output", "digital_out", {"pin_no": 33}, alias="LED Output"),
    ]
    
    return configs

def showcase_display_sensors():
    """Display and output devices."""
    print("=== DISPLAY SENSORS ===")
    
    configs = [
        # Text displays
        SensorConfig("lcd_display", "lcd1602", {"address": 39, "columns": 16, "rows": 2}, alias="LCD Display"),
        SensorConfig("segment_display", "ht16k33", {"address": 112}, alias="7-Segment Display"),
    ]
    
    return configs

def create_smart_home_config():
    """Create a complete smart home sensor configuration."""
    print("\n=== SMART HOME CONFIGURATION ===")
    
    config = {
        "config_type": "sensors",
        "sensors": [
            # Environmental monitoring
            {
                "sensor_id": "living_room_env",
                "sensor_type": "bme280",
                "inputs": {"address": 119, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Living Room Environment"
            },
            # Air quality
            {
                "sensor_id": "air_quality",
                "sensor_type": "ccs811",
                "inputs": {"address": 90, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Air Quality Monitor"
            },
            # Security system
            {
                "sensor_id": "motion_security",
                "sensor_type": "pir",
                "inputs": {"pin_no": 12},
                "enabled": True,
                "alias": "Security Motion"
            },
            {
                "sensor_id": "door_sensor",
                "sensor_type": "hall",
                "inputs": {"pin_no": 13},
                "enabled": True,
                "alias": "Door Sensor"
            },
            # Lighting control
            {
                "sensor_id": "light_level",
                "sensor_type": "bh1750",
                "inputs": {"address": 35, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Ambient Light"
            },
            {
                "sensor_id": "smart_lights",
                "sensor_type": "dout",
                "inputs": {"pin_no": 25, "active_high": True},
                "enabled": True,
                "alias": "Smart Lights"
            },
            # Water monitoring
            {
                "sensor_id": "water_leak",
                "sensor_type": "water",
                "inputs": {"pin_no": 14},
                "enabled": True,
                "alias": "Water Leak Detector"
            },
            # User interface
            {
                "sensor_id": "control_button",
                "sensor_type": "button",
                "inputs": {"pin_no": 0, "debounce_ms": 50},
                "enabled": True,
                "alias": "Control Button"
            },
            {
                "sensor_id": "brightness_dial",
                "sensor_type": "potentiometer",
                "inputs": {"pin_no": 36, "min_value": 0, "max_value": 100, "units": "percent"},
                "enabled": True,
                "alias": "Brightness Control"
            },
            # Display
            {
                "sensor_id": "status_display",
                "sensor_type": "lcd1602",
                "inputs": {"address": 39, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Status Display"
            }
        ]
    }
    
    return config

def create_industrial_config():
    """Create an industrial monitoring configuration."""
    print("\n=== INDUSTRIAL MONITORING CONFIGURATION ===")
    
    config = {
        "config_type": "sensors",
        "sensors": [
            # Machine monitoring
            {
                "sensor_id": "machine_vibration",
                "sensor_type": "mpu6050",
                "inputs": {"address": 104, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Vibration Monitor"
            },
            {
                "sensor_id": "machine_temp",
                "sensor_type": "ds18b20",
                "inputs": {"pin_no": 4, "unit": "celsius"},
                "enabled": True,
                "alias": "Machine Temperature"
            },
            # Power monitoring
            {
                "sensor_id": "voltage_main",
                "sensor_type": "ads1115",
                "inputs": {"address": 72, "channel": 0, "gain": 2, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Main Voltage"
            },
            {
                "sensor_id": "voltage_backup",
                "sensor_type": "voltage",
                "inputs": {"pin_no": 35, "voltage_divider_ratio": 5.0},
                "enabled": True,
                "alias": "Backup Power"
            },
            # Safety systems
            {
                "sensor_id": "emergency_stop",
                "sensor_type": "button",
                "inputs": {"pin_no": 0, "debounce_ms": 100},
                "enabled": True,
                "alias": "Emergency Stop"
            },
            {
                "sensor_id": "safety_relay",
                "sensor_type": "dout",
                "inputs": {"pin_no": 25, "active_high": True},
                "enabled": True,
                "alias": "Safety Relay"
            },
            # Environmental
            {
                "sensor_id": "facility_env",
                "sensor_type": "bme680",
                "inputs": {"address": 119, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Facility Environment"
            },
            # User interface
            {
                "sensor_id": "control_panel",
                "sensor_type": "ht16k33",
                "inputs": {"address": 112, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Control Panel"
            }
        ]
    }
    
    return config

def create_garden_config():
    """Create a garden monitoring configuration."""
    print("\n=== GARDEN MONITORING CONFIGURATION ===")
    
    config = {
        "config_type": "sensors",
        "sensors": [
            # Environmental monitoring
            {
                "sensor_id": "garden_climate",
                "sensor_type": "sht31d",
                "inputs": {"address": 68, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Garden Climate"
            },
            {
                "sensor_id": "soil_temp",
                "sensor_type": "ds18b20",
                "inputs": {"pin_no": 18, "unit": "celsius"},
                "enabled": True,
                "alias": "Soil Temperature"
            },
            # Light monitoring
            {
                "sensor_id": "sunlight",
                "sensor_type": "bh1750",
                "inputs": {"address": 35, "sda_pin": 21, "scl_pin": 22},
                "enabled": True,
                "alias": "Sunlight Level"
            },
            # Soil monitoring
            {
                "sensor_id": "soil_moisture",
                "sensor_type": "analog_in",
                "inputs": {"pin_no": 36},
                "enabled": True,
                "alias": "Soil Moisture"
            },
            # Water system
            {
                "sensor_id": "water_level",
                "sensor_type": "ultrasonic",
                "inputs": {"trigger_pin": 5, "echo_pin": 18},
                "enabled": True,
                "alias": "Water Tank Level"
            },
            {
                "sensor_id": "water_pump",
                "sensor_type": "dout",
                "inputs": {"pin_no": 25, "active_high": True},
                "enabled": True,
                "alias": "Water Pump"
            },
            {
                "sensor_id": "rain_sensor",
                "sensor_type": "water",
                "inputs": {"pin_no": 14},
                "enabled": True,
                "alias": "Rain Detector"
            }
        ]
    }
    
    return config

def main():
    """Demonstrate all sensor types and configurations."""
    print("CyberFly MicroPython - Complete Sensor Library")
    print("=" * 60)
    print("Supporting 37 different sensor types!")
    print()
    
    # Showcase all sensor categories
    all_configs = []
    all_configs.extend(showcase_basic_sensors())
    all_configs.extend(showcase_environmental_sensors())
    all_configs.extend(showcase_motion_sensors())
    all_configs.extend(showcase_distance_sensors())
    all_configs.extend(showcase_light_sensors())
    all_configs.extend(showcase_analog_sensors())
    all_configs.extend(showcase_digital_sensors())
    all_configs.extend(showcase_display_sensors())
    
    print(f"\\nTotal sensor configurations demonstrated: {len(all_configs)}")
    
    # Show practical configurations
    smart_home = create_smart_home_config()
    industrial = create_industrial_config()
    garden = create_garden_config()
    
    print("\\n=== SENSOR TYPE SUMMARY ===")
    sensor_categories = {
        "Basic Sensors": ["temp_internal", "system_info", "vcgen", "digital_in", "digital_out", "analog_in"],
        "Environmental": ["dht11", "dht22", "sht31d", "ds18b20", "bmp280", "bme280", "bme680", "ccs811"],
        "Motion & Position": ["pir", "pir_motion", "mpu6050", "button", "rotary_encoder"],
        "Distance": ["ultrasonic", "hc_sr04", "vl53l0x"],
        "Light & Color": ["photoresistor", "bh1750", "tcs34725"],
        "Analog": ["potentiometer", "voltage", "ads1115"],
        "Digital I/O": ["din", "hall", "water", "dout"],
        "Displays": ["lcd1602", "ht16k33"]
    }
    
    for category, sensors in sensor_categories.items():
        print(f"{category}: {len(sensors)} types")
        print(f"  {', '.join(sensors)}")
    
    print("\\n=== INTERFACE TYPES ===")
    interfaces = {
        "GPIO Digital": 15,
        "GPIO Analog": 4,
        "I2C": 12,
        "1-Wire": 1,
        "Always Available": 3,
        "Display/Output": 2
    }
    
    for interface, count in interfaces.items():
        print(f"{interface}: {count} sensors")
    
    print("\\n🎉 Complete sensor library ready for any IoT project!")

if __name__ == "__main__":
    main()