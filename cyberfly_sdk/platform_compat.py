"""
Platform compatibility module for ESP32 and RP2040.
Provides unified API for platform-specific features.
"""

import sys

# Detect platform
def detect_platform():
    """Detect the current platform (ESP32, RP2040, or other)."""
    try:
        impl = sys.implementation
        if hasattr(impl, 'name'):
            impl_name = impl.name.lower()
            # Check for specific platform
            try:
                import machine
                if hasattr(machine, 'unique_id'):
                    uid = machine.unique_id()
                    # ESP32 typically has 6-byte unique ID
                    # RP2040 typically has 8-byte unique ID
                    if len(uid) == 8:
                        return 'rp2040'
                    elif len(uid) == 6:
                        return 'esp32'
            except:
                pass
        return 'unknown'
    except:
        return 'unknown'

PLATFORM = detect_platform()

# Platform-specific imports with fallbacks
try:
    import machine
    HAS_MACHINE = True
except ImportError:
    HAS_MACHINE = False
    print("[WARN] machine module not available")

try:
    import network
    HAS_NETWORK = True
except ImportError:
    HAS_NETWORK = False
    print("[WARN] network module not available")

# Pin management
class Pin:
    """Platform-compatible Pin wrapper."""
    IN = 0
    OUT = 1
    PULL_UP = 2
    PULL_DOWN = 3
    
    def __init__(self, pin, mode=None, pull=None):
        if HAS_MACHINE:
            try:
                # ESP32 and RP2040 have different Pin APIs
                from machine import Pin as MachinePin
                if mode is not None:
                    if pull is not None:
                        self._pin = MachinePin(pin, mode, pull)
                    else:
                        self._pin = MachinePin(pin, mode)
                else:
                    self._pin = MachinePin(pin)
            except Exception as e:
                print(f"[WARN] Pin init failed: {e}")
                self._pin = None
        else:
            self._pin = None
        self.pin_num = pin
        self._value = 0
    
    def value(self, val=None):
        if self._pin:
            try:
                return self._pin.value(val) if val is not None else self._pin.value()
            except:
                pass
        # Fallback
        if val is not None:
            self._value = val
        return self._value
    
    def on(self):
        return self.value(1)
    
    def off(self):
        return self.value(0)

# ADC (Analog-to-Digital Converter)
class ADC:
    """Platform-compatible ADC wrapper."""
    
    def __init__(self, pin):
        self.pin_num = pin if isinstance(pin, int) else getattr(pin, 'pin_num', 0)
        if HAS_MACHINE:
            try:
                from machine import ADC as MachineADC, Pin as MachinePin
                # ESP32: ADC can take pin number or Pin object
                # RP2040: ADC requires specific pins (26-28 for ADC0-2)
                if PLATFORM == 'rp2040':
                    # RP2040 ADC pins: 26 (ADC0), 27 (ADC1), 28 (ADC2)
                    if self.pin_num >= 26 and self.pin_num <= 28:
                        self._adc = MachineADC(self.pin_num)
                    else:
                        # Try to create ADC anyway, let it fail if invalid
                        self._adc = MachineADC(self.pin_num)
                else:
                    # ESP32 supports various ADC pins
                    try:
                        self._adc = MachineADC(MachinePin(self.pin_num))
                    except:
                        self._adc = MachineADC(self.pin_num)
            except Exception as e:
                print(f"[WARN] ADC init failed: {e}")
                self._adc = None
        else:
            self._adc = None
    
    def read_u16(self):
        """Read 16-bit ADC value (0-65535)."""
        if self._adc:
            try:
                return self._adc.read_u16()
            except Exception as e:
                print(f"[WARN] ADC read failed: {e}")
        return 32768  # Mid-range fallback
    
    def read(self):
        """Read raw ADC value (ESP32: 0-4095, RP2040: 0-65535)."""
        if self._adc:
            try:
                if hasattr(self._adc, 'read'):
                    return self._adc.read()
                else:
                    # Convert 16-bit to 12-bit for compatibility
                    return self.read_u16() >> 4
            except:
                pass
        return 2048  # Mid-range fallback

# I2C
class I2C:
    """Platform-compatible I2C wrapper."""
    
    def __init__(self, id=0, scl=None, sda=None, freq=400000):
        self.id = id
        self.scl = scl
        self.sda = sda
        self.freq = freq
        if HAS_MACHINE:
            try:
                from machine import I2C as MachineI2C, Pin as MachinePin
                if PLATFORM == 'rp2040':
                    # RP2040: I2C(0) or I2C(1)
                    if scl is not None and sda is not None:
                        self._i2c = MachineI2C(id, scl=MachinePin(scl), sda=MachinePin(sda), freq=freq)
                    else:
                        self._i2c = MachineI2C(id, freq=freq)
                else:
                    # ESP32: I2C(-1) for software I2C
                    if scl is not None and sda is not None:
                        self._i2c = MachineI2C(id, scl=MachinePin(scl), sda=MachinePin(sda), freq=freq)
                    else:
                        self._i2c = MachineI2C(id, freq=freq)
            except Exception as e:
                print(f"[WARN] I2C init failed: {e}, trying SoftI2C")
                try:
                    from machine import SoftI2C, Pin as MachinePin
                    if scl is not None and sda is not None:
                        self._i2c = SoftI2C(scl=MachinePin(scl), sda=MachinePin(sda), freq=freq)
                    else:
                        self._i2c = None
                except:
                    self._i2c = None
        else:
            self._i2c = None
    
    def scan(self):
        if self._i2c:
            try:
                return self._i2c.scan()
            except:
                pass
        return []
    
    def readfrom_mem(self, addr, reg, nbytes):
        if self._i2c:
            try:
                return self._i2c.readfrom_mem(addr, reg, nbytes)
            except:
                pass
        return b'\x00' * nbytes
    
    def writeto_mem(self, addr, reg, data):
        if self._i2c:
            try:
                self._i2c.writeto_mem(addr, reg, data)
            except:
                pass

