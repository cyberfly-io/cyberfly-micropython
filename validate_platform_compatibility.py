"""
Platform Compatibility Validation Script
Run this on your ESP32 or RP2040 to validate platform compatibility
"""

import sys
import time

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(test_name, passed, message=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"        {message}")

def test_platform_detection():
    """Test 1: Platform Detection"""
    print_header("Test 1: Platform Detection")
    
    try:
        from cyberfly_sdk.platform_compat import detect_platform, get_platform_info
        
        platform = detect_platform()
        print_result("Detect platform", platform in ["esp32", "rp2040"], 
                    f"Detected: {platform}")
        
        info = get_platform_info()
        print_result("Get platform info", 'platform' in info,
                    f"Platform: {info.get('platform')}, ID: {info.get('unique_id')}, Freq: {info.get('freq_mhz')}MHz")
        
        return True
    except Exception as e:
        print_result("Platform detection", False, str(e))
        return False

def test_pin_control():
    """Test 2: Pin Control"""
    print_header("Test 2: Pin Control")
    
    try:
        from cyberfly_sdk.platform_compat import Pin, detect_platform
        
        platform = detect_platform()
        pin = 2 if platform == "esp32" else 25
        
        # Test output pin
        led = Pin(pin, Pin.OUT)
        print_result("Create output pin", led is not None, f"Pin {pin}")
        
        # Test value setting
        led.value(1)
        print_result("Set pin high", True, "value(1)")
        
        led.value(0)
        print_result("Set pin low", True, "value(0)")
        
        return True
    except Exception as e:
        print_result("Pin control", False, str(e))
        return False

def test_adc():
    """Test 3: ADC"""
    print_header("Test 3: ADC")
    
    try:
        from cyberfly_sdk.platform_compat import ADC, detect_platform
        
        platform = detect_platform()
        
        # Choose appropriate ADC pin
        if platform == "esp32":
            adc_pin = 34
        elif platform == "rp2040":
            adc_pin = 26
        else:
            adc_pin = 26
        
        adc = ADC(adc_pin)
        print_result("Create ADC", adc is not None, f"Pin {adc_pin}")
        
        # Read value
        value = adc.read_u16()
        print_result("Read ADC", 0 <= value <= 65535, 
                    f"Value: {value} ({value*3.3/65535:.2f}V)")
        
        return True
    except Exception as e:
        print_result("ADC", False, str(e))
        return False

def test_i2c():
    """Test 4: I2C"""
    print_header("Test 4: I2C")
    
    try:
        from cyberfly_sdk.platform_compat import I2C, detect_platform
        
        platform = detect_platform()
        
        # Choose appropriate I2C pins
        if platform == "esp32":
            scl, sda = 22, 21
        elif platform == "rp2040":
            scl, sda = 1, 0
        else:
            scl, sda = 22, 21
        
        i2c = I2C(scl=scl, sda=sda, freq=400000)
        print_result("Create I2C", i2c is not None, 
                    f"SCL={scl}, SDA={sda}, 400kHz")
        
        # Scan for devices
        devices = i2c.scan()
        print_result("Scan I2C bus", devices is not None,
                    f"Found {len(devices)} device(s): {[hex(d) for d in devices]}")
        
        return True
    except Exception as e:
        print_result("I2C", False, str(e))
        return False

def test_rtc():
    """Test 5: RTC"""
    print_header("Test 5: RTC")
    
    try:
        from cyberfly_sdk.platform_compat import RTC
        
        rtc = RTC()
        print_result("Create RTC", rtc is not None)
        
        # Set time
        rtc.datetime((2024, 1, 15, 1, 12, 30, 0, 0))
        print_result("Set RTC time", True, "2024-01-15 12:30:00")
        
        # Read time
        dt = rtc.datetime()
        print_result("Read RTC time", dt is not None,
                    f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}")
        
        return True
    except Exception as e:
        print_result("RTC", False, str(e))
        return False

