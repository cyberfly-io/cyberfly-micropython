#!/usr/bin/env python3
"""
GPIO Pin Status Dashboard Example

This example demonstrates how to monitor GPIO pin states and send them to the dashboard
for real-time visualization. The pin status sensor can monitor multiple pins simultaneously
and report their current values, making it perfect for debugging and monitoring.

Features:
- Monitor multiple GPIO pins simultaneously  
- Auto-detect pin configuration (input/output)
- Support for pull-up/pull-down configuration
- Real-time dashboard updates
- Error handling for unavailable pins
"""

import time
from cyberflySdk import CyberflyClient

# Device configuration
DEVICE_CONFIG = {
    "device_id": "pin_monitor_001",
    "key_pair": {"publicKey": "your_public_key", "secretKey": "your_secret_key"},
    "ssid": "your_wifi_ssid", 
    "wifi_password": "your_wifi_password",
    "network_id": "testnet04"
}

def setup_pin_monitoring(client):
    """Set up GPIO pin monitoring sensors."""
    
    print("Setting up GPIO pin monitoring...")
    
    # Example 1: Monitor common ESP32 GPIO pins
    print("Adding ESP32 GPIO pin monitor...")
    client.add_sensor(
        sensor_id="esp32_gpio_status",
        sensor_type="pin_status",
        inputs={
            "pins": [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23],
            "mode": "auto",  # Auto-detect input/output
            "pull_mode": "none"  # No pull resistors
        },
        alias="ESP32 GPIO Monitor"
    )
    
    # Example 2: Monitor specific input pins with pull-up
    print("Adding input pin monitor with pull-up...")
    client.add_sensor(
        sensor_id="input_pins",
        sensor_type="pin_status", 
        inputs={
            "pins": [0, 35, 36, 39],  # Boot button and ADC pins
            "mode": "input",
            "pull_mode": "up"
        },
        alias="Input Pins with Pull-up"
    )
    
    # Example 3: Monitor output pins
    print("Adding output pin monitor...")
    client.add_sensor(
        sensor_id="output_pins",
        sensor_type="pin_status",
        inputs={
            "pins": [2, 4, 16, 17],  # Common LED pins  
            "mode": "output"
        },
        alias="Output Pin Monitor"
    )
    
    # Example 4: Single pin monitor
    print("Adding single pin monitor...")
    client.add_sensor(
        sensor_id="led_pin",
        sensor_type="pin_status",
        inputs={
            "pin_no": 2,  # Built-in LED on many boards
            "mode": "output"
        },
        alias="Built-in LED Pin"
    )
    
    print("Pin monitoring sensors configured!")

def demonstrate_pin_control(client):
    """Demonstrate controlling output pins."""
    
    print("\n=== Pin Control Demonstration ===")
    
    try:
        # Read current pin status
        print("Reading pin status...")
        pin_reading = client.read_sensor("output_pins")
        
        if pin_reading.get('status') == 'success':
            print("Output pin status:")
            pins_data = pin_reading['data']['pins']
            for pin_key, pin_info in pins_data.items():
                if pin_info.get('mode') == 'output' and pin_info.get('configured'):
                    pin_num = pin_info['pin_number']
                    current_state = pin_info.get('state', 'UNKNOWN')
                    print(f"  Pin {pin_num}: {current_state}")
        
        # You can add pin control functionality here
        # For now, just demonstrate reading
        
    except Exception as e:
        print(f"Error in pin control demo: {e}")

