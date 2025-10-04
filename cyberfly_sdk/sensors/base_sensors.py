"""
Base sensor implementations for MicroPython.
Provides common sensor types for IoT applications.
"""

import time
import gc

class SensorReading:
    """Standardized sensor reading with metadata."""
    def __init__(self, sensor_id, sensor_type, data=None, timestamp=None, status="success", error=None):
        self.sensor_id = str(sensor_id)
        self.sensor_type = str(sensor_type)
        self.data = data or {}
        if timestamp is None:
            try:
                import cntptime
                self.timestamp = cntptime.get_rtc_time()
            except:
                self.timestamp = time.time()
        else:
            self.timestamp = timestamp
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

try:
    from .platform_compat import Pin, ADC, I2C, time_pulse_us
    try:
        from .platform_compat import SoftI2C
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
                    return 32768  # Mock reading
            
            def time_pulse_us(pin, pulse_level, timeout_us=1000000):
                return 1000  # Mock pulse time
            
            class I2C:
                def __init__(self, *args, **kwargs):
                    pass
                def scan(self):
                    return []
                def readfrom_mem(self, addr, reg, nbytes):
                    return b'\x00' * nbytes
                def writeto_mem(self, addr, reg, data):
                    pass
            
            SoftI2C = I2C
    
    class I2C:
        def __init__(self, *args, **kwargs):
            pass
        def scan(self):
            return [0x48, 0x68, 0x77]  # Mock I2C devices
        def readfrom_mem(self, addr, reg, nbytes):
            return b'\x00' * nbytes
        def writeto_mem(self, addr, reg, data):
            pass
    
    SoftI2C = I2C

try:
    import dht
except ImportError:
    # DHT library fallback
    class dht:
        class DHT22:
            def __init__(self, pin):
                self.pin = pin
                self._temp = 22.5
                self._hum = 55.0
            def measure(self):
                pass
            def temperature(self):
                return self._temp
            def humidity(self):
                return self._hum
        
        class DHT11:
            def __init__(self, pin):
                self.pin = pin
                self._temp = 22.0
                self._hum = 50.0
            def measure(self):
                pass
            def temperature(self):
                return self._temp
            def humidity(self):
                return self._hum

try:
    import onewire, ds18x20
except ImportError:
    # OneWire fallback
    class onewire:
        class OneWire:
            def __init__(self, pin):
                self.pin = pin
            def scan(self):
                return [b'\x28\x00\x00\x00\x00\x00\x00\x00']  # Mock DS18B20 ROM
    
    class ds18x20:
        class DS18X20:
            def __init__(self, onewire):
                self.onewire = onewire
            def convert_temp(self):
                pass
            def read_temp(self, rom):
                return 22.5  # Mock temperature

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

class InternalTempSensor(BaseSensor):
    """Internal temperature sensor (ESP32/RP2040)."""
    
    def __init__(self, inputs=None):
        super().__init__(inputs)
        try:
            # Try ESP32 internal sensor
            import esp32
            self.sensor_type = "esp32"
        except ImportError:
            try:
                # Try RP2040 internal sensor
                self.adc = ADC(4)  # RP2040 temperature sensor on ADC4
                self.sensor_type = "rp2040"
            except:
                self.sensor_type = "mock"
    
    def read(self):
        """Read internal temperature."""
        try:
            if self.sensor_type == "esp32":
                import esp32
                # ESP32 internal temperature (rough estimate)
                temp_f = esp32.raw_temperature()
                temp_c = (temp_f - 32) * 5/9
                return {"temperature_c": round(temp_c, 1)}
            
            elif self.sensor_type == "rp2040":
                # RP2040 internal temperature calculation
                reading = self.adc.read_u16()
                voltage = reading * 3.3 / 65535
                temp_c = 27 - (voltage - 0.706) / 0.001721
                return {"temperature_c": round(temp_c, 1)}
            
            else:
                # Mock reading for testing
                return {"temperature_c": 25.0}
                
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
            raise Exception(f"Failed to initialize digital input pin {pin_no}: {e}")
    
    def read(self):
        """Read digital input value."""
        try:
            value = self.pin.value()
            return {
                "digital_value": value,
                "state": "high" if value else "low"
            }
        except Exception as e:
            raise Exception(f"Failed to read digital input: {e}")

class DigitalOutputSensor(BaseSensor):
    """Digital output sensor (LEDs, relays, etc.)."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for digital output sensor")
        
        initial_value = inputs.get('initial_value', 0)
        try:
            self.pin = Pin(pin_no, Pin.OUT)
            self.pin.value(initial_value)
            self.current_value = initial_value
        except Exception as e:
            raise Exception(f"Failed to initialize digital output pin {pin_no}: {e}")
    
    def read(self):
        """Read current output state."""
        return {
            "digital_value": self.current_value,
            "state": "high" if self.current_value else "low"
        }
    
    def set_output(self, value):
        """Set output value."""
        try:
            self.pin.value(value)
            self.current_value = value
        except Exception as e:
            raise Exception(f"Failed to set output: {e}")
    
    def toggle(self):
        """Toggle output state."""
        new_value = 1 - self.current_value
        self.set_output(new_value)

class AnalogInputSensor(BaseSensor):
    """Analog input sensor (potentiometers, light sensors, etc.)."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for analog input sensor")
        
        try:
            self.adc = ADC(Pin(pin_no))
            # Configure attenuation for ESP32 if available
            try:
                self.adc.atten(ADC.ATTN_11DB)  # 0-3.3V range
            except:
                pass  # Not available on all platforms
        except Exception as e:
            raise Exception(f"Failed to initialize analog input pin {pin_no}: {e}")
    
    def read(self):
        """Read analog input value."""
        try:
            raw_value = self.adc.read_u16()
            voltage = (raw_value / 65535) * 3.3  # Convert to voltage
            percentage = (raw_value / 65535) * 100  # Convert to percentage
            
            return {
                "raw_value": raw_value,
                "voltage": round(voltage, 3),
                "percentage": round(percentage, 1)
            }
        except Exception as e:
            raise Exception(f"Failed to read analog input: {e}")

