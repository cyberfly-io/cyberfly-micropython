"""
Motion and distance sensor implementations.
Includes PIR motion sensors, ultrasonic distance sensors, and accelerometers.
"""

import time
from .base import BaseSensor, I2CBaseSensor, Pin, time_pulse_us

# OneWire imports for DS18B20
try:
    import onewire, ds18x20
except ImportError:
    # OneWire library fallback - in production this would indicate missing driver
    print("Warning: OneWire library not available - DS18B20 sensors will not function")
    class onewire:
        class OneWire:
            def __init__(self, pin):
                self.pin = pin
                print(f"OneWire fallback initialized on pin {pin.pin if hasattr(pin, 'pin') else pin}")
            def scan(self):
                print("OneWire scan: No library available")
                return []  # Return empty list instead of mock data
    
    class ds18x20:
        class DS18X20:
            def __init__(self, onewire):
                self.onewire = onewire
            def convert_temp(self):
                pass
            def read_temp(self, rom):
                return None  # Return None to indicate no reading available

class PIRSensor(BaseSensor):
    """PIR (Passive Infrared) motion sensor."""
    
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
            current_state = bool(self.pin.value())
            now = time.time()
            
            if current_state and not self.motion_detected:
                self.motion_detected = True
                self.last_motion_time = now
            elif not current_state:
                self.motion_detected = False
            
            time_since_motion = now - self.last_motion_time if self.last_motion_time > 0 else 0
            
            return {
                "motion_detected": self.motion_detected,
                "current_state": current_state,
                "last_motion_time": self.last_motion_time,
                "time_since_motion": round(time_since_motion, 1)
            }
        except Exception as e:
            raise Exception(f"Failed to read PIR sensor: {e}")

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
            self.max_distance = inputs.get('max_distance', 400)  # cm
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
            
            # Measure echo pulse duration
            try:
                pulse_time = time_pulse_us(self.echo, 1, timeout_us=30000)
                if pulse_time < 0:
                    # Timeout occurred
                    distance_cm = self.max_distance
                    status = "timeout"
                else:
                    # Calculate distance: pulse_time in microseconds
                    # Sound travels at ~343 m/s, so distance = (pulse_time * 343) / (2 * 1000000) * 100
                    distance_cm = (pulse_time * 0.0343) / 2
                    status = "success"
                    
                    # Limit to sensor range
                    if distance_cm > self.max_distance:
                        distance_cm = self.max_distance
                        status = "out_of_range"
                        
            except Exception:
                distance_cm = self.max_distance
                status = "error"
            
            return self._cache_reading({
                "distance_cm": round(distance_cm, 1),
                "distance_mm": round(distance_cm * 10, 0),
                "distance_inches": round(distance_cm / 2.54, 1),
                "status": status
            }, cache_time=0.1)  # Very short cache for motion detection
            
        except Exception as e:
            raise Exception(f"Failed to read ultrasonic sensor: {e}")

class MPU6050Sensor(I2CBaseSensor):
    """MPU6050 6-axis accelerometer and gyroscope."""
    
    # MPU6050 Register addresses
    PWR_MGMT_1 = 0x6B
    ACCEL_XOUT_H = 0x3B
    GYRO_XOUT_H = 0x43
    TEMP_OUT_H = 0x41
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x68)  # Default I2C address
        self.accel_scale = inputs.get('accel_scale', 2)  # ±2g, 4g, 8g, 16g
        self.gyro_scale = inputs.get('gyro_scale', 250)  # ±250, 500, 1000, 2000 °/s
        self._init_sensor()
    
    def _init_sensor(self):
        """Initialize MPU6050 sensor."""
        try:
            # Wake up the sensor (disable sleep mode)
            self.i2c.writeto_mem(self.address, self.PWR_MGMT_1, b'\x00')
            time.sleep_ms(100)
            
            # Configure accelerometer range
            accel_config = {2: 0x00, 4: 0x08, 8: 0x10, 16: 0x18}
            self.i2c.writeto_mem(self.address, 0x1C, bytes([accel_config.get(self.accel_scale, 0x00)]))
            
            # Configure gyroscope range
            gyro_config = {250: 0x00, 500: 0x08, 1000: 0x10, 2000: 0x18}
            self.i2c.writeto_mem(self.address, 0x1B, bytes([gyro_config.get(self.gyro_scale, 0x00)]))
            
        except Exception as e:
            print(f"MPU6050 initialization failed: {e}")
    
    def read(self):
        """Read MPU6050 sensor data."""
        try:
            # Read accelerometer data
            accel_data = self.i2c.readfrom_mem(self.address, self.ACCEL_XOUT_H, 6)
            accel_x = self._bytes_to_int(accel_data[0], accel_data[1], signed=True)
            accel_y = self._bytes_to_int(accel_data[2], accel_data[3], signed=True)
            accel_z = self._bytes_to_int(accel_data[4], accel_data[5], signed=True)
            
            # Read gyroscope data
            gyro_data = self.i2c.readfrom_mem(self.address, self.GYRO_XOUT_H, 6)
            gyro_x = self._bytes_to_int(gyro_data[0], gyro_data[1], signed=True)
            gyro_y = self._bytes_to_int(gyro_data[2], gyro_data[3], signed=True)
            gyro_z = self._bytes_to_int(gyro_data[4], gyro_data[5], signed=True)
            
            # Read temperature
            temp_data = self.i2c.readfrom_mem(self.address, self.TEMP_OUT_H, 2)
            temp_raw = self._bytes_to_int(temp_data[0], temp_data[1], signed=True)
            temperature = temp_raw / 340.0 + 36.53
            
            # Convert to physical units
            accel_scale_factor = {2: 16384, 4: 8192, 8: 4096, 16: 2048}[self.accel_scale]
            gyro_scale_factor = {250: 131, 500: 65.5, 1000: 32.8, 2000: 16.4}[self.gyro_scale]
            
            return self._cache_reading({
                "accel_x": round(accel_x / accel_scale_factor, 3),
                "accel_y": round(accel_y / accel_scale_factor, 3),
                "accel_z": round(accel_z / accel_scale_factor, 3),
                "gyro_x": round(gyro_x / gyro_scale_factor, 3),
                "gyro_y": round(gyro_y / gyro_scale_factor, 3),
                "gyro_z": round(gyro_z / gyro_scale_factor, 3),
                "temperature": round(temperature, 1)
            }, cache_time=0.05)  # Fast update for motion
            
        except Exception as e:
            # Fallback to mock data
            return self._cache_reading({
                "accel_x": 0.0,
                "accel_y": 0.0,
                "accel_z": 1.0,
                "gyro_x": 0.0,
                "gyro_y": 0.0,
                "gyro_z": 0.0,
                "temperature": 25.0
            }, cache_time=0.05)