# SoftI2C alias
SoftI2C = I2C

# Time pulse measurement
def time_pulse_us(pin, pulse_level, timeout_us=1000000):
    """Platform-compatible time_pulse_us."""
    if HAS_MACHINE:
        try:
            from machine import time_pulse_us as machine_time_pulse_us
            return machine_time_pulse_us(pin, pulse_level, timeout_us)
        except:
            pass
    return -1  # Timeout fallback

# Reset function
def reset():
    """Platform-compatible reset."""
    if HAS_MACHINE:
        try:
            import machine
            machine.reset()
        except:
            pass
    print("[INFO] Reset not available, please manually reset device")

# RTC (Real-Time Clock)
class RTC:
    """Platform-compatible RTC wrapper."""
    
    def __init__(self):
        if HAS_MACHINE:
            try:
                import machine
                self._rtc = machine.RTC()
            except:
                self._rtc = None
        else:
            self._rtc = None
    
    def datetime(self, datetimetuple=None):
        """Get or set RTC datetime.
        
        Format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
        """
        if self._rtc:
            try:
                if datetimetuple is not None:
                    # Both ESP32 and RP2040 use 8-tuple format
                    return self._rtc.datetime(datetimetuple)
                else:
                    return self._rtc.datetime()
            except Exception as e:
                print(f"[WARN] RTC datetime failed: {e}")
        # Fallback: return epoch time as tuple
        import time
        t = time.localtime()
        return (t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0)

# WiFi connection
class WiFi:
    """Platform-compatible WiFi wrapper."""
    
    @staticmethod
    def connect(ssid, password, timeout=30):
        """Connect to WiFi network."""
        if not HAS_NETWORK:
            print("[ERROR] network module not available")
            return False
        
        try:
            import network
            import time
            
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            
            if wlan.isconnected():
                print("[INFO] Already connected to WiFi")
                return True
            
            print(f"[INFO] Connecting to WiFi: {ssid}")
            wlan.connect(ssid, password)
            
            # Wait for connection
            attempts = 0
            while not wlan.isconnected() and attempts < timeout:
                time.sleep(1)
                attempts += 1
                if attempts % 5 == 0:
                    print(f"[INFO] Waiting for WiFi connection... ({attempts}s)")
            
            if wlan.isconnected():
                print(f"[INFO] WiFi connected: {wlan.ifconfig()[0]}")
                return True
            else:
                print("[ERROR] WiFi connection timeout")
                return False
        except Exception as e:
            print(f"[ERROR] WiFi connection failed: {e}")
            return False
    
    @staticmethod
    def disconnect():
        """Disconnect from WiFi."""
        if HAS_NETWORK:
            try:
                import network
                wlan = network.WLAN(network.STA_IF)
                wlan.disconnect()
                wlan.active(False)
            except:
                pass
    
    @staticmethod
    def is_connected():
        """Check if WiFi is connected."""
        if HAS_NETWORK:
            try:
                import network
                wlan = network.WLAN(network.STA_IF)
                return wlan.isconnected()
            except:
                pass
        return False
    
    @staticmethod
    def get_ip():
        """Get IP address."""
        if HAS_NETWORK:
            try:
                import network
                wlan = network.WLAN(network.STA_IF)
                if wlan.isconnected():
                    return wlan.ifconfig()[0]
            except:
                pass
        return None

# Unique ID
def unique_id():
    """Get platform unique ID."""
    if HAS_MACHINE:
        try:
            import machine
            import ubinascii
            uid = machine.unique_id()
            return ubinascii.hexlify(uid).decode()
        except:
            pass
    return "unknown"

# Frequency management (ESP32 specific)
def freq(hz=None):
    """Get or set CPU frequency (ESP32 specific)."""
    if HAS_MACHINE:
        try:
            import machine
            if hz is not None:
                machine.freq(hz)
            return machine.freq()
        except:
            pass
    return 160000000  # Default 160MHz

# Platform information
def get_platform_info():
    """Get comprehensive platform information."""
    info = {
        'platform': PLATFORM,
        'has_machine': HAS_MACHINE,
        'has_network': HAS_NETWORK,
        'unique_id': unique_id(),
    }
    
    try:
        import sys
        info['sys_platform'] = sys.platform
        info['implementation'] = sys.implementation.name
        info['version'] = '.'.join(map(str, sys.implementation.version))
    except:
        pass
    
    if HAS_MACHINE:
        try:
            import machine
            info['freq'] = machine.freq()
        except:
            pass
    
    return info

# Export commonly used items
__all__ = [
    'PLATFORM',
    'HAS_MACHINE',
    'HAS_NETWORK',
    'Pin',
    'ADC',
    'I2C',
    'SoftI2C',
    'RTC',
    'WiFi',
    'time_pulse_us',
    'reset',
    'unique_id',
    'freq',
    'get_platform_info',
    'detect_platform',
]