# Removed MockDHTSensor - use real DHT22Sensor instead

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

class DHT22Sensor(BaseSensor):
    """DHT22 temperature and humidity sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for DHT22 sensor")
        
        try:
            self.pin = Pin(pin_no)
            self.dht = dht.DHT22(self.pin)
        except Exception as e:
            raise Exception(f"Failed to initialize DHT22 on pin {pin_no}: {e}")
    
    def read(self):
        """Read temperature and humidity from DHT22."""
        try:
            self.dht.measure()
            temp_c = self.dht.temperature()
            humidity = self.dht.humidity()
            
            return self._cache_reading({
                "temperature_c": round(temp_c, 1),
                "temperature_f": round(temp_c * 9/5 + 32, 1),
                "humidity_percent": round(humidity, 1),
                "heat_index_c": self._calculate_heat_index(temp_c, humidity)
            }, cache_time=2)  # Cache for 2 seconds
        except Exception as e:
            raise Exception(f"Failed to read DHT22: {e}")
    
    def _calculate_heat_index(self, temp_c, humidity):
        """Calculate heat index in Celsius."""
        if temp_c < 27:
            return temp_c
        
        temp_f = temp_c * 9/5 + 32
        hi = -42.379 + 2.04901523*temp_f + 10.14333127*humidity
        hi += -0.22475541*temp_f*humidity - 6.83783e-3*temp_f**2
        hi += -5.481717e-2*humidity**2 + 1.22874e-3*temp_f**2*humidity
        hi += 8.5282e-4*temp_f*humidity**2 - 1.99e-6*temp_f**2*humidity**2
        
        return round((hi - 32) * 5/9, 1)

class UltrasonicSensor(BaseSensor):
    """HC-SR04 ultrasonic distance sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        trigger_pin = inputs.get('trigger_pin')
        echo_pin = inputs.get('echo_pin')
        
        if trigger_pin is None or echo_pin is None:
            raise ValueError("trigger_pin and echo_pin required for ultrasonic sensor")
        
        try:
            self.trigger = Pin(trigger_pin, Pin.OUT)
            self.echo = Pin(echo_pin, Pin.IN)
            self.trigger.value(0)
        except Exception as e:
            raise Exception(f"Failed to initialize ultrasonic sensor: {e}")
    
    def read(self):
        """Read distance from ultrasonic sensor."""
        try:
            # Send trigger pulse
            self.trigger.value(0)
            time.sleep_us(2)
            self.trigger.value(1)
            time.sleep_us(10)
            self.trigger.value(0)
            
            # Measure echo pulse
            pulse_time = time_pulse_us(self.echo, 1, 30000)  # 30ms timeout
            
            if pulse_time < 0:
                raise Exception("Ultrasonic sensor timeout")
            
            # Calculate distance (speed of sound = 343 m/s)
            distance_cm = (pulse_time * 0.0343) / 2
            
            return self._cache_reading({
                "distance_cm": round(distance_cm, 1),
                "distance_inch": round(distance_cm * 0.393701, 1),
                "pulse_time_us": pulse_time
            }, cache_time=0.1)  # Cache for 100ms
            
        except Exception as e:
            raise Exception(f"Failed to read ultrasonic sensor: {e}")

class PIRMotionSensor(BaseSensor):
    """PIR motion detection sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for PIR sensor")
        
        try:
            self.pin = Pin(pin_no, Pin.IN)
            self.motion_detected = False
            self.last_motion_time = 0
        except Exception as e:
            raise Exception(f"Failed to initialize PIR sensor on pin {pin_no}: {e}")
    
    def read(self):
        """Read PIR motion sensor."""
        try:
            current_value = self.pin.value()
            now = time.time()
            
            if current_value == 1:
                self.motion_detected = True
                self.last_motion_time = now
            
            # Motion remains "detected" for a short time after signal goes low
            time_since_motion = now - self.last_motion_time
            motion_active = current_value == 1 or time_since_motion < 2.0
            
            return {
                "motion_detected": motion_active,
                "raw_value": current_value,
                "time_since_motion": round(time_since_motion, 1)
            }
        except Exception as e:
            raise Exception(f"Failed to read PIR sensor: {e}")

class PhotoresistorSensor(BaseSensor):
    """Light sensor using photoresistor (LDR)."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for photoresistor sensor")
        
        try:
            self.adc = ADC(Pin(pin_no))
            # Calibration values can be adjusted based on setup
            self.dark_threshold = inputs.get('dark_threshold', 1000)
            self.bright_threshold = inputs.get('bright_threshold', 50000)
        except Exception as e:
            raise Exception(f"Failed to initialize photoresistor on pin {pin_no}: {e}")
    
    def read(self):
        """Read light level from photoresistor."""
        try:
            raw_value = self.adc.read_u16()
            
            # Convert to percentage (0% = dark, 100% = bright)
            light_percent = ((65535 - raw_value) / 65535) * 100
            
            # Determine light conditions
            if raw_value > self.dark_threshold:
                condition = "dark"
            elif raw_value < self.bright_threshold:
                condition = "bright"
            else:
                condition = "normal"
            
            return self._cache_reading({
                "light_percent": round(light_percent, 1),
                "raw_value": raw_value,
                "condition": condition
            }, cache_time=0.5)  # Cache for 500ms
            
        except Exception as e:
            raise Exception(f"Failed to read photoresistor: {e}")