def main():
    """Main application demonstrating pin status monitoring."""
    
    print("🔌 GPIO Pin Status Dashboard Example")
    print("=" * 50)
    
    # Initialize CyberFly client
    client = CyberflyClient(
        device_id=DEVICE_CONFIG["device_id"],
        key_pair=DEVICE_CONFIG["key_pair"],
        ssid=DEVICE_CONFIG["ssid"],
        wifi_password=DEVICE_CONFIG["wifi_password"],
        network_id=DEVICE_CONFIG["network_id"]
    )
    
    print(f"Initialized CyberFly client for device: {DEVICE_CONFIG['device_id']}")
    
    # Set up pin monitoring
    setup_pin_monitoring(client)
    
    # Set up command handler
    @client.on_message()
    def handle_commands(command_data):
        """Handle commands from IoT platform."""
        print(f"Received command: {command_data}")
        
        # Pin control commands can be handled here
        if 'pin_command' in command_data:
            pin_cmd = command_data['pin_command']
            action = pin_cmd.get('action')
            
            if action == 'read_status':
                # Publish current pin status
                success = client.publish_pin_status()
                print(f"Pin status published: {success}")
            
            elif action == 'dashboard_update':
                # Publish complete dashboard summary
                success = client.publish_dashboard_summary()
                print(f"Dashboard summary published: {success}")
    
    # Display sensor status
    print("\n📊 Configured Pin Monitors:")
    status = client.get_sensor_status()
    for sensor_id in status.get('sensor_list', []):
        sensor_info = client.get_sensor_status(sensor_id)
        state = "✓" if sensor_info.get('enabled') else "✗"
        alias = sensor_info.get('alias', sensor_id)
        sensor_type = sensor_info.get('sensor_type', 'unknown')
        print(f"  {state} {alias} ({sensor_type})")
    
    # Demonstrate pin control
    demonstrate_pin_control(client)
    
    print("\n🚀 Pin monitoring active! Dashboard commands:")
    print("  • Send pin status to dashboard:")
    print('    {"pin_command": {"action": "read_status"}}')
    print("  • Send complete dashboard update:")
    print('    {"pin_command": {"action": "dashboard_update"}}')
    print("  • Read specific pin sensor:")
    print('    {"sensor_command": {"action": "read", "sensor_id": "esp32_gpio_status"}}')
    
    # Main monitoring loop
    last_pin_publish = time.time()
    last_dashboard_publish = time.time()
    pin_publish_interval = 10  # Publish pin status every 10 seconds
    dashboard_publish_interval = 30  # Publish full dashboard every 30 seconds
    
    try:
        while True:
            # Check for incoming commands
            client.check_msg()
            
            current_time = time.time()
            
            # Periodically publish pin status
            if current_time - last_pin_publish >= pin_publish_interval:
                try:
                    success = client.publish_pin_status()
                    print(f"[{time.localtime()}] Pin status published: {success}")
                    last_pin_publish = current_time
                except Exception as e:
                    print(f"Error publishing pin status: {e}")
            
            # Periodically publish full dashboard
            if current_time - last_dashboard_publish >= dashboard_publish_interval:
                try:
                    success = client.publish_dashboard_summary()
                    print(f"[{time.localtime()}] Dashboard summary published: {success}")
                    last_dashboard_publish = current_time
                except Exception as e:
                    print(f"Error publishing dashboard summary: {e}")
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🛑 Pin monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error in main loop: {e}")
    
    print("Pin status monitoring example completed.")

def test_pin_status_commands():
    """Test function showing pin status command examples."""
    
    print("\n=== Pin Status Command Examples ===")
    
    commands = [
        {
            "title": "Read all pin status",
            "command": {"sensor_command": {"action": "read", "sensor_id": "esp32_gpio_status"}}
        },
        {
            "title": "Read input pins only", 
            "command": {"sensor_command": {"action": "read", "sensor_id": "input_pins"}}
        },
        {
            "title": "Read output pins only",
            "command": {"sensor_command": {"action": "read", "sensor_id": "output_pins"}}
        },
        {
            "title": "Publish pin status to dashboard",
            "command": {"pin_command": {"action": "read_status"}}
        },
        {
            "title": "Publish complete dashboard update",
            "command": {"pin_command": {"action": "dashboard_update"}}
        },
        {
            "title": "Get sensor status",
            "command": {"sensor_command": {"action": "status"}}
        }
    ]
    
    for cmd_info in commands:
        print(f"\n{cmd_info['title']}:")
        print(f"  {cmd_info['command']}")

if __name__ == "__main__":
    main()
    test_pin_status_commands()