#!/usr/bin/env python3
"""
Test Script for read_pin_status Command

This script demonstrates how to test the read_pin_status command
for IoT platform integration. It shows both manual testing and
automated testing scenarios.
"""

import json
import time

def test_read_pin_status_command():
    """Test the read_pin_status command structure and responses."""
    
    print("=" * 60)
    print("Testing read_pin_status Command for IoT Platform")
    print("=" * 60)
    
    # Test Case 1: Basic read_pin_status command
    print("\n1. Basic read_pin_status command (auto-creation):")
    command1 = {
        "sensor_command": {
            "action": "read_pin_status"
        }
    }
    print(json.dumps(command1, indent=2))
    print("Expected: Auto-creates 'pin_status' sensor with default pins")
    
    # Test Case 2: read_pin_status with specific sensor_id
    print("\n2. read_pin_status with custom sensor ID:")
    command2 = {
        "sensor_command": {
            "action": "read_pin_status",
            "sensor_id": "gpio_monitor"
        }
    }
    print(json.dumps(command2, indent=2))
    print("Expected: Reads 'gpio_monitor' sensor or creates if not exists")
    
    # Test Case 3: Expected success response format
    print("\n3. Expected Success Response Format:")
    success_response = {
        "status": "success",
        "action": "read_pin_status",
        "sensor_id": "pin_status",
        "timestamp": int(time.time()),
        "data": {
            "total_pins": 15,
            "configured_pins": 12,
            "error_pins": 3,
            "timestamp": int(time.time()),
            "pins": {
                "pin_0": {
                    "pin_number": 0,
                    "mode": "input",
                    "value": 1,
                    "state": "HIGH",
                    "status": "success",
                    "configured": True
                },
                "pin_2": {
                    "pin_number": 2,
                    "mode": "output",
                    "value": 0,
                    "state": "LOW",
                    "status": "success",
                    "configured": True
                }
            }
        }
    }
    print(json.dumps(success_response, indent=2))
    
    # Test Case 4: Expected error response format
    print("\n4. Expected Error Response (sensor not found, auto-create failed):")
    error_response = {
        "status": "error",
        "error": "Failed to create pin status sensor",
        "action": "read_pin_status"
    }
    print(json.dumps(error_response, indent=2))
    
    # Test Case 5: Full IoT platform command with authentication
    print("\n5. Full IoT Platform Command Structure:")
    full_command = {
        "device_exec": json.dumps({
            "sensor_command": {
                "action": "read_pin_status"
            },
            "expiry_time": int(time.time()) + 300,  # 5 minutes from now
            "response_topic": "device_001/response"
        }),
        "pubKey": "your_public_key_here",
        "sig": "signature_here"
    }
    print(json.dumps(full_command, indent=2))
    
    print("\n" + "=" * 60)
    print("Test Commands Completed")
    print("=" * 60)