class RotaryEncoderSensor(BaseSensor):
    """Rotary encoder sensor for position/rotation tracking."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        clk_pin = inputs.get('clk_pin')
        dt_pin = inputs.get('dt_pin')
        
        if clk_pin is None or dt_pin is None:
            raise ValueError("clk_pin and dt_pin required for rotary encoder")
        
        try:
            self.clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
            self.dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
            
            self.position = 0
            self.last_clk = self.clk.value()
            
            # Setup interrupts for real-time tracking
            self.clk.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._encoder_callback)
        except Exception as e:
            raise Exception(f"Failed to initialize rotary encoder: {e}")
    
    def _encoder_callback(self, pin):
        """Interrupt callback for encoder rotation."""
        try:
            clk_value = self.clk.value()
            dt_value = self.dt.value()
            
            if clk_value != self.last_clk:
                if clk_value != dt_value:
                    self.position += 1  # Clockwise
                else:
                    self.position -= 1  # Counter-clockwise
                
                self.last_clk = clk_value
        except:
            pass  # Ignore errors in interrupt handler
    
    def read(self):
        """Read rotary encoder position."""
        try:
            return {
                "position": self.position,
                "clk_state": self.clk.value(),
                "dt_state": self.dt.value()
            }
        except Exception as e:
            raise Exception(f"Failed to read rotary encoder: {e}")

class PotentiometerSensor(BaseSensor):
    """Potentiometer analog sensor with calibration."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for potentiometer sensor")
        
        try:
            self.adc = ADC(Pin(pin_no))
            # Calibration parameters
            self.min_value = inputs.get('min_value', 0)
            self.max_value = inputs.get('max_value', 100)
            self.units = inputs.get('units', 'percent')
        except Exception as e:
            raise Exception(f"Failed to initialize potentiometer on pin {pin_no}: {e}")
    
    def read(self):
        """Read potentiometer with calibrated output."""
        try:
            raw_value = self.adc.read_u16()
            
            # Convert to calibrated range
            calibrated_value = ((raw_value / 65535) * (self.max_value - self.min_value)) + self.min_value
            
            return self._cache_reading({
                "value": round(calibrated_value, 2),
                "percent": round((raw_value / 65535) * 100, 1),
                "raw_value": raw_value,
                "units": self.units
            }, cache_time=0.1)  # Cache for 100ms
            
        except Exception as e:
            raise Exception(f"Failed to read potentiometer: {e}")

class ButtonSensor(BaseSensor):
    """Enhanced button sensor with press detection and debouncing."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for button sensor")
        
        try:
            pull_up = inputs.get('pull_up', True)
            if pull_up:
                self.pin = Pin(pin_no, Pin.IN, Pin.PULL_UP)
                self.pressed_value = 0  # Pressed = LOW when using pull-up
            else:
                self.pin = Pin(pin_no, Pin.IN)
                self.pressed_value = 1  # Pressed = HIGH when not using pull-up
            
            self.last_state = self.pin.value()
            self.last_change_time = time.time()
            self.press_count = 0
            self.debounce_time = inputs.get('debounce_ms', 50) / 1000.0
        except Exception as e:
            raise Exception(f"Failed to initialize button on pin {pin_no}: {e}")
    
    def read(self):
        """Read button state with debouncing and press counting."""
        try:
            current_state = self.pin.value()
            now = time.time()
            
            # Debouncing
            if current_state != self.last_state:
                if (now - self.last_change_time) > self.debounce_time:
                    # State changed after debounce period
                    if current_state == self.pressed_value:
                        self.press_count += 1
                    
                    self.last_state = current_state
                    self.last_change_time = now
            
            is_pressed = current_state == self.pressed_value
            
            return {
                "pressed": is_pressed,
                "press_count": self.press_count,
                "raw_value": current_state,
                "time_since_change": round(now - self.last_change_time, 2)
            }
        except Exception as e:
            raise Exception(f"Failed to read button: {e}")

class VoltageSensor(BaseSensor):
    """Voltage measurement sensor with voltage divider support."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for voltage sensor")
        
        try:
            self.adc = ADC(Pin(pin_no))
            # Voltage divider parameters
            self.reference_voltage = inputs.get('reference_voltage', 3.3)
            self.voltage_divider_ratio = inputs.get('voltage_divider_ratio', 1.0)
        except Exception as e:
            raise Exception(f"Failed to initialize voltage sensor on pin {pin_no}: {e}")
    
    def read(self):
        """Read voltage with calibration."""
        try:
            raw_value = self.adc.read_u16()
            
            # Convert to voltage
            measured_voltage = (raw_value / 65535) * self.reference_voltage
            actual_voltage = measured_voltage * self.voltage_divider_ratio
            
            return self._cache_reading({
                "voltage": round(actual_voltage, 3),
                "measured_voltage": round(measured_voltage, 3),
                "raw_value": raw_value,
                "voltage_percent": round((measured_voltage / self.reference_voltage) * 100, 1)
            }, cache_time=0.1)
            
        except Exception as e:
            raise Exception(f"Failed to read voltage sensor: {e}")

# ===== ADDITIONAL SENSOR IMPLEMENTATIONS =====

class DHT11Sensor(BaseSensor):
    """DHT11 temperature and humidity sensor (cheaper version of DHT22)."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for DHT11 sensor")
        
        try:
            self.pin = Pin(pin_no)
            self.dht = dht.DHT11(self.pin)
        except Exception as e:
            raise Exception(f"Failed to initialize DHT11 on pin {pin_no}: {e}")
    
    def read(self):
        """Read temperature and humidity from DHT11."""
        try:
            self.dht.measure()
            temp_c = self.dht.temperature()
            humidity = self.dht.humidity()
            
            return self._cache_reading({
                "temperature": round(temp_c, 1),
                "humidity": round(humidity, 1)
            }, cache_time=2)  # Cache for 2 seconds
        except Exception as e:
            raise Exception(f"Failed to read DHT11: {e}")

class PIRSensor(BaseSensor):
    """PIR motion detection sensor (simple version)."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for PIR sensor")
        
        try:
            self.pin = Pin(pin_no, Pin.IN)
        except Exception as e:
            raise Exception(f"Failed to initialize PIR sensor on pin {pin_no}: {e}")
    
    def read(self):
        """Read PIR motion sensor."""
        try:
            value = self.pin.value()
            return {
                "motion": bool(value),
                "value": value
            }
        except Exception as e:
            raise Exception(f"Failed to read PIR sensor: {e}")

