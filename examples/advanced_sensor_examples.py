"""
Advanced Sensor Examples for CyberFly MicroPython
Demonstrates usage of all available sensor types with practical examples.
"""

from cyberfly_sdk.sensors import SensorManager, SensorConfig
from cyberfly_sdk.cyberflySdk import CyberFlyClient
import time

def setup_basic_sensors(sensor_manager):
    """Setup basic sensor types that are always available."""
    print("=== Setting up Basic Sensors ===")
    
    # Internal temperature sensor (always available)
    temp_config = SensorConfig(
        sensor_id="cpu_temp",
        sensor_type="temp_internal",
        alias="CPU Temperature"
    )
    sensor_manager.add_sensor(temp_config)
    
    # System information sensor (always available)
    sys_config = SensorConfig(
        sensor_id="system_info",
        sensor_type="system_info",
        alias="System Monitor"
    )
    sensor_manager.add_sensor(sys_config)
    
    print("✓ Basic sensors configured")

def setup_digital_sensors(sensor_manager):
    """Setup digital input/output sensors."""
    print("\n=== Setting up Digital Sensors ===")
    
    # Enhanced button with debouncing
    button_config = SensorConfig(
        sensor_id="boot_button",
        sensor_type="button",
        inputs={
            "pin_no": 0,          # Boot button pin
            "pull_up": True,
            "debounce_ms": 50
        },
        alias="Boot Button"
    )
    sensor_manager.add_sensor(button_config)
    
    # Status LED output
    led_config = SensorConfig(
        sensor_id="status_led",
        sensor_type="digital_out",
        inputs={
            "pin_no": 2,          # ESP32 built-in LED
            "initial_value": 0
        },
        alias="Status LED"
    )
    sensor_manager.add_sensor(led_config)
    
    # PIR motion sensor
    pir_config = SensorConfig(
        sensor_id="motion_detector",
        sensor_type="pir_motion",
        inputs={"pin_no": 12},
        alias="Motion Detector"
    )
    sensor_manager.add_sensor(pir_config)
    
    print("✓ Digital sensors configured")

def setup_analog_sensors(sensor_manager):
    """Setup analog sensors with calibration."""
    print("\n=== Setting up Analog Sensors ===")
    
    # Photoresistor light sensor
    light_config = SensorConfig(
        sensor_id="light_sensor",
        sensor_type="photoresistor",
        inputs={
            "pin_no": 36,           # ADC capable pin
            "dark_threshold": 1000,
            "bright_threshold": 50000
        },
        alias="Light Sensor"
    )
    sensor_manager.add_sensor(light_config)
    
    # Potentiometer with custom calibration
    pot_config = SensorConfig(
        sensor_id="volume_control",
        sensor_type="potentiometer",
        inputs={
            "pin_no": 39,           # ADC capable pin
            "min_value": 0,
            "max_value": 100,
            "units": "percent"
        },
        alias="Volume Control"
    )
    sensor_manager.add_sensor(pot_config)
    
    # Voltage sensor for battery monitoring
    voltage_config = SensorConfig(
        sensor_id="battery_voltage",
        sensor_type="voltage",
        inputs={
            "pin_no": 35,                    # ADC capable pin
            "reference_voltage": 3.3,
            "voltage_divider_ratio": 2.0     # If using voltage divider
        },
        alias="Battery Monitor"
    )
    sensor_manager.add_sensor(voltage_config)
    
    print("✓ Analog sensors configured")

def setup_environmental_sensors(sensor_manager):
    """Setup environmental monitoring sensors."""
    print("\n=== Setting up Environmental Sensors ===")
    
    # DHT22 temperature and humidity
    dht_config = SensorConfig(
        sensor_id="environment",
        sensor_type="dht22",
        inputs={"pin_no": 4},
        alias="Temperature & Humidity"
    )
    sensor_manager.add_sensor(dht_config)
    
    # Ultrasonic distance sensor
    ultrasonic_config = SensorConfig(
        sensor_id="distance_meter",
        sensor_type="ultrasonic",
        inputs={
            "trigger_pin": 5,
            "echo_pin": 18
        },
        alias="Distance Meter"
    )
    sensor_manager.add_sensor(ultrasonic_config)
    
    print("✓ Environmental sensors configured")