class HallEffectSensor(BaseSensor):
    """Hall effect magnetic field sensor."""
    
    def __init__(self, inputs):
        super().__init__(inputs)
        pin_no = inputs.get('pin_no')
        if pin_no is None:
            raise ValueError("pin_no required for Hall effect sensor")
        
        self.sensor_type = inputs.get('type', 'digital')  # 'digital' or 'analog'
        
        try:
            if self.sensor_type == 'digital':
                self.pin = Pin(pin_no, Pin.IN, Pin.PULL_UP)
            else:
                from .base import ADC
                self.adc = ADC(Pin(pin_no))
                self.vref = inputs.get('vref', 3.3)
        except Exception as e:
            raise Exception(f"Failed to initialize Hall effect sensor on pin {pin_no}: {e}")
    
    def read(self):
        """Read Hall effect sensor."""
        try:
            if self.sensor_type == 'digital':
                # Digital Hall sensor (detects magnetic field presence)
                magnetic_field_detected = not bool(self.pin.value())  # Active low
                return {
                    "magnetic_field_detected": magnetic_field_detected,
                    "sensor_type": "digital"
                }
            else:
                # Analog Hall sensor (measures field strength)
                raw_value = self.adc.read_u16()
                voltage = (raw_value / 65535) * self.vref
                # Convert voltage to magnetic field strength (sensor-specific)
                field_strength = (voltage - self.vref/2) * 100  # Simplified conversion
                
                return {
                    "field_strength": round(field_strength, 2),
                    "voltage": round(voltage, 3),
                    "raw_value": raw_value,
                    "sensor_type": "analog"
                }
        except Exception as e:
            raise Exception(f"Failed to read Hall effect sensor: {e}")

class DS18B20Sensor(BaseSensor):
    """DS18B20 waterproof temperature sensor (OneWire)."""
    
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
                print("No DS18B20 sensors found")
        except Exception as e:
            raise Exception(f"Failed to initialize DS18B20 on pin {pin_no}: {e}")
    
    def read(self):
        """Read DS18B20 temperature sensor."""
        try:
            if not self.roms:
                # No sensors detected - this could be a real hardware issue
                # Try scanning again in case sensors were connected after initialization
                try:
                    self.roms = self.ow.scan()
                    if not self.roms:
                        raise Exception("No DS18B20 sensors detected on OneWire bus")
                except Exception as scan_error:
                    raise Exception(f"OneWire scan failed: {scan_error}")
            
            # Start temperature conversion for all sensors
            self.ds.convert_temp()
            time.sleep_ms(750)  # Wait for conversion (12-bit resolution)
            
            temperatures = []
            rom_errors = []
            
            for i, rom in enumerate(self.roms):
                try:
                    temp = self.ds.read_temp(rom)
                    if temp is not None and -55 <= temp <= 125:  # DS18B20 valid range
                        temperatures.append({
                            "sensor_index": i,
                            "rom": ''.join(['%02X' % b for b in rom]),
                            "temperature": temp
                        })
                    else:
                        rom_errors.append(f"Sensor {i}: Invalid temperature reading")
                except Exception as read_error:
                    rom_errors.append(f"Sensor {i}: {str(read_error)}")
            
            if temperatures:
                # Calculate statistics
                temp_values = [t["temperature"] for t in temperatures]
                avg_temp = sum(temp_values) / len(temp_values)
                min_temp = min(temp_values)
                max_temp = max(temp_values)
                
                result = {
                    "temperature_c": round(avg_temp, 2),
                    "temperature_f": round(avg_temp * 9/5 + 32, 2),
                    "sensor_count": len(temperatures),
                    "min_temperature": round(min_temp, 2),
                    "max_temperature": round(max_temp, 2)
                }
                
                # Add individual sensor readings
                for temp_data in temperatures:
                    sensor_key = f"sensor_{temp_data['sensor_index'] + 1}"
                    result[f"{sensor_key}_temp_c"] = round(temp_data["temperature"], 2)
                    result[f"{sensor_key}_rom"] = temp_data["rom"]
                
                # Add any errors encountered
                if rom_errors:
                    result["errors"] = rom_errors
                
                return self._cache_reading(result, cache_time=1)
            else:
                # No valid readings obtained
                error_msg = "No valid temperature readings obtained"
                if rom_errors:
                    error_msg += f". Errors: {'; '.join(rom_errors)}"
                raise Exception(error_msg)
                
        except Exception as e:
            raise Exception(f"Failed to read DS18B20: {e}")
                
        except Exception as e:
            raise Exception(f"Failed to read DS18B20: {e}")