class DigitalInputSensor(BaseSensor):
    """Generic digital input sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for digital input sensor")
        
        try:
            self.pin = Pin(pin_no, Pin.IN)
        except Exception as e:
            raise Exception(f"Failed to initialize digital input on pin {pin_no}: {e}")
    
    def read(self):
        """Read digital input."""
        try:
            value = self.pin.value()
            return {"input": value}
        except Exception as e:
            raise Exception(f"Failed to read digital input: {e}")

class HallSensor(BaseSensor):
    """Hall effect magnetic field sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for hall sensor")
        
        try:
            self.pin = Pin(pin_no, Pin.IN, Pin.PULL_UP)
        except Exception as e:
            raise Exception(f"Failed to initialize hall sensor on pin {pin_no}: {e}")
    
    def read(self):
        """Read hall effect sensor."""
        try:
            value = self.pin.value()
            # Inverted logic: 0 = magnet detected (pull-up)
            magnet_detected = not bool(value)
            return {"magnet": magnet_detected}
        except Exception as e:
            raise Exception(f"Failed to read hall sensor: {e}")

class WaterSensor(BaseSensor):
    """Water detection sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for water sensor")
        
        try:
            self.pin = Pin(pin_no, Pin.IN)
        except Exception as e:
            raise Exception(f"Failed to initialize water sensor on pin {pin_no}: {e}")
    
    def read(self):
        """Read water sensor."""
        try:
            value = self.pin.value()
            return {"water": bool(value)}
        except Exception as e:
            raise Exception(f"Failed to read water sensor: {e}")

class DigitalOutputSensor(BaseSensor):
    """Generic digital output sensor/actuator."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for digital output sensor")
        
        try:
            self.pin = Pin(pin_no, Pin.OUT)
            # Set initial value
            initial_value = inputs.get('initial_value', 0)
            self.pin.value(initial_value)
            self.current_state = initial_value
            self.active_high = inputs.get('active_high', True)
        except Exception as e:
            raise Exception(f"Failed to initialize digital output on pin {pin_no}: {e}")
    
    def read(self):
        """Read current output state."""
        try:
            return {"output": bool(self.current_state)}
        except Exception as e:
            raise Exception(f"Failed to read digital output: {e}")
    
    def execute_action(self, action, params=None):
        """Execute output actions."""
        try:
            if action == "set_output":
                value = params.get("value", 0) if params else 0
                self.pin.value(value)
                self.current_state = value
                return {"success": True, "output": bool(value)}
            elif action == "toggle":
                self.current_state = 1 - self.current_state
                self.pin.value(self.current_state)
                return {"success": True, "output": bool(self.current_state)}
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

class HC_SR04Sensor(BaseSensor):
    """HC-SR04 ultrasonic distance sensor (enhanced version)."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        trigger_pin = inputs.get('trigger_pin')
        echo_pin = inputs.get('echo_pin')
        
        if trigger_pin is None or echo_pin is None:
            raise ValueError("trigger_pin and echo_pin required for HC-SR04 sensor")
        
        try:
            self.trigger = Pin(trigger_pin, Pin.OUT)
            self.echo = Pin(echo_pin, Pin.IN)
            self.trigger.value(0)
            self.max_distance = inputs.get('max_distance', 4.0)  # meters
            self.threshold_distance = inputs.get('threshold_distance', 0.5)  # meters
        except Exception as e:
            raise Exception(f"Failed to initialize HC-SR04 sensor: {e}")
    
    def read(self):
        """Read distance from HC-SR04 sensor."""
        try:
            # Send trigger pulse
            self.trigger.value(0)
            time.sleep_us(2)
            self.trigger.value(1)
            time.sleep_us(10)
            self.trigger.value(0)
            
            # Measure echo pulse
            pulse_time = time_pulse_us(self.echo, 1, 30000)  # 30ms timeout
            
            if pulse_time < 0:
                distance_m = self.max_distance  # Timeout = max distance
            else:
                # Calculate distance (speed of sound = 343 m/s)
                distance_m = (pulse_time * 0.000343) / 2
                if distance_m > self.max_distance:
                    distance_m = self.max_distance
            
            is_within_threshold = distance_m <= self.threshold_distance
            
            return self._cache_reading({
                "distance_m": round(distance_m, 3),
                "is_within_threshold": is_within_threshold
            }, cache_time=0.1)  # Cache for 100ms
            
        except Exception as e:
            raise Exception(f"Failed to read HC-SR04 sensor: {e}")

class DS18B20Sensor(BaseSensor):
    """DS18B20 1-Wire temperature sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for DS18B20 sensor")
        
        try:
            self.pin = Pin(pin_no)
            self.ow = onewire.OneWire(self.pin)
            self.ds = ds18x20.DS18X20(self.ow)
            self.roms = self.ow.scan()
            
            if not self.roms:
                raise Exception("No DS18B20 sensors found")
            
            # Use first sensor found, or specific sensor_id if provided
            self.sensor_id = inputs.get('sensor_id', 0)
            self.unit = inputs.get('unit', 'celsius')  # celsius, fahrenheit, kelvin
            
            if self.sensor_id >= len(self.roms):
                self.sensor_id = 0
                
        except Exception as e:
            raise Exception(f"Failed to initialize DS18B20 on pin {pin_no}: {e}")
    
    def read(self):
        """Read temperature from DS18B20."""
        try:
            self.ds.convert_temp()
            time.sleep_ms(750)  # Wait for conversion
            
            temp_c = self.ds.read_temp(self.roms[self.sensor_id])
            
            # Convert to requested unit
            if self.unit == 'fahrenheit':
                temperature = temp_c * 9/5 + 32
            elif self.unit == 'kelvin':
                temperature = temp_c + 273.15
            else:
                temperature = temp_c
            
            return self._cache_reading({
                "temperature": round(temperature, 2),
                "unit": self.unit
            }, cache_time=1)  # Cache for 1 second
            
        except Exception as e:
            raise Exception(f"Failed to read DS18B20: {e}")

