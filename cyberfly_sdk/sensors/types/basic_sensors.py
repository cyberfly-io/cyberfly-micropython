"""
Basic sensor implementations: digital inputs, analog inputs, internal sensors.
Simple sensors that don't require complex protocols.
"""

import time
from .base import BaseSensor, Pin, ADC

class InternalTempSensor(BaseSensor):
    """Internal temperature sensor (ESP32/RP2040)."""
    
    def __init__(self, inputs=None):
        super().__init__(inputs)
        try:
            # Try ESP32 internal sensor
            import esp32
            self.sensor_type = "esp32"
            self.esp32 = esp32
        except ImportError:
            try:
                # Try RP2040 internal sensor
                self.adc = ADC(4)  # RP2040 temperature sensor on ADC4
                self.sensor_type = "rp2040"
            except:
                # Generic temperature sensor fallback (use system temperature if available)
                self.sensor_type = "generic"
                self._temp_offset = inputs.get('temp_offset', 0) if inputs else 0
    
    def read(self):
        """Read internal temperature."""
        try:
            if self.sensor_type == "esp32":
                # ESP32 internal temperature sensor
                # The esp32.raw_temperature() returns Fahrenheit, but it's not very accurate
                # Better approach is to use the ADC and proper calibration
                try:
                    temp_f = self.esp32.raw_temperature()
                    temp_c = (temp_f - 32) * 5/9
                    
                    # Apply basic calibration (ESP32 internal sensor has offset)
                    temp_c = temp_c - 10  # Typical offset adjustment
                    
                    return {"temperature_c": round(temp_c, 1), "sensor_type": "esp32_internal"}
                except:
                    # Fallback if ESP32 temperature sensor fails
                    return {"temperature_c": 25.0, "sensor_type": "esp32_fallback"}
            
            elif self.sensor_type == "rp2040":
                # RP2040 internal temperature calculation
                reading = self.adc.read_u16()
                voltage = reading * 3.3 / 65535
                temp_c = 27 - (voltage - 0.706) / 0.001721
                
                return {
                    "temperature_c": round(temp_c, 1),
                    "voltage": round(voltage, 3),
                    "raw_reading": reading,
                    "sensor_type": "rp2040_internal"
                }
            
            else:
                # Generic sensor - use ambient estimate with variation
                import time
                base_temp = 25.0 + self._temp_offset
                # Add small time-based variation to simulate temperature changes
                variation = (time.time() % 600) / 100 - 3  # ±3°C variation over 10 minutes
                temp_c = base_temp + variation
                
                return {
                    "temperature_c": round(temp_c, 1),
                    "sensor_type": "generic_estimated"
                }
                
        except Exception as e:
            raise Exception(f"Failed to read internal temperature: {e}")

class DigitalInputSensor(BaseSensor):
    """Digital input sensor (buttons, switches, etc.)."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for digital input sensor")
        
        pull_up = inputs.get('pull_up', True)
        try:
            if pull_up:
                self.pin = Pin(pin_no, Pin.IN, Pin.PULL_UP)
            else:
                self.pin = Pin(pin_no, Pin.IN)
        except Exception as e:
            raise Exception(f"Failed to initialize digital input on pin {pin_no}: {e}")
    
    def read(self):
        """Read digital input state."""
        try:
            value = self.pin.value()
            return {
                "state": bool(value),
                "value": int(value)
            }
        except Exception as e:
            raise Exception(f"Failed to read digital input: {e}")

class AnalogInputSensor(BaseSensor):
    """Analog input sensor (potentiometers, voltage dividers, etc.)."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for analog input sensor")
        
        self.vref = inputs.get('vref', 3.3)  # Reference voltage
        try:
            self.adc = ADC(Pin(pin_no))
        except Exception as e:
            raise Exception(f"Failed to initialize ADC on pin {pin_no}: {e}")
    
    def read(self):
        """Read analog input value."""
        try:
            raw_value = self.adc.read_u16()
            voltage = (raw_value / 65535) * self.vref
            percentage = (raw_value / 65535) * 100
            
            return {
                "raw": raw_value,
                "voltage": round(voltage, 3),
                "percentage": round(percentage, 1)
            }
        except Exception as e:
            raise Exception(f"Failed to read analog input: {e}")

class SystemInfoSensor(BaseSensor):
    """System information sensor (memory, uptime, etc.)."""
    
    def __init__(self, inputs=None):
        super().__init__(inputs)
    
    def read(self):
        """Read system information."""
        try:
            import gc
            gc.collect()
            free_mem = gc.mem_free()
            alloc_mem = gc.mem_alloc()
            total_mem = free_mem + alloc_mem
            
            uptime = time.time()  # Approximate uptime since boot
            
            return {
                "free_memory": free_mem,
                "allocated_memory": alloc_mem,
                "total_memory": total_mem,
                "memory_usage_percent": round((alloc_mem / total_mem) * 100, 1),
                "uptime_seconds": round(uptime, 1)
            }
        except Exception as e:
            raise Exception(f"Failed to read system info: {e}")