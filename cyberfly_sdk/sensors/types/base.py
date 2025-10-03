"""
Base sensor classes and common utilities for MicroPython sensor implementations.
Provides foundation classes for all sensor types.
"""

import time
import gc

class SensorReading:
    """Standardized sensor reading with metadata."""
    def __init__(self, sensor_id, sensor_type, data=None, timestamp=None, status="success", error=None):
        self.sensor_id = str(sensor_id)
        self.sensor_type = str(sensor_type)
        self.data = data or {}
        self.timestamp = timestamp or time.time()
        self.status = str(status)
        self.error = error
    
    def to_dict(self):
        result = {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'data': self.data,
            'timestamp': self.timestamp,
            'status': self.status
        }
        if self.error:
            result['error'] = self.error
        return result

# Hardware abstraction imports with fallbacks
try:
    from ...platform_compat import Pin, ADC, I2C, time_pulse_us
    # Try to get SoftI2C from platform_compat
    try:
        from ...platform_compat import SoftI2C
    except (ImportError, AttributeError):
        SoftI2C = I2C
except ImportError:
    try:
        from platform_compat import Pin, ADC, I2C, time_pulse_us
        try:
            from platform_compat import SoftI2C
        except (ImportError, AttributeError):
            SoftI2C = I2C
    except ImportError:
        try:
            from machine import Pin, ADC, time_pulse_us, I2C, SoftI2C
        except ImportError:
            # Fallback for testing
            class Pin:
                IN = 0
                OUT = 1
                PULL_UP = 2
                def __init__(self, pin, mode=None, pull=None):
                    self.pin = pin
                    self.mode = mode
                    self.pull = pull
                    self._value = 0
                def value(self, val=None):
                    if val is None:
                        return self._value
                    self._value = val
                def on(self):
                    self._value = 1
                def off(self):
                    self._value = 0
            
            class ADC:
                def __init__(self, pin):
                    self.pin = pin
                def read_u16(self):
                    return 32768
            
            def time_pulse_us(pin, pulse_level, timeout_us=1000000):
                return 1000
            
            class I2C:
                def __init__(self, *args, **kwargs):
                    pass
                def scan(self):
                    return [0x48, 0x68, 0x77]
                def readfrom_mem(self, addr, reg, nbytes):
                    return b'\x00' * nbytes
                def writeto_mem(self, addr, reg, data):
                    pass
            
            SoftI2C = I2C

class BaseSensor:
    """Base class for all sensors."""
    
    def __init__(self, inputs=None):
        self.inputs = inputs or {}
        self.last_reading = None
        self.last_read_time = 0
    
    def read(self):
        """Read sensor data. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement read method")
    
    def _cache_reading(self, data, cache_time=1):
        """Cache reading for specified time to avoid rapid re-reads."""
        now = time.time()
        if self.last_reading is None or (now - self.last_read_time) >= cache_time:
            self.last_reading = data
            self.last_read_time = now
            return data
        return self.last_reading

class I2CBaseSensor(BaseSensor):
    """Base class for I2C sensors."""
    
    def __init__(self, inputs, default_address):
        super().__init__(inputs)
        self.address = inputs.get('address', default_address)
        i2c_bus = inputs.get('i2c_bus', 0)
        
        try:
            if i2c_bus == 0:
                # Default I2C pins for ESP32
                self.i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
            else:
                # Alternative I2C pins
                self.i2c = SoftI2C(scl=Pin(25), sda=Pin(26), freq=100000)
            
            # Check if device is present
            devices = self.i2c.scan()
            if self.address not in devices:
                print(f"Warning: I2C device at 0x{self.address:02X} not found")
                
        except Exception as e:
            raise Exception(f"Failed to initialize I2C sensor: {e}")
    
    def _bytes_to_int(self, msb, lsb, signed=False):
        """Convert two bytes to integer."""
        value = (msb << 8) | lsb
        if signed and value > 32767:
            value -= 65536
        return value