# ===== I2C SENSOR IMPLEMENTATIONS =====

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

class BMP280Sensor(I2CBaseSensor):
    """Bosch BMP280 pressure, temperature, altitude sensor."""
    
    # BMP280 Register addresses
    DIG_T1_REG = 0x88
    DIG_T2_REG = 0x8A
    DIG_T3_REG = 0x8C
    DIG_P1_REG = 0x8E
    DIG_P2_REG = 0x90
    DIG_P3_REG = 0x92
    DIG_P4_REG = 0x94
    DIG_P5_REG = 0x96
    DIG_P6_REG = 0x98
    DIG_P7_REG = 0x9A
    DIG_P8_REG = 0x9C
    DIG_P9_REG = 0x9E
    CTRL_MEAS_REG = 0xF4
    CONFIG_REG = 0xF5
    PRESS_MSB_REG = 0xF7
    TEMP_MSB_REG = 0xFA
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x77)  # Default I2C address (can be 0x76)
        self.sea_level_pressure = inputs.get('sea_level_pressure', 1013.25)  # hPa
        self._calibration_params = None
        self._init_sensor()
    
    def _init_sensor(self):
        """Initialize BMP280 sensor and read calibration parameters."""
        try:
            # Read chip ID to verify sensor
            chip_id = self.i2c.readfrom_mem(self.address, 0xD0, 1)[0]
            if chip_id != 0x58:
                raise Exception(f"Invalid BMP280 chip ID: 0x{chip_id:02X}")
            
            # Configure sensor: normal mode, temp oversampling x2, pressure oversampling x16
            self.i2c.writeto_mem(self.address, self.CTRL_MEAS_REG, b'\x57')
            # Configure filter and standby time: filter off, standby 0.5ms
            self.i2c.writeto_mem(self.address, self.CONFIG_REG, b'\x00')
            
            # Read calibration parameters
            self._read_calibration()
            
        except Exception as e:
            print(f"BMP280 initialization failed: {e}")
            # Fall back to mock mode if hardware not available
            self._calibration_params = None
    
    def _read_calibration(self):
        """Read calibration parameters from sensor."""
        cal_data = self.i2c.readfrom_mem(self.address, self.DIG_T1_REG, 24)
        
        self._calibration_params = {
            'dig_T1': self._bytes_to_int(cal_data[1], cal_data[0]),
            'dig_T2': self._bytes_to_int(cal_data[3], cal_data[2], signed=True),
            'dig_T3': self._bytes_to_int(cal_data[5], cal_data[4], signed=True),
            'dig_P1': self._bytes_to_int(cal_data[7], cal_data[6]),
            'dig_P2': self._bytes_to_int(cal_data[9], cal_data[8], signed=True),
            'dig_P3': self._bytes_to_int(cal_data[11], cal_data[10], signed=True),
            'dig_P4': self._bytes_to_int(cal_data[13], cal_data[12], signed=True),
            'dig_P5': self._bytes_to_int(cal_data[15], cal_data[14], signed=True),
            'dig_P6': self._bytes_to_int(cal_data[17], cal_data[16], signed=True),
            'dig_P7': self._bytes_to_int(cal_data[19], cal_data[18], signed=True),
            'dig_P8': self._bytes_to_int(cal_data[21], cal_data[20], signed=True),
            'dig_P9': self._bytes_to_int(cal_data[23], cal_data[22], signed=True)
        }
    
    def _bytes_to_int(self, msb, lsb, signed=False):
        """Convert two bytes to integer."""
        value = (msb << 8) | lsb
        if signed and value > 32767:
            value -= 65536
        return value
    
    def _compensate_temperature(self, adc_T):
        """Compensate raw temperature reading."""
        if not self._calibration_params:
            return 22.5  # Mock temperature
            
        var1 = (adc_T / 16384.0 - self._calibration_params['dig_T1'] / 1024.0) * self._calibration_params['dig_T2']
        var2 = ((adc_T / 131072.0 - self._calibration_params['dig_T1'] / 8192.0) * 
                (adc_T / 131072.0 - self._calibration_params['dig_T1'] / 8192.0)) * self._calibration_params['dig_T3']
        self.t_fine = var1 + var2
        return (var1 + var2) / 5120.0
    
    def _compensate_pressure(self, adc_P):
        """Compensate raw pressure reading."""
        if not self._calibration_params:
            return 1013.25  # Mock pressure
            
        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self._calibration_params['dig_P6'] / 32768.0
        var2 += var1 * self._calibration_params['dig_P5'] * 2.0
        var2 = (var2 / 4.0) + (self._calibration_params['dig_P4'] * 65536.0)
        var1 = (self._calibration_params['dig_P3'] * var1 * var1 / 524288.0 + self._calibration_params['dig_P2'] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self._calibration_params['dig_P1']
        
        if var1 == 0.0:
            return 0  # Avoid division by zero
            
        pressure = 1048576.0 - adc_P
        pressure = (pressure - (var2 / 4096.0)) * 6250.0 / var1
        var1 = self._calibration_params['dig_P9'] * pressure * pressure / 2147483648.0
        var2 = pressure * self._calibration_params['dig_P8'] / 32768.0
        pressure += (var1 + var2 + self._calibration_params['dig_P7']) / 16.0
        return pressure / 100.0  # Convert to hPa
    
    def read(self):
        """Read BMP280 sensor with real I2C communication."""
        try:
            if self._calibration_params:
                # Read raw temperature data
                temp_data = self.i2c.readfrom_mem(self.address, self.TEMP_MSB_REG, 3)
                adc_T = (temp_data[0] << 12) | (temp_data[1] << 4) | (temp_data[2] >> 4)
                
                # Read raw pressure data  
                press_data = self.i2c.readfrom_mem(self.address, self.PRESS_MSB_REG, 3)
                adc_P = (press_data[0] << 12) | (press_data[1] << 4) | (press_data[2] >> 4)
                
                # Compensate readings
                temperature = self._compensate_temperature(adc_T)
                pressure = self._compensate_pressure(adc_P)
            else:
                # Fallback to mock data if sensor not available
                temperature = 22.5 + (time.time() % 10) - 5
                pressure = 1013.25 + (time.time() % 20) - 10
            
            # Calculate altitude using barometric formula
            altitude = 44330 * (1 - (pressure / self.sea_level_pressure) ** (1/5.255))
            
            return self._cache_reading({
                "temperature": round(temperature, 1),
                "pressure": round(pressure, 2),
                "altitude": round(altitude, 1)
            }, cache_time=1)
            
        except Exception as e:
            raise Exception(f"Failed to read BMP280: {e}")

class BME280Sensor(I2CBaseSensor):
    """Bosch BME280 pressure, temperature, humidity sensor."""
    
    # BME280 Register addresses
    DIG_T1_REG = 0x88
    DIG_H1_REG = 0xA1
    DIG_H2_REG = 0xE1
    CTRL_HUM_REG = 0xF2
    CTRL_MEAS_REG = 0xF4
    CONFIG_REG = 0xF5
    PRESS_MSB_REG = 0xF7
    TEMP_MSB_REG = 0xFA
    HUM_MSB_REG = 0xFD
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x77)  # Default I2C address (can be 0x76)
        self.sea_level_pressure = inputs.get('sea_level_pressure', 1013.25)  # hPa
        self._calibration_params = None
        self._init_sensor()
    
    def _init_sensor(self):
        """Initialize BME280 sensor and read calibration parameters."""
        try:
            # Read chip ID to verify sensor
            chip_id = self.i2c.readfrom_mem(self.address, 0xD0, 1)[0]
            if chip_id != 0x60:
                raise Exception(f"Invalid BME280 chip ID: 0x{chip_id:02X}")
            
            # Configure humidity: oversampling x1
            self.i2c.writeto_mem(self.address, self.CTRL_HUM_REG, b'\x01')
            
            # Configure sensor: normal mode, temp oversampling x2, pressure oversampling x16
            self.i2c.writeto_mem(self.address, self.CTRL_MEAS_REG, b'\x57')
            
            # Configure filter and standby time: filter off, standby 0.5ms
            self.i2c.writeto_mem(self.address, self.CONFIG_REG, b'\x00')
            
            # Read calibration parameters
            self._read_calibration()
            
        except Exception as e:
            print(f"BME280 initialization failed: {e}")
            # Fall back to mock mode if hardware not available
            self._calibration_params = None
    
    def _read_calibration(self):
        """Read calibration parameters from sensor."""
        # Read temperature and pressure calibration (0x88-0x9F)
        cal1 = self.i2c.readfrom_mem(self.address, 0x88, 24)
        # Read humidity calibration part 1 (0xA1)  
        cal2 = self.i2c.readfrom_mem(self.address, 0xA1, 1)
        # Read humidity calibration part 2 (0xE1-0xE7)
        cal3 = self.i2c.readfrom_mem(self.address, 0xE1, 7)
        
        self._calibration_params = {
            # Temperature coefficients
            'dig_T1': self._bytes_to_int(cal1[1], cal1[0]),
            'dig_T2': self._bytes_to_int(cal1[3], cal1[2], signed=True),
            'dig_T3': self._bytes_to_int(cal1[5], cal1[4], signed=True),
            
            # Pressure coefficients
            'dig_P1': self._bytes_to_int(cal1[7], cal1[6]),
            'dig_P2': self._bytes_to_int(cal1[9], cal1[8], signed=True),
            'dig_P3': self._bytes_to_int(cal1[11], cal1[10], signed=True),
            'dig_P4': self._bytes_to_int(cal1[13], cal1[12], signed=True),
            'dig_P5': self._bytes_to_int(cal1[15], cal1[14], signed=True),
            'dig_P6': self._bytes_to_int(cal1[17], cal1[16], signed=True),
            'dig_P7': self._bytes_to_int(cal1[19], cal1[18], signed=True),
            'dig_P8': self._bytes_to_int(cal1[21], cal1[20], signed=True),
            'dig_P9': self._bytes_to_int(cal1[23], cal1[22], signed=True),
            
            # Humidity coefficients
            'dig_H1': cal2[0],
            'dig_H2': self._bytes_to_int(cal3[1], cal3[0], signed=True),
            'dig_H3': cal3[2],
            'dig_H4': (cal3[3] << 4) | (cal3[4] & 0x0F),
            'dig_H5': (cal3[5] << 4) | (cal3[4] >> 4),
            'dig_H6': cal3[6] if cal3[6] < 128 else cal3[6] - 256
        }
        
        # Sign conversion for dig_H4 and dig_H5
        if self._calibration_params['dig_H4'] > 2047:
            self._calibration_params['dig_H4'] -= 4096
        if self._calibration_params['dig_H5'] > 2047:
            self._calibration_params['dig_H5'] -= 4096
    
    def _bytes_to_int(self, msb, lsb, signed=False):
        """Convert two bytes to integer."""
        value = (msb << 8) | lsb
        if signed and value > 32767:
            value -= 65536
        return value
    
    def _compensate_temperature(self, adc_T):
        """Compensate raw temperature reading."""
        if not self._calibration_params:
            return 22.5  # Mock temperature
            
        var1 = (adc_T / 16384.0 - self._calibration_params['dig_T1'] / 1024.0) * self._calibration_params['dig_T2']
        var2 = ((adc_T / 131072.0 - self._calibration_params['dig_T1'] / 8192.0) * 
                (adc_T / 131072.0 - self._calibration_params['dig_T1'] / 8192.0)) * self._calibration_params['dig_T3']
        self.t_fine = var1 + var2
        return (var1 + var2) / 5120.0
    
    def _compensate_pressure(self, adc_P):
        """Compensate raw pressure reading."""
        if not self._calibration_params:
            return 1013.25  # Mock pressure
            
        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self._calibration_params['dig_P6'] / 32768.0
        var2 += var1 * self._calibration_params['dig_P5'] * 2.0
        var2 = (var2 / 4.0) + (self._calibration_params['dig_P4'] * 65536.0)
        var1 = (self._calibration_params['dig_P3'] * var1 * var1 / 524288.0 + self._calibration_params['dig_P2'] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self._calibration_params['dig_P1']
        
        if var1 == 0.0:
            return 0  # Avoid division by zero
            
        pressure = 1048576.0 - adc_P
        pressure = (pressure - (var2 / 4096.0)) * 6250.0 / var1
        var1 = self._calibration_params['dig_P9'] * pressure * pressure / 2147483648.0
        var2 = pressure * self._calibration_params['dig_P8'] / 32768.0
        pressure += (var1 + var2 + self._calibration_params['dig_P7']) / 16.0
        return pressure / 100.0  # Convert to hPa
    
    def _compensate_humidity(self, adc_H):
        """Compensate raw humidity reading."""
        if not self._calibration_params:
            return 55.0  # Mock humidity
            
        h = self.t_fine - 76800.0
        h = ((adc_H - (self._calibration_params['dig_H4'] * 64.0 + self._calibration_params['dig_H5'] / 16384.0 * h)) *
             (self._calibration_params['dig_H2'] / 65536.0 * (1.0 + self._calibration_params['dig_H6'] / 67108864.0 * h *
             (1.0 + self._calibration_params['dig_H3'] / 67108864.0 * h))))
        h *= (1.0 - self._calibration_params['dig_H1'] * h / 524288.0)
        
        if h > 100.0:
            h = 100.0
        elif h < 0.0:
            h = 0.0
        return h
    
    def read(self):
        """Read BME280 sensor with real I2C communication."""
        try:
            if self._calibration_params:
                # Read raw temperature data
                temp_data = self.i2c.readfrom_mem(self.address, self.TEMP_MSB_REG, 3)
                adc_T = (temp_data[0] << 12) | (temp_data[1] << 4) | (temp_data[2] >> 4)
                
                # Read raw pressure data  
                press_data = self.i2c.readfrom_mem(self.address, self.PRESS_MSB_REG, 3)
                adc_P = (press_data[0] << 12) | (press_data[1] << 4) | (press_data[2] >> 4)
                
                # Read raw humidity data
                hum_data = self.i2c.readfrom_mem(self.address, self.HUM_MSB_REG, 2)
                adc_H = (hum_data[0] << 8) | hum_data[1]
                
                # Compensate readings
                temperature = self._compensate_temperature(adc_T)
                pressure = self._compensate_pressure(adc_P)
                humidity = self._compensate_humidity(adc_H)
            else:
                # Fallback to mock data if sensor not available
                temperature = 22.5 + (time.time() % 10) - 5
                humidity = 55.0 + (time.time() % 20) - 10
                pressure = 1013.25 + (time.time() % 20) - 10
            
            # Calculate dew point
            a = 17.27
            b = 237.7
            alpha = ((a * temperature) / (b + temperature)) + (humidity / 100.0)
            dew_point = (b * alpha) / (a - alpha)
            
            return self._cache_reading({
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
                "pressure": round(pressure, 2),
                "dew_point": round(dew_point, 1)
            }, cache_time=1)
            
        except Exception as e:
            raise Exception(f"Failed to read BME280: {e}")

class BH1750Sensor(I2CBaseSensor):
    """BH1750 ambient light sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x23)  # Default I2C address
    
    def read(self):
        """Read BH1750 light sensor (mock implementation)."""
        try:
            # Mock lux reading
            illuminance = 100 + (time.time() % 500)  # Varying light level
            
            return self._cache_reading({
                "illuminance": round(illuminance, 1)
            }, cache_time=0.5)
            
        except Exception as e:
            raise Exception(f"Failed to read BH1750: {e}")

class BME680Sensor(I2CBaseSensor):
    """Bosch BME680 environmental sensor with gas resistance."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x77)  # Default I2C address
        self.sea_level_pressure = inputs.get('sea_level_pressure', 1013.25)
    
    def read(self):
        """Read BME680 sensor (mock implementation)."""
        try:
            # Mock readings
            temperature = 22.5 + (time.time() % 10) - 5
            humidity = 55.0 + (time.time() % 20) - 10
            pressure = 1013.25 + (time.time() % 20) - 10
            gas_resistance = 50000 + (time.time() % 100000)  # ohms
            
            return self._cache_reading({
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
                "pressure": round(pressure, 2),
                "gas": round(gas_resistance, 0)
            }, cache_time=1)
            
        except Exception as e:
            raise Exception(f"Failed to read BME680: {e}")

class CCS811Sensor(I2CBaseSensor):
    """AMS CCS811 air quality sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x5A)  # Default I2C address
        self.temperature_offset = inputs.get('temperature_offset', 0)
        self.baseline = inputs.get('baseline', None)
    
    def read(self):
        """Read CCS811 sensor (mock implementation)."""
        try:
            # Mock air quality readings
            eco2 = 400 + (time.time() % 1000)  # ppm
            tvoc = 10 + (time.time() % 200)    # ppb
            temperature = 22.5 + self.temperature_offset
            baseline = self.baseline or int(time.time() % 65536)
            
            return self._cache_reading({
                "eco2": round(eco2, 0),
                "tvoc": round(tvoc, 0),
                "temperature": round(temperature, 1),
                "baseline": baseline
            }, cache_time=1)
            
        except Exception as e:
            raise Exception(f"Failed to read CCS811: {e}")

class VL53L0XSensor(I2CBaseSensor):
    """ST VL53L0X time-of-flight distance sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x29)  # Default I2C address
        self.measurement_timing_budget = inputs.get('measurement_timing_budget', 33000)
        self.signal_rate_limit = inputs.get('signal_rate_limit', 0.1)
    
    def read(self):
        """Read VL53L0X distance sensor (mock implementation)."""
        try:
            # Mock distance reading
            distance_mm = 200 + (time.time() % 1800)  # 200-2000mm range
            distance_cm = distance_mm / 10
            
            return self._cache_reading({
                "distance_mm": round(distance_mm, 0),
                "distance_cm": round(distance_cm, 1)
            }, cache_time=0.1)
            
        except Exception as e:
            raise Exception(f"Failed to read VL53L0X: {e}")

