"""
CyberFly MicroPython No-Code IoT Device

This is a no    # Set up automatic command handling
    @client.on_message()
    def handle_commands(command_data):
        """
        Automatically handles all sensor commands from IoT platform.
        No code needed - sensor commands are processed automatically!
        """
        print(f"Received command: {command_data}")
        # Sensor commands are handled automatically by the SDK
        # Custom commands can be handled here if needed
    
    print("\\n🚀 Device ready! You can now:")on that automatically:
1. Enters BLE provisioning mode on first boot or button press
2. Allows configuration of WiFi, device credentials, AND sensors via mobile app
3. Auto-detects available sensors and suggests configurations
4. Automatically starts the IoT device with configured sensors
5. Handles sensor commands from the IoT platform

No programming required - everything is configured via BLE!
"""

from cyberflySdk import CyberflyClient
import time

def main():
    """
    No-code main function - handles everything automatically!
    
    Workflow:
    1. Check if device is configured
    2. If not, enter BLE provisioning (with sensor setup)
    3. If configured, start IoT device with sensors
    4. Handle commands from IoT platform automatically
    """
    
    print("=== CyberFly No-Code IoT Device ===")
    
    # This automatically handles:
    # - BLE provisioning if not configured
    # - Sensor auto-detection and setup
    # - Device configuration
    # - Automatic restart after configuration
    client = CyberflyClient.boot(
        button_pin=0,      # Boot button to trigger setup
        long_ms=3000,      # Hold button for 3 seconds
        ble=True,          # Enable BLE provisioning
        ble_timeout=300    # 5 minutes to complete setup
    )
    
    if client is None:
        # Device was just configured and will restart
        print("Device configured - restarting...")
        return
    
    print(f"Device started: {client.device_id}")
    
    # Display configured sensors
    if hasattr(client, 'sensor_manager') and client.sensor_manager:
        status = client.get_sensor_status()
        print(f"Loaded {status['total_sensors']} sensors:")
        for sensor in status['sensors']:
            state = "✓" if sensor['enabled'] else "✗"
            alias = sensor.get('alias', sensor['sensor_id'])
            print(f"  {state} {alias} ({sensor['sensor_type']})")
    
    # Set up automatic command handling
    @client.on_message()
    def handle_commands(command_data):
        \"\"\"
        Automatically handles all sensor commands from IoT platform.
        No code needed - sensor commands are processed automatically!
        \"\"\"
        print(f"Received command: {command_data}")
        # Sensor commands are handled automatically by the SDK
        # Custom commands can be handled here if needed
    
    print("\\n🚀 Device ready! You can now:")
    print("  • Send sensor commands from the IoT platform")
    print("  • View real-time sensor data")
    print("  • Control output devices remotely")
    print("  • Monitor device status")
    
    # Main loop - automatically publishes sensor data
    last_publish = time.time()
    publish_interval = 60  # Publish every minute
    
    try:
        while True:
            # Process incoming commands
            client.check_msg()
            
            # Auto-publish sensor readings
            current_time = time.time()
            if current_time - last_publish >= publish_interval:
                try:
                    if hasattr(client, 'sensor_manager') and client.sensor_manager:
                        readings = client.read_all_sensors()
                        if readings:
                            success_count = sum(1 for r in readings if r['status'] == 'success')
                            print(f"📊 Published {success_count} sensor readings")
                            client.publish_all_sensor_readings()
                    last_publish = current_time
                except Exception as e:
                    print(f"Error publishing sensors: {e}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\\nStopping device...")
    except Exception as e:
        print(f"Device error: {e}")
        # Could implement auto-recovery here

if __name__ == "__main__":
    main()

"""
=== BLE Provisioning Protocol ===

The enhanced BLE provisioning now supports a multi-step setup process:

1. DEVICE CONFIGURATION (first step):
   Send device config JSON:
   {
     "device_id": "my-iot-device",
     "ssid": "MyWiFi", 
     "wifi_password": "password123",
     "network_id": "testnet04",
     "publicKey": "...",
     "secretKey": "..."
   }
   
   Response: {"status": "sensor_ready", "available_sensors": [...], "detected_sensors": [...]}

2. SENSOR CONFIGURATION (second step):
   Send sensor config JSON:
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
         "inputs": {"pin_no": 2},
         "enabled": true, 
         "alias": "Status LED"
       }
     ]
   }
   
   Response: {"status": "sensor_saved"} -> Device restarts

3. DEVICE OPERATION:
   After restart, device automatically:
   - Connects to WiFi
   - Loads sensor configurations  
   - Starts IoT platform connection
   - Begins handling sensor commands
   
=== Available Sensor Types ===

The system auto-detects and suggests these sensors:

• temp_internal - Internal temperature sensor (always available)
• system_info - Memory/uptime monitor (always available)  
• digital_in - Buttons, switches (requires pin_no)
• digital_out - LEDs, relays (requires pin_no)
• analog_in - Potentiometers, light sensors (requires pin_no)

Auto-detected sensors include:
• Boot button (GPIO 0)
• Status LED (GPIO 2 on ESP32, GPIO 25 on RP2040)

=== IoT Platform Commands ===

Once configured, the device automatically handles these commands:

// Read all sensors
{"sensor_command": {"action": "read"}}

// Read specific sensor  
{"sensor_command": {"action": "read", "sensor_id": "temp1"}}

// Control output device
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "led1",
    "params": {"execute_action": "toggle"}
  }
}

// Get sensor status
{"sensor_command": {"action": "status"}}
"""