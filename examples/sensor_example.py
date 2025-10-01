"""
Example: CyberFly MicroPython Sensor Integration

This example demonstrates how to use the CyberFly MicroPython SDK with integrated sensor support.
Similar functionality to the Python client SDK but optimized for MicroPython constraints.

Prerequisites:
- ESP32 or RP2040 board
- MicroPython firmware
- Connected sensors (optional - includes mock sensors for testing)
"""

from cyberflySdk import CyberflyClient
import time
import gc

# Example device configuration - these would normally come from BLE provisioning
DEVICE_CONFIG = {
    "device_id": "micropython-sensor-device-01",
    "ssid": "your-wifi-ssid",
    "wifi_password": "your-wifi-password",
    "network_id": "testnet04",
    "key_pair": {
        "publicKey": "d04bbd8f403e583248aa461896bd7518113f89b85c98f3d9596bbfbf30df0bcb",
        "secretKey": "a0ec3175c6c80e60bc8ef18bd7b73a631c507b9f0a42c973036c7f96d21b047a"
    }
}

def setup_example_sensors(client):
    """Set up example sensors for demonstration."""
    
    print("Setting up example sensors...")
    
    # Internal temperature sensor (works on ESP32/RP2040)
    client.add_sensor(
        sensor_id="internal_temp",
        sensor_type="temp_internal",
        inputs={},
        alias="Internal Temperature"
    )
    
    # System information sensor
    client.add_sensor(
        sensor_id="system_info",
        sensor_type="system_info",
        inputs={},
        alias="System Monitor"
    )
    
    # Digital input sensor (button on GPIO 0)
    client.add_sensor(
        sensor_id="button_1",
        sensor_type="digital_in", 
        inputs={"pin_no": 0, "pull_up": True},
        alias="Boot Button"
    )
    
    # Digital output sensor (LED on GPIO 2) 
    client.add_sensor(
        sensor_id="led_1",
        sensor_type="digital_out",
        inputs={"pin_no": 2, "initial_value": 0},
        alias="Status LED"
    )
    
    # Analog input sensor (if available on your board)
    # client.add_sensor(
    #     sensor_id="analog_1",
    #     sensor_type="analog_in",
    #     inputs={"pin_no": 36},  # ESP32 ADC pin
    #     alias="Analog Sensor"
    # )
    
    print("Sensors configured successfully")

def handle_iot_commands(command_data):
    """
    Handle commands from the IoT platform UI.
    
    Expected sensor command formats:
    1. Read specific sensor:
       {"sensor_command": {"action": "read", "sensor_id": "internal_temp"}}
    
    2. Read all sensors:
       {"sensor_command": {"action": "read"}}
    
    3. Execute action on output sensor:
       {"sensor_command": {"action": "execute", "sensor_id": "led_1", 
                          "params": {"execute_action": "toggle"}}}
    
    4. Get sensor status:
       {"sensor_command": {"action": "status"}}
    """
    print(f"Received command: {command_data}")
    
    # Sensor commands are handled automatically by the SDK
    # This handler is for other types of commands
    if 'custom_action' in command_data:
        print(f"Handling custom action: {command_data['custom_action']}")
        # Add your custom command handling here

def main():
    """Main application loop."""
    
    # Initialize the CyberFly client
    client = CyberflyClient(
        device_id=DEVICE_CONFIG["device_id"],
        key_pair=DEVICE_CONFIG["key_pair"],
        ssid=DEVICE_CONFIG["ssid"],
        wifi_password=DEVICE_CONFIG["wifi_password"],
        network_id=DEVICE_CONFIG["network_id"]
    )
    
    print(f"Initialized CyberFly client for device: {DEVICE_CONFIG['device_id']}")
    
    # Set up sensors
    setup_example_sensors(client)
    
    # Set up command handler for IoT platform commands
    @client.on_message()
    def message_handler(data):
        handle_iot_commands(data)
    
    # Display sensor status
    print("\nSensor Status:")
    status = client.get_sensor_status()
    print(f"Total sensors: {status['total_sensors']}")
    for sensor in status['sensors']:
        state = "enabled" if sensor['enabled'] else "disabled"
        print(f"  - {sensor['sensor_id']}: {sensor['sensor_type']} ({state})")
    
    # Main loop
    print("\nStarting main loop...")
    print("Device is ready to receive commands from IoT platform")
    print("Send sensor commands from the platform UI to:")
    print("  - Read sensor data")
    print("  - Control output devices") 
    print("  - Get device status")
    
    last_publish_time = time.time()
    publish_interval = 30  # seconds
    
    try:
        while True:
            # Check for incoming messages
            client.check_msg()
            
            # Periodically publish sensor readings
            current_time = time.time()
            if current_time - last_publish_time >= publish_interval:
                try:
                    # Read and publish all sensor data
                    readings = client.read_all_sensors()
                    if readings:
                        print(f"\nSensor readings at {time.time()}:")
                        for reading in readings:
                            if reading['status'] == 'success':
                                data_str = ', '.join([f"{k}: {v}" for k, v in reading['data'].items()])
                                print(f"  {reading['sensor_id']}: {data_str}")
                            else:
                                print(f"  {reading['sensor_id']}: ERROR - {reading.get('error', 'Unknown error')}")
                        
                        # Publish to platform
                        client.publish_all_sensor_readings()
                        print("Published sensor readings to platform")
                    
                    last_publish_time = current_time
                    
                except Exception as e:
                    print(f"Error reading/publishing sensors: {e}")
            
            # Garbage collection to free memory
            gc.collect()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error in main loop: {e}")

def test_sensor_commands():
    """
    Test function to demonstrate sensor commands that can be sent from IoT platform.
    This shows the format of commands that the IoT platform UI should send.
    """
    
    print("=== Example Sensor Commands for IoT Platform ===\n")
    
    # Example commands that can be sent from IoT platform:
    
    print("1. Read specific sensor:")
    read_command = {
        "sensor_command": {
            "action": "read",
            "sensor_id": "internal_temp"
        }
    }
    print(f"   {read_command}\n")
    
    print("2. Read all sensors:")
    read_all_command = {
        "sensor_command": {
            "action": "read"
        }
    }
    print(f"   {read_all_command}\n")
    
    print("3. Get sensor status:")
    status_command = {
        "sensor_command": {
            "action": "status"
        }
    }
    print(f"   {status_command}\n")
    
    print("4. Execute action on output sensor (toggle LED):")
    execute_command = {
        "sensor_command": {
            "action": "execute", 
            "sensor_id": "led_1",
            "params": {
                "execute_action": "toggle"
            }
        }
    }
    print(f"   {execute_command}\n")
    
    print("5. Set output sensor value:")
    set_output_command = {
        "sensor_command": {
            "action": "execute",
            "sensor_id": "led_1", 
            "params": {
                "execute_action": "set_output",
                "execute_params": {"value": 1}
            }
        }
    }
    print(f"   {set_output_command}\n")

if __name__ == "__main__":
    # Uncomment to see example commands
    # test_sensor_commands()
    
    main()