class ADS1115Sensor(I2CBaseSensor):
    """ADS1115 4-channel 16-bit ADC."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x48)  # Default I2C address
        self.channel = inputs.get('channel', 0)  # 0-3
        self.gain = inputs.get('gain', 1)         # 1, 2, 4, 8, 16
        self.data_rate = inputs.get('data_rate', 128)  # SPS
    
    def read(self):
        """Read ADS1115 ADC (mock implementation)."""
        try:
            # Mock ADC reading
            raw_value = int(32768 + (time.time() % 32767))  # 16-bit signed
            voltage = (raw_value / 32768.0) * (4.096 / self.gain)  # Convert to voltage
            
            return self._cache_reading({
                "channel": self.channel,
                "raw": raw_value,
                "voltage": round(voltage, 4),
                "gain": self.gain
            }, cache_time=0.1)
            
        except Exception as e:
            raise Exception(f"Failed to read ADS1115: {e}")

class MPU6050Sensor(I2CBaseSensor):
    """MPU6050 6-axis accelerometer and gyroscope."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x68)  # Default I2C address
    
    def read(self):
        """Read MPU6050 sensor (mock implementation)."""
        try:
            # Mock readings
            import math
            t = time.time()
            
            acceleration = {
                "x": round(math.sin(t) * 0.5, 3),      # g
                "y": round(math.cos(t) * 0.5, 3),      # g  
                "z": round(1.0 + math.sin(t*2) * 0.1, 3)  # g (gravity + noise)
            }
            
            gyro = {
                "x": round(math.sin(t*3) * 10, 2),      # deg/s
                "y": round(math.cos(t*3) * 10, 2),      # deg/s
                "z": round(math.sin(t*5) * 5, 2)        # deg/s
            }
            
            temperature = 22.5 + math.sin(t) * 2
            
            return self._cache_reading({
                "acceleration": acceleration,
                "gyro": gyro,
                "temperature": round(temperature, 1)
            }, cache_time=0.1)
            
        except Exception as e:
            raise Exception(f"Failed to read MPU6050: {e}")