def test_system_functions():
    """Test 6: System Functions"""
    print_header("Test 6: System Functions")
    
    try:
        from cyberfly_sdk.platform_compat import unique_id, freq
        
        # Test unique_id
        uid = unique_id()
        print_result("Get unique ID", uid is not None,
                    f"{len(uid)} bytes: {uid.hex()}")
        
        # Test freq
        f = freq()
        print_result("Get CPU frequency", f > 0,
                    f"{f / 1_000_000:.0f} MHz")
        
        return True
    except Exception as e:
        print_result("System functions", False, str(e))
        return False

def test_wifi():
    """Test 7: WiFi (availability check only)"""
    print_header("Test 7: WiFi Availability")
    
    try:
        from cyberfly_sdk.platform_compat import WiFi, detect_platform
        
        platform = detect_platform()
        
        wifi = WiFi()
        print_result("WiFi module available", wifi is not None)
        
        if platform == "esp32":
            print_result("WiFi support", True, "ESP32: Built-in WiFi")
        elif platform == "rp2040":
            print_result("WiFi support", True, "RP2040: Pico W only")
        
        # Note: Not actually connecting (would need credentials)
        print("        (Skipping actual connection - would need WiFi credentials)")
        
        return True
    except Exception as e:
        print_result("WiFi", False, str(e))
        return False

def test_memory():
    """Test 8: Memory Check"""
    print_header("Test 8: Memory Check")
    
    try:
        import gc
        from cyberfly_sdk.platform_compat import detect_platform
        
        platform = detect_platform()
        
        gc.collect()
        free = gc.mem_free()
        print_result("Get free memory", free > 0,
                    f"{free:,} bytes free")
        
        # Platform-specific expectations
        if platform == "esp32":
            expected = "520KB+"
        elif platform == "rp2040":
            expected = "264KB"
        else:
            expected = "Unknown"
        
        print_result("Platform memory", True,
                    f"{platform.upper()}: {expected} total RAM")
        
        return True
    except Exception as e:
        print_result("Memory check", False, str(e))
        return False

def test_imports():
    """Test 9: All Module Imports"""
    print_header("Test 9: Module Imports")
    
    modules = [
        ("cyberfly_sdk.platform_compat", "Platform compatibility"),
        ("cyberfly_sdk.cyberflySdk", "CyberflyClient"),
        ("cyberfly_sdk.shipper_utils", "Shipper utilities"),
        ("cyberfly_sdk.cntptime", "NTP time"),
        ("cyberfly_sdk.actuators.led", "LED module"),
        ("cyberfly_sdk.sensors.types.base", "Sensor base types"),
        ("cyberfly_sdk.sensors.base_sensors", "Base sensors"),
        ("cyberfly_sdk.schedule", "Scheduler"),
    ]
    
    all_passed = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print_result(description, True, module_name)
        except Exception as e:
            print_result(description, False, f"{module_name}: {e}")
            all_passed = False
    
    return all_passed

def run_all_tests():
    """Run all validation tests"""
    print_header("CYBERFLY SDK - PLATFORM COMPATIBILITY VALIDATION")
    
    print("\nPython Implementation:")
    print(f"  Name: {sys.implementation.name}")
    print(f"  Version: {'.'.join(map(str, sys.version_info[:3]))}")
    
    tests = [
        test_platform_detection,
        test_pin_control,
        test_adc,
        test_i2c,
        test_rtc,
        test_system_functions,
        test_wifi,
        test_memory,
        test_imports,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            import sys
            sys.print_exception(e)
            failed += 1
        
        time.sleep(0.5)  # Brief pause between tests
    
    # Summary
    print_header("TEST SUMMARY")
    total = passed + failed
    print(f"  Total Tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Success Rate: {passed/total*100:.1f}%")
    
    if failed == 0:
        print("\n  ✓ All tests passed! Platform compatibility is working correctly.")
    else:
        print(f"\n  ✗ {failed} test(s) failed. Check the output above for details.")
    
    print("=" * 60)

# Run validation
if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import sys
        sys.print_exception(e)