def setup_user_interface_sensors(sensor_manager):
    """Setup user interface sensors."""
    print("\n=== Setting up User Interface Sensors ===")
    
    # Rotary encoder for user input
    encoder_config = SensorConfig(
        sensor_id="rotary_input",
        sensor_type="rotary_encoder",
        inputs={
            "clk_pin": 16,
            "dt_pin": 17
        },
        alias="Rotary Input"
    )
    sensor_manager.add_sensor(encoder_config)
    
    print("✓ User interface sensors configured")

def demonstrate_sensor_commands(sensor_manager):
    """Demonstrate various sensor command operations."""
    print("\n=== Demonstrating Sensor Commands ===")
    
    # Read all sensors
    print("\\nReading all sensors:")
    result = sensor_manager.process_command({"action": "read"})
    print(f"All sensors: {result}")
    
    # Read specific sensor
    print("\\nReading specific sensor:")
    result = sensor_manager.process_command({
        "action": "read", 
        "sensor_id": "cpu_temp"
    })
    print(f"CPU Temperature: {result}")
    
    # Control LED output
    print("\\nControlling LED:")
    result = sensor_manager.process_command({
        "action": "execute",
        "sensor_id": "status_led",
        "params": {"execute_action": "toggle"}
    })
    print(f"LED toggle: {result}")
    
    # Get sensor status
    print("\\nGetting sensor status:")
    result = sensor_manager.process_command({"action": "status"})
    print(f"Sensor status: {result}")

def advanced_sensor_usage():
    """Advanced sensor usage patterns."""
    print("\n=== Advanced Sensor Usage Patterns ===")
    
    sensor_manager = SensorManager()
    
    # Setup motion-activated lighting system
    motion_config = SensorConfig(
        sensor_id="motion_light_trigger",
        sensor_type="pir_motion",
        inputs={"pin_no": 12},
        alias="Motion Light Trigger"
    )
    sensor_manager.add_sensor(motion_config)
    
    led_config = SensorConfig(
        sensor_id="auto_light",
        sensor_type="digital_out",
        inputs={"pin_no": 13, "initial_value": 0},
        alias="Auto Light"
    )
    sensor_manager.add_sensor(led_config)
    
    # Simulate motion-activated lighting
    print("\\nTesting motion-activated lighting:")
    
    # Check motion sensor
    motion_result = sensor_manager.process_command({
        "action": "read",
        "sensor_id": "motion_light_trigger"
    })
    
    if motion_result and motion_result.get("motion_detected"):
        # Turn on light when motion detected
        sensor_manager.process_command({
            "action": "execute",
            "sensor_id": "auto_light",
            "params": {
                "execute_action": "set_output",
                "execute_params": {"value": 1}
            }
        })
        print("Motion detected - Light ON")
    else:
        print("No motion detected - Light OFF")