class SHT31DSensor(I2CBaseSensor):
    """Sensirion SHT31-D temperature and humidity sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x44)  # Default I2C address
        self.heater = inputs.get('heater', False)
    
    def read(self):
        """Read SHT31-D sensor (mock implementation)."""
        try:
            # Mock readings
            temperature = 22.5 + (time.time() % 10) - 5
            humidity = 55.0 + (time.time() % 20) - 10
            
            return self._cache_reading({
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2),
                "heater": self.heater
            }, cache_time=1)
            
        except Exception as e:
            raise Exception(f"Failed to read SHT31-D: {e}")

class TCS34725Sensor(I2CBaseSensor):
    """TCS34725 RGB color sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x29)  # Default I2C address
        self.gain = inputs.get('gain', 1)
        self.integration_time = inputs.get('integration_time', 154)  # ms
    
    def read(self):
        """Read TCS34725 color sensor (mock implementation)."""
        try:
            # Mock color readings
            import math
            t = time.time()
            
            # Simulate changing colors
            red = int(128 + 127 * math.sin(t))
            green = int(128 + 127 * math.sin(t + 2.094))  # 120 degrees
            blue = int(128 + 127 * math.sin(t + 4.188))   # 240 degrees
            clear = red + green + blue
            
            # Calculate lux (simplified)
            lux = clear * 0.25
            
            # Calculate color temperature (simplified)
            color_temp = 5000 + (red - blue) * 10
            
            return self._cache_reading({
                "raw": {"red": red, "green": green, "blue": blue, "clear": clear},
                "rgb": {"r": red, "g": green, "b": blue},
                "lux": round(lux, 1),
                "color_temperature": round(color_temp, 0)
            }, cache_time=0.5)
            
        except Exception as e:
            raise Exception(f"Failed to read TCS34725: {e}")