def simulate_iot_platform_flow():
    """Simulate the complete IoT platform request/response flow."""
    
    print("\n" + "=" * 60)
    print("Simulated IoT Platform Request/Response Flow")
    print("=" * 60)
    
    # Step 1: IoT Platform sends command
    print("\nStep 1: IoT Platform sends command to device")
    print("-" * 60)
    platform_command = {
        "sensor_command": {
            "action": "read_pin_status"
        }
    }
    print("Command sent:")
    print(json.dumps(platform_command, indent=2))
    
    # Step 2: Device processes command
    print("\nStep 2: Device processes command")
    print("-" * 60)
    print("• Device receives command via MQTT")
    print("• Authenticates command signature")
    print("• Checks if pin_status sensor exists")
    print("• If not exists: Auto-creates with default pins [0,2,4,5,12,13,14,15,16,17,18,19,21,22,23]")
    print("• Reads GPIO pin states")
    print("• Formats response data")
    
    # Step 3: Device sends response
    print("\nStep 3: Device sends response to platform")
    print("-" * 60)
    device_response = {
        "status": "success",
        "action": "read_pin_status",
        "sensor_id": "pin_status",
        "timestamp": int(time.time()),
        "data": {
            "total_pins": 15,
            "configured_pins": 13,
            "error_pins": 2,
            "pins": {
                "pin_0": {"pin_number": 0, "mode": "input", "value": 1, "state": "HIGH", "status": "success"},
                "pin_2": {"pin_number": 2, "mode": "output", "value": 0, "state": "LOW", "status": "success"},
                "pin_4": {"pin_number": 4, "mode": "input", "value": 1, "state": "HIGH", "status": "success"},
                "pin_5": {"pin_number": 5, "mode": "input", "value": 0, "state": "LOW", "status": "success"}
            }
        }
    }
    print("Response data:")
    print(json.dumps(device_response, indent=2))
    
    # Step 4: Platform displays data
    print("\nStep 4: IoT Platform displays data on dashboard")
    print("-" * 60)
    print("Dashboard Updates:")
    print(f"  • Total Pins Monitored: {device_response['data']['total_pins']}")
    print(f"  • Successfully Configured: {device_response['data']['configured_pins']}")
    print(f"  • Configuration Errors: {device_response['data']['error_pins']}")
    print("\n  Pin States:")
    for pin_key, pin_info in device_response['data']['pins'].items():
        print(f"    • Pin {pin_info['pin_number']}: {pin_info['state']} ({pin_info['mode']})")
    
    print("\n" + "=" * 60)

def test_command_variations():
    """Test various command variations and edge cases."""
    
    print("\n" + "=" * 60)
    print("Command Variations and Edge Cases")
    print("=" * 60)
    
    variations = [
        {
            "name": "Default auto-creation",
            "command": {"sensor_command": {"action": "read_pin_status"}},
            "description": "Creates pin_status sensor with default pins"
        },
        {
            "name": "Custom sensor ID",
            "command": {"sensor_command": {"action": "read_pin_status", "sensor_id": "esp32_gpio"}},
            "description": "Creates esp32_gpio sensor if not exists"
        },
        {
            "name": "Pre-configured sensor",
            "command": {"sensor_command": {"action": "read_pin_status", "sensor_id": "my_pins"}},
            "description": "Reads existing my_pins sensor (no auto-creation needed)"
        },
        {
            "name": "With response topic",
            "command": {
                "sensor_command": {"action": "read_pin_status"},
                "response_topic": "device_001/response"
            },
            "description": "Sends response to specific MQTT topic"
        }
    ]
    
    for i, variation in enumerate(variations, 1):
        print(f"\n{i}. {variation['name']}")
        print("-" * 60)
        print(f"Description: {variation['description']}")
        print("Command:")
        print(json.dumps(variation['command'], indent=2))
    
    print("\n" + "=" * 60)

def compare_with_other_commands():
    """Compare read_pin_status with other similar commands."""
    
    print("\n" + "=" * 60)
    print("Command Comparison")
    print("=" * 60)
    
    commands = [
        {
            "name": "read_pin_status",
            "command": {"sensor_command": {"action": "read_pin_status"}},
            "features": [
                "✓ Auto-creates sensor if needed",
                "✓ Returns structured pin data",
                "✓ Includes pin configuration status",
                "✓ Synchronous response",
                "✓ No pre-configuration required"
            ]
        },
        {
            "name": "read_sensor",
            "command": {"sensor_command": {"action": "read_sensor", "sensor_id": "gpio_monitor"}},
            "features": [
                "✗ Requires pre-configured sensor",
                "✓ Returns sensor reading data",
                "✓ Generic format",
                "✓ Synchronous response",
                "✗ Must configure sensor first"
            ]
        },
        {
            "name": "pin_command: read_status",
            "command": {"pin_command": {"action": "read_status"}},
            "features": [
                "✓ Auto-creates if needed",
                "✓ Publishes to MQTT topic",
                "✓ Dashboard-specific format",
                "✗ Asynchronous (no direct response)",
                "✓ One-way publish"
            ]
        }
    ]
    
    for cmd_info in commands:
        print(f"\n{cmd_info['name']}:")
        print("-" * 60)
        print("Command:")
        print(json.dumps(cmd_info['command'], indent=2))
        print("\nFeatures:")
        for feature in cmd_info['features']:
            print(f"  {feature}")
    
    print("\n" + "=" * 60)