def sensor_monitoring_loop(sensor_manager, duration_seconds=30):
    """Continuous sensor monitoring loop."""
    print(f"\\n=== Monitoring Sensors for {duration_seconds} seconds ===")
    
    start_time = time.time()
    reading_interval = 2  # Read every 2 seconds
    
    while (time.time() - start_time) < duration_seconds:
        try:
            # Read environmental sensors
            temp_data = sensor_manager.process_command({
                "action": "read",
                "sensor_id": "environment"
            })
            
            # Read motion sensor
            motion_data = sensor_manager.process_command({
                "action": "read", 
                "sensor_id": "motion_detector"
            })
            
            # Read light sensor
            light_data = sensor_manager.process_command({
                "action": "read",
                "sensor_id": "light_sensor"
            })
            
            # Print summary
            current_time = time.time() - start_time
            print(f"\\n[{current_time:.1f}s] Sensor readings:")
            if temp_data:
                print(f"  Temperature: {temp_data.get('temperature_c', 'N/A')}°C")
                print(f"  Humidity: {temp_data.get('humidity_percent', 'N/A')}%")
            
            if motion_data:
                print(f"  Motion: {'Detected' if motion_data.get('motion_detected') else 'None'}")
            
            if light_data:
                print(f"  Light: {light_data.get('light_percent', 'N/A')}%")
            
            time.sleep(reading_interval)
            
        except KeyboardInterrupt:
            print("\\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"Error during monitoring: {e}")
            time.sleep(1)

def main():
    """Main example function demonstrating all sensor capabilities."""
    print("CyberFly MicroPython - Advanced Sensor Examples")
    print("=" * 50)
    
    # Initialize sensor manager
    sensor_manager = SensorManager()
    
    try:
        # Setup different categories of sensors
        setup_basic_sensors(sensor_manager)
        setup_digital_sensors(sensor_manager)
        setup_analog_sensors(sensor_manager)
        setup_environmental_sensors(sensor_manager)
        setup_user_interface_sensors(sensor_manager)
        
        # Demonstrate sensor operations
        demonstrate_sensor_commands(sensor_manager)
        
        # Show advanced usage patterns
        advanced_sensor_usage()
        
        # Optional: Run monitoring loop
        print("\\n" + "=" * 50)
        print("Starting sensor monitoring...")
        print("Press Ctrl+C to stop monitoring")
        
        sensor_monitoring_loop(sensor_manager, duration_seconds=60)
        
    except Exception as e:
        print(f"Error in sensor examples: {e}")
    
    finally:
        print("\\nSensor examples completed!")

def create_iot_dashboard_config():
    """Create a complete IoT dashboard sensor configuration."""
    print("\\n=== IoT Dashboard Configuration Example ===")
    
    # This configuration can be sent via BLE or used programmatically
    dashboard_config = {
        "config_type": "sensors",
        "sensors": [
            # Environmental monitoring
            {
                "sensor_id": "env_temp_humid",
                "sensor_type": "dht22",
                "inputs": {"pin_no": 4},
                "enabled": True,
                "alias": "Environment Monitor"
            },
            
            # Security system
            {
                "sensor_id": "motion_security",
                "sensor_type": "pir_motion", 
                "inputs": {"pin_no": 12},
                "enabled": True,
                "alias": "Security Motion"
            },
            {
                "sensor_id": "security_light",
                "sensor_type": "digital_out",
                "inputs": {"pin_no": 13, "initial_value": 0},
                "enabled": True,
                "alias": "Security Light"
            },
            
            # Distance monitoring
            {
                "sensor_id": "parking_sensor",
                "sensor_type": "ultrasonic",
                "inputs": {"trigger_pin": 5, "echo_pin": 18},
                "enabled": True,
                "alias": "Parking Distance"
            },
            
            # Ambient monitoring
            {
                "sensor_id": "ambient_light",
                "sensor_type": "photoresistor",
                "inputs": {"pin_no": 36},
                "enabled": True,
                "alias": "Ambient Light"
            },
            
            # User controls
            {
                "sensor_id": "user_button",
                "sensor_type": "button",
                "inputs": {"pin_no": 0, "pull_up": True, "debounce_ms": 50},
                "enabled": True,
                "alias": "User Button"
            },
            {
                "sensor_id": "brightness_control",
                "sensor_type": "potentiometer",
                "inputs": {"pin_no": 39, "min_value": 0, "max_value": 100, "units": "percent"},
                "enabled": True,
                "alias": "Brightness Control"
            },
            
            # System monitoring
            {
                "sensor_id": "battery_level",
                "sensor_type": "voltage",
                "inputs": {"pin_no": 35, "reference_voltage": 3.3, "voltage_divider_ratio": 2.0},
                "enabled": True,
                "alias": "Battery Level"
            },
            {
                "sensor_id": "system_status",
                "sensor_type": "system_info",
                "enabled": True,
                "alias": "System Status"
            }
        ]
    }
    
    print("Complete IoT dashboard configuration:")
    import json
    print(json.dumps(dashboard_config, indent=2))
    
    return dashboard_config

if __name__ == "__main__":
    # Run basic examples
    main()
    
    # Show complete dashboard configuration
    create_iot_dashboard_config()