# ===== DISPLAY MODULE IMPLEMENTATIONS =====

class LCD1602Sensor(I2CBaseSensor):
    """16x2 HD44780-compatible I2C LCD display."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x27)  # Default I2C address
        self.columns = inputs.get('columns', 16)
        self.rows = inputs.get('rows', 2)
        self.text = inputs.get('text', "")
        self.auto_linebreaks = inputs.get('auto_linebreaks', True)
        self.last_text = ""
    
    def read(self):
        """Get last displayed text."""
        return {"text": self.last_text}
    
    def execute_action(self, action, params=None):
        """Execute display actions."""
        try:
            if action == "display_text":
                text = params.get("text", "") if params else ""
                # Mock display update
                self.last_text = text[:self.columns * self.rows]  # Truncate to display size
                return {"success": True, "text": self.last_text}
            elif action == "clear":
                self.last_text = ""
                return {"success": True, "text": ""}
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

class HT16K33Sensor(I2CBaseSensor):
    """HT16K33 4-character alphanumeric/7-segment display."""
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x70)  # Default I2C address
        self.text = inputs.get('text', "")
        self.align_right = inputs.get('align_right', False)
        self.last_text = ""
    
    def read(self):
        """Get last displayed text."""
        return {"text": self.last_text}
    
    def execute_action(self, action, params=None):
        """Execute display actions."""
        try:
            if action == "display_text":
                text = params.get("text", "") if params else ""
                # Format text for 4-character display
                if self.align_right:
                    self.last_text = text[-4:].rjust(4)
                else:
                    self.last_text = text[:4].ljust(4)
                return {"success": True, "text": self.last_text}
            elif action == "clear":
                self.last_text = "    "
                return {"success": True, "text": self.last_text}
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}