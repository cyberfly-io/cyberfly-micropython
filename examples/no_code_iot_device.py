"""
CyberFly MicroPython No-Code IoT Device

This is a no-code solution that automatically:
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
        """Automatically handles all sensor commands from IoT platform."""
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