def print_integration_examples():
    """Print integration code examples."""
    
    print("\n" + "=" * 60)
    print("Integration Code Examples")
    print("=" * 60)
    
    print("\n1. Python Client Example:")
    print("-" * 60)
    print("""
import json
from cyberflySdk import CyberflyClient

# Initialize client
client = CyberflyClient(
    device_id="device_001",
    key_pair={"publicKey": "...", "secretKey": "..."},
    ssid="WiFi_SSID",
    wifi_password="password",
    network_id="testnet04"
)

# Handler for read_pin_status command
@client.on_message()
def handle_commands(command_data):
    if 'sensor_command' in command_data:
        sensor_cmd = command_data['sensor_command']
        
        if sensor_cmd.get('action') == 'read_pin_status':
            print("Received read_pin_status command")
            # Command is automatically processed by SDK
            # Response is sent back to platform
            
            # Optional: Log the event
            print(f"Pin status requested at {time.time()}")

# Main loop
while True:
    client.check_msg()
    time.sleep(0.1)
""")
    
    print("\n2. IoT Platform API Example:")
    print("-" * 60)
    print("""
// Send command to device via platform API
fetch('https://iot-platform.com/api/device/device_001/command', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        sensor_command: {
            action: 'read_pin_status'
        },
        expiry_time: Date.now() + 300000  // 5 minutes
    })
})
.then(response => response.json())
.then(data => {
    if (data.status === 'success') {
        console.log('Total pins:', data.data.total_pins);
        console.log('Configured pins:', data.data.configured_pins);
        
        // Update dashboard
        updatePinDisplay(data.data.pins);
    }
})
.catch(error => console.error('Error:', error));
""")
    
    print("\n3. MQTT Direct Publish Example:")
    print("-" * 60)
    print("""
import paho.mqtt.client as mqtt
import json

# MQTT client setup
client = mqtt.Client()
client.connect("mqtt.iot-platform.com", 1883, 60)

# Send read_pin_status command
command = {
    "sensor_command": {
        "action": "read_pin_status"
    }
}

client.publish("device_001/commands", json.dumps(command))

# Subscribe to response
def on_message(client, userdata, message):
    response = json.loads(message.payload)
    if response.get('action') == 'read_pin_status':
        print(f"Received pin status: {response['data']}")

client.subscribe("device_001/response")
client.on_message = on_message
client.loop_forever()
""")
    
    print("\n" + "=" * 60)

def main():
    """Run all test demonstrations."""
    
    print("\n" + "=" * 70)
    print(" " * 15 + "read_pin_status Command Test Suite")
    print("=" * 70)
    
    # Run all test sections
    test_read_pin_status_command()
    simulate_iot_platform_flow()
    test_command_variations()
    compare_with_other_commands()
    print_integration_examples()
    
    print("\n" + "=" * 70)
    print("All Tests Completed Successfully!")
    print("=" * 70)
    print("\nNext Steps:")
    print("  1. Deploy firmware to device")
    print("  2. Send test command from IoT platform")
    print("  3. Verify response data in dashboard")
    print("  4. Monitor pin states in real-time")
    print("\nDocumentation:")
    print("  • Command Reference: READ_PIN_STATUS_COMMAND.md")
    print("  • Quick Start: PIN_STATUS_QUICK_START.md")
    print("  • Setup Guide: NO_CODE_SETUP.md")
    print("=" * 70)

if __name__ == "__main__":
    main()