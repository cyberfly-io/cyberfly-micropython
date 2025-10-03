"""
Platform Compatibility Examples
Demonstrates how to write code that works on both ESP32 and RP2040
"""

import time
import gc


def example_1_platform_detection():
    """Example 1: Detect which platform we're running on"""
    print("\n=== Example 1: Platform Detection ===")
    
    from cyberfly_sdk.platform_compat import detect_platform, get_platform_info
    
    # Simple detection
    platform = detect_platform()
    print(f"Detected platform: {platform}")
    
    # Detailed information
    info = get_platform_info()
    print(f"Platform: {info['platform']}")
    print(f"Unique ID: {info['unique_id']}")
    print(f"CPU Frequency: {info['freq_mhz']} MHz")


def example_2_led_control():
    """Example 2: Control an LED on any platform"""
    print("\n=== Example 2: LED Control ===")
    
    from cyberfly_sdk.platform_compat import Pin, detect_platform
    
    platform = detect_platform()
    
    # Different platforms have LED on different pins
    if platform == "esp32":
        led_pin = 2  # Most ESP32 boards
    elif platform == "rp2040":
        led_pin = 25  # Raspberry Pi Pico
    else:
        led_pin = 2  # Default
    
    print(f"Using LED on pin {led_pin}")
    led = Pin(led_pin, Pin.OUT)
    
    # Blink LED 5 times
    for i in range(5):
        led.value(1)
        print(f"  Blink {i+1}: ON")
        time.sleep(0.5)
        led.value(0)
        print(f"  Blink {i+1}: OFF")
        time.sleep(0.5)
    
    print("LED test complete!")


def example_3_adc_reading():
    """Example 3: Read analog values (platform-aware)"""
    print("\n=== Example 3: ADC Reading ===")
    
    from cyberfly_sdk.platform_compat import ADC, detect_platform
    
    platform = detect_platform()
    
    # Choose appropriate ADC pin
    if platform == "esp32":
        adc_pin = 34  # Common ADC pin on ESP32
        print(f"Using ESP32 ADC pin: GPIO {adc_pin}")
    elif platform == "rp2040":
        adc_pin = 26  # ADC0 on RP2040
        print(f"Using RP2040 ADC pin: GPIO {adc_pin} (ADC0)")
        print("Note: RP2040 only supports ADC on pins 26, 27, 28")
    else:
        adc_pin = 26
        print(f"Using default ADC pin: {adc_pin}")
    
    try:
        # Platform compatibility layer handles the differences
        adc = ADC(adc_pin)
        
        # Read 10 samples
        print("Reading 10 ADC samples...")
        for i in range(10):
            value = adc.read_u16()  # 0-65535
            voltage = (value / 65535) * 3.3
            print(f"  Sample {i+1}: {value:5d} (raw) = {voltage:.2f}V")
            time.sleep(0.1)
        
        print("ADC test complete!")
        
    except Exception as e:
        print(f"ADC error: {e}")
        print("Make sure you're using a valid ADC pin for your platform")


def example_4_i2c_scan():
    """Example 4: I2C device scanning"""
    print("\n=== Example 4: I2C Scan ===")
    
    from cyberfly_sdk.platform_compat import I2C, detect_platform
    
    platform = detect_platform()
    
    # Platform-specific pin recommendations
    if platform == "esp32":
        scl, sda = 22, 21  # Common ESP32 I2C pins
        print(f"Using ESP32 I2C pins: SDA={sda}, SCL={scl}")
    elif platform == "rp2040":
        scl, sda = 1, 0  # I2C0 on RP2040
        print(f"Using RP2040 I2C0 pins: SDA={sda}, SCL={scl}")
        print("Note: RP2040 I2C pins are fixed to specific GPIO")
    else:
        scl, sda = 22, 21
    
    try:
        # Platform compatibility layer handles the initialization
        i2c = I2C(scl=scl, sda=sda, freq=400000)
        
        print("Scanning I2C bus...")
        devices = i2c.scan()
        
        if devices:
            print(f"Found {len(devices)} device(s):")
            for addr in devices:
                print(f"  - 0x{addr:02X} ({addr})")
        else:
            print("No I2C devices found")
        
        print("I2C scan complete!")
        
    except Exception as e:
        print(f"I2C error: {e}")
        print("Make sure I2C devices are connected and pins are correct")


def example_5_wifi_connection():
    """Example 5: WiFi connection (if available)"""
    print("\n=== Example 5: WiFi Connection ===")
    
    from cyberfly_sdk.platform_compat import WiFi, detect_platform
    
    platform = detect_platform()
    
    # Check WiFi availability
    if platform == "esp32":
        print("ESP32: WiFi available")
    elif platform == "rp2040":
        print("RP2040: WiFi only on Pico W variant")
    
    # Replace with your WiFi credentials for testing
    SSID = "YourSSID"
    PASSWORD = "YourPassword"
    
    if SSID == "YourSSID":
        print("Skipping WiFi test (credentials not configured)")
        print("To test WiFi, update SSID and PASSWORD in this example")
        return
    
    try:
        wifi = WiFi()
        print(f"Connecting to {SSID}...")
        
        wifi.connect(SSID, PASSWORD, timeout_s=10)
        
        if wifi.isconnected():
            config = wifi.ifconfig()
            print(f"Connected! IP: {config[0]}")
            print(f"Subnet: {config[1]}")
            print(f"Gateway: {config[2]}")
            print(f"DNS: {config[3]}")
        else:
            print("Connection failed")
        
    except Exception as e:
        print(f"WiFi error: {e}")


def example_6_rtc_time():
    """Example 6: Real-time clock"""
    print("\n=== Example 6: RTC Time ===")
    
    from cyberfly_sdk.platform_compat import RTC
    
    try:
        rtc = RTC()
        
        # Get current time
        dt = rtc.datetime()
        print(f"Current RTC time: {dt}")
        print(f"Formatted: {dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}")
        
        # Set time (example: 2024-01-15 12:30:00)
        print("\nSetting RTC time to 2024-01-15 12:30:00...")
        rtc.datetime((2024, 1, 15, 1, 12, 30, 0, 0))
        
        # Read back
        dt = rtc.datetime()
        print(f"New RTC time: {dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}")
        
        print("RTC test complete!")
        
    except Exception as e:
        print(f"RTC error: {e}")


def example_7_platform_adaptation():
    """Example 7: Adapting code to platform capabilities"""
    print("\n=== Example 7: Platform Adaptation ===")
    
    from cyberfly_sdk.platform_compat import detect_platform
    
    platform = detect_platform()
    print(f"Platform: {platform}")
    
    # Adapt features based on platform
    features = {
        "gpio": True,
        "pwm": True,
        "uart": True,
        "rtc": True,
    }
    
    if platform == "esp32":
        features.update({
            "wifi": True,
            "bluetooth": True,
            "adc_pins": "Multiple (GPIO 32-39 on ESP32)",
            "i2c_flexible": True,
            "deep_sleep": "Excellent (μA range)",
            "ram": "High (520KB+)",
        })
    elif platform == "rp2040":
        features.update({
            "wifi": "Pico W only",
            "bluetooth": False,
            "adc_pins": "Limited (GPIO 26-28 only)",
            "i2c_flexible": False,
            "deep_sleep": "Good (mA range)",
            "ram": "Limited (264KB)",
            "pio": True,  # Unique to RP2040
        })
    
    print("\nPlatform capabilities:")
    for feature, value in features.items():
        if isinstance(value, bool):
            status = "✓" if value else "✗"
            print(f"  {status} {feature}")
        else:
            print(f"  • {feature}: {value}")


def example_8_memory_management():
    """Example 8: Memory management on different platforms"""
    print("\n=== Example 8: Memory Management ===")
    
    from cyberfly_sdk.platform_compat import detect_platform
    
    platform = detect_platform()
    
    # Check memory
    free_before = gc.mem_free()
    print(f"Free memory before: {free_before:,} bytes")
    
    # Allocate some memory
    data = bytearray(10000)
    free_after = gc.mem_free()
    print(f"Free memory after allocating 10KB: {free_after:,} bytes")
    print(f"Memory used: {free_before - free_after:,} bytes")
    
    # Clean up
    del data
    gc.collect()
    free_final = gc.mem_free()
    print(f"Free memory after cleanup: {free_final:,} bytes")
    
    # Platform-specific advice
    if platform == "esp32":
        print("\nESP32 has plenty of RAM (520KB+)")
        print("You can use larger buffers and data structures")
    elif platform == "rp2040":
        print("\nRP2040 has limited RAM (264KB)")
        print("Be mindful of memory usage:")
        print("  - Use smaller buffers")
        print("  - Call gc.collect() regularly")
        print("  - Avoid large string concatenations")
        print("  - Use generators instead of lists where possible")


def example_9_cyberfly_client():
    """Example 9: Using Cyberfly Client (cross-platform)"""
    print("\n=== Example 9: Cyberfly Client ===")
    
    from cyberfly_sdk.platform_compat import detect_platform
    
    platform = detect_platform()
    print(f"Platform: {platform}")
    
    # Note: This is just to show the API, not actually connecting
    print("\nExample client initialization:")
    print("""
    from cyberfly_sdk import CyberflyClient
    
    client = CyberflyClient(
        ssid="YourSSID",
        password="YourPassword",
        api_key="your_api_key",
        device_id="my_device_01"
    )
    
    # Works on both ESP32 and RP2040!
    client.boot()
    
    # Add sensors (examples)
    from cyberfly_sdk.sensors.base_sensors import DHTSensor
    dht = DHTSensor(sensor_id="temp1", pin=4)
    client.add_sensor(dht)
    
    # Start monitoring
    client.start()
    """)
    
    print("The Cyberfly SDK handles all platform differences automatically!")


def run_all_examples():
    """Run all examples"""
    print("=" * 60)
    print("PLATFORM COMPATIBILITY EXAMPLES")
    print("=" * 60)
    
    examples = [
        example_1_platform_detection,
        example_2_led_control,
        example_3_adc_reading,
        example_4_i2c_scan,
        example_5_wifi_connection,
        example_6_rtc_time,
        example_7_platform_adaptation,
        example_8_memory_management,
        example_9_cyberfly_client,
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            example()
        except Exception as e:
            print(f"\nExample {i} error: {e}")
            import sys
            sys.print_exception(e)
        
        if i < len(examples):
            print("\n" + "-" * 60)
            time.sleep(1)  # Brief pause between examples
    
    print("\n" + "=" * 60)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 60)


# Run specific example or all examples
if __name__ == "__main__":
    # Run all examples
    run_all_examples()
    
    # Or run individual examples:
    # example_1_platform_detection()
    # example_2_led_control()
    # example_3_adc_reading()
    # etc.
