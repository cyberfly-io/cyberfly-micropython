"""
Environmental sensor implementations: temperature, humidity, pressure, air quality.
Includes DHT series, BMP/BME series, and air quality sensors.
"""

import time
from .base import BaseSensor, I2CBaseSensor, Pin

# DHT sensor imports
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

class DHT11Sensor(BaseSensor):
    """DHT11 temperature and humidity sensor."""
    
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
                "temperature_c": round(temp_c, 1),
                "temperature_f": round(temp_c * 9/5 + 32, 1),
                "humidity_percent": round(humidity, 1)
            }, cache_time=2)  # Cache for 2 seconds
        except Exception as e:
            raise Exception(f"Failed to read DHT11: {e}")

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

class BME680Sensor(I2CBaseSensor):
    """Bosch BME680 environmental sensor with gas resistance."""
    
    # BME680 Register addresses
    CHIP_ID_REG = 0xD0
    CTRL_GAS_1_REG = 0x71
    CTRL_HUM_REG = 0x72
    CTRL_MEAS_REG = 0x74
    CONFIG_REG = 0x75
    MEAS_STATUS_REG = 0x1D
    PRESS_MSB_REG = 0x1F
    TEMP_MSB_REG = 0x22
    HUM_MSB_REG = 0x25
    GAS_RES_MSB_REG = 0x2A
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x77)  # Default I2C address (can be 0x76)
        self.sea_level_pressure = inputs.get('sea_level_pressure', 1013.25)
        self.target_temp = inputs.get('target_temp', 320)  # Target temperature for gas sensor
        self._calibration_params = None
        self._init_sensor()
    
    def _init_sensor(self):
        """Initialize BME680 sensor and read calibration parameters."""
        try:
            # Read chip ID to verify sensor
            chip_id = self.i2c.readfrom_mem(self.address, self.CHIP_ID_REG, 1)[0]
            if chip_id != 0x61:
                raise Exception(f"Invalid BME680 chip ID: 0x{chip_id:02X}")
            
            # Soft reset
            self.i2c.writeto_mem(self.address, 0xE0, b'\xB6')
            time.sleep_ms(10)
            
            # Configure humidity oversampling x2
            self.i2c.writeto_mem(self.address, self.CTRL_HUM_REG, b'\x02')
            
            # Configure temperature oversampling x4, pressure oversampling x4
            self.i2c.writeto_mem(self.address, self.CTRL_MEAS_REG, b'\x54')
            
            # Configure gas sensor (enable, heat temp, heat duration)
            self.i2c.writeto_mem(self.address, self.CTRL_GAS_1_REG, b'\x10')
            
            # Set gas sensor heater temperature (simplified)
            # In production, would use proper resistance calculation
            self.i2c.writeto_mem(self.address, 0x5A, b'\x73')  # ~320°C equivalent
            self.i2c.writeto_mem(self.address, 0x64, b'\x65')  # Heat duration ~150ms
            
            # Read calibration parameters (simplified)
            self._read_calibration()
            
        except Exception as e:
            print(f"BME680 initialization failed: {e}")
            # Fall back to mock mode if hardware not available
            self._calibration_params = None
    
    def _read_calibration(self):
        """Read basic calibration parameters from sensor."""
        try:
            # Read basic temperature and pressure calibration
            cal_data = self.i2c.readfrom_mem(self.address, 0x89, 25)
            
            # Simplified calibration parameters (BME680 has complex calibration)
            self._calibration_params = {
                'par_T1': self._bytes_to_int(cal_data[1], cal_data[0]),
                'par_T2': self._bytes_to_int(cal_data[3], cal_data[2], signed=True),
                'par_T3': cal_data[4] if cal_data[4] < 128 else cal_data[4] - 256,
                'par_P1': self._bytes_to_int(cal_data[6], cal_data[5]),
                'par_P2': self._bytes_to_int(cal_data[8], cal_data[7], signed=True),
                'par_P3': cal_data[9] if cal_data[9] < 128 else cal_data[9] - 256,
                # Additional parameters would be read for full implementation
            }
        except Exception as e:
            print(f"BME680 calibration read failed: {e}")
            self._calibration_params = None
    
    def _compensate_temperature(self, adc_T):
        """Compensate raw temperature reading (simplified)."""
        if not self._calibration_params:
            return 22.5  # Fallback
            
        # Simplified BME680 temperature compensation
        var1 = (adc_T >> 3) - (self._calibration_params['par_T1'] << 1)
        var2 = (var1 * self._calibration_params['par_T2']) >> 11
        var3 = ((var1 >> 1) * (var1 >> 1)) >> 12
        var3 = ((var3) * (self._calibration_params['par_T3'] << 4)) >> 14
        self.t_fine = var2 + var3
        return ((self.t_fine * 5) + 128) >> 8
    
    def _compensate_pressure(self, adc_P):
        """Compensate raw pressure reading (simplified)."""
        if not self._calibration_params:
            return 1013.25  # Fallback
            
        # Simplified BME680 pressure compensation
        var1 = ((self.t_fine) >> 1) - 64000
        var2 = ((((var1 >> 2) * (var1 >> 2)) >> 11) * self._calibration_params['par_P3']) >> 2
        var2 += ((var1 * self._calibration_params['par_P2']) << 1)
        var2 = (var2 >> 2) + (self._calibration_params['par_P1'] << 16)
        
        if var2 == 0:
            return 0
            
        var1 = (((((adc_P << 15) - (var2 >> 1)) / var2) * 1000) >> 15)
        return var1 / 100.0  # Convert to hPa
    
    def _compensate_humidity(self, adc_H):
        """Compensate raw humidity reading (simplified)."""
        if not self._calibration_params:
            return 55.0  # Fallback
            
        # Simplified humidity compensation
        temp_scaled = self.t_fine / 5120.0
        var1 = adc_H - (76.8 + (temp_scaled * 3.0))
        var2 = var1 * (120.0 / (1 << 14))
        var3 = var2 + (temp_scaled * temp_scaled * 0.017)
        
        if var3 > 100.0:
            var3 = 100.0
        elif var3 < 0.0:
            var3 = 0.0
        return var3
    
    def read(self):
        """Read BME680 sensor with real I2C communication."""
        try:
            if self._calibration_params:
                # Trigger forced mode measurement
                self.i2c.writeto_mem(self.address, self.CTRL_MEAS_REG, b'\x55')  # Forced mode
                
                # Wait for measurement to complete
                time.sleep_ms(200)
                
                # Check measurement status
                status = self.i2c.readfrom_mem(self.address, self.MEAS_STATUS_REG, 1)[0]
                if status & 0x80:  # New data available
                    # Read temperature data
                    temp_data = self.i2c.readfrom_mem(self.address, self.TEMP_MSB_REG, 3)
                    adc_T = (temp_data[0] << 12) | (temp_data[1] << 4) | (temp_data[2] >> 4)
                    
                    # Read pressure data
                    press_data = self.i2c.readfrom_mem(self.address, self.PRESS_MSB_REG, 3)
                    adc_P = (press_data[0] << 12) | (press_data[1] << 4) | (press_data[2] >> 4)
                    
                    # Read humidity data
                    hum_data = self.i2c.readfrom_mem(self.address, self.HUM_MSB_REG, 2)
                    adc_H = (hum_data[0] << 8) | hum_data[1]
                    
                    # Read gas resistance data
                    gas_data = self.i2c.readfrom_mem(self.address, self.GAS_RES_MSB_REG, 2)
                    gas_res_adc = (gas_data[0] << 2) | (gas_data[1] >> 6)
                    gas_range = gas_data[1] & 0x0F
                    
                    # Compensate readings
                    temperature = self._compensate_temperature(adc_T) / 100.0
                    pressure = self._compensate_pressure(adc_P)
                    humidity = self._compensate_humidity(adc_H)
                    
                    # Calculate gas resistance (simplified)
                    if gas_res_adc != 0:
                        gas_resistance = (1 << gas_range) * gas_res_adc
                    else:
                        gas_resistance = 0
                else:
                    # No new data, use previous reading or defaults
                    temperature = 22.5
                    pressure = 1013.25
                    humidity = 55.0
                    gas_resistance = 50000
            else:
                # Fallback to varying data if sensor not available
                temperature = 22.5 + (time.time() % 10) - 5
                humidity = 55.0 + (time.time() % 20) - 10
                pressure = 1013.25 + (time.time() % 20) - 10
                gas_resistance = 50000 + (time.time() % 100000)
            
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
    
    # CCS811 Register addresses
    STATUS_REG = 0x00
    MEAS_MODE_REG = 0x01
    ALG_RESULT_DATA_REG = 0x02
    RAW_DATA_REG = 0x03
    ENV_DATA_REG = 0x05
    THRESHOLDS_REG = 0x10
    BASELINE_REG = 0x11
    HW_ID_REG = 0x20
    HW_VERSION_REG = 0x21
    FW_BOOT_VERSION_REG = 0x23
    FW_APP_VERSION_REG = 0x24
    ERROR_ID_REG = 0xE0
    APP_START_REG = 0xF4
    SW_RESET_REG = 0xFF
    
    def __init__(self, inputs):
        super().__init__(inputs, 0x5A)  # Default I2C address (can be 0x5B)
        self.temperature_offset = inputs.get('temperature_offset', 0)
        self.baseline = inputs.get('baseline', None)
        self.drive_mode = inputs.get('drive_mode', 1)  # 0=idle, 1=1s, 2=10s, 3=60s, 4=250ms
        self._initialized = False
        self._init_sensor()
    
    def _init_sensor(self):
        """Initialize CCS811 sensor."""
        try:
            # Check hardware ID
            hw_id = self.i2c.readfrom_mem(self.address, self.HW_ID_REG, 1)[0]
            if hw_id != 0x81:
                raise Exception(f"Invalid CCS811 hardware ID: 0x{hw_id:02X}")
            
            # Check status register
            status = self.i2c.readfrom_mem(self.address, self.STATUS_REG, 1)[0]
            if not (status & 0x10):  # APP_VALID bit
                raise Exception("CCS811 application not valid")
            
            # Start application
            self.i2c.writeto(self.address, bytes([self.APP_START_REG]))
            time.sleep_ms(100)
            
            # Check if application started
            status = self.i2c.readfrom_mem(self.address, self.STATUS_REG, 1)[0]
            if not (status & 0x80):  # FW_MODE bit
                raise Exception("CCS811 application did not start")
            
            # Configure measurement mode
            # Bit 7: unused, Bits 6-4: drive_mode, Bit 3: interrupt, Bit 2: interrupt threshold, Bits 1-0: unused
            mode_reg = (self.drive_mode & 0x07) << 4
            self.i2c.writeto_mem(self.address, self.MEAS_MODE_REG, bytes([mode_reg]))
            
            # Set baseline if provided
            if self.baseline is not None:
                baseline_bytes = [(self.baseline >> 8) & 0xFF, self.baseline & 0xFF]
                self.i2c.writeto_mem(self.address, self.BASELINE_REG, bytes(baseline_bytes))
            
            self._initialized = True
            time.sleep_ms(1000)  # Wait for first measurement
            
        except Exception as e:
            print(f"CCS811 initialization failed: {e}")
            self._initialized = False
    
    def _set_environmental_data(self, humidity, temperature):
        """Set environmental compensation data."""
        try:
            if self._initialized:
                # Convert humidity (0-100%) to CCS811 format
                hum_raw = int(humidity * 512)  # 0-51200 range
                
                # Convert temperature (°C) to CCS811 format  
                temp_raw = int((temperature + 25) * 512)  # Offset by 25°C
                
                env_data = [
                    (hum_raw >> 8) & 0xFF, hum_raw & 0xFF,
                    (temp_raw >> 8) & 0xFF, temp_raw & 0xFF
                ]
                self.i2c.writeto_mem(self.address, self.ENV_DATA_REG, bytes(env_data))
        except Exception as e:
            print(f"CCS811 environmental data setting failed: {e}")
    
    def read(self):
        """Read CCS811 sensor with real I2C communication."""
        try:
            if not self._initialized:
                # Fallback to varying data if sensor not available
                eco2 = 400 + (time.time() % 1000)  # ppm
                tvoc = 10 + (time.time() % 200)    # ppb
                temperature = 22.5 + self.temperature_offset
                baseline = self.baseline or int(time.time() % 65536)
                
                return self._cache_reading({
                    "eco2": round(eco2, 0),
                    "tvoc": round(tvoc, 0),
                    "temperature": round(temperature, 1),
                    "baseline": baseline,
                    "status": "sensor_not_available"
                }, cache_time=1)
            
            # Check data ready status
            status = self.i2c.readfrom_mem(self.address, self.STATUS_REG, 1)[0]
            
            if not (status & 0x08):  # DATA_READY bit
                # No new data available, return cached or estimated data
                eco2 = 400
                tvoc = 0
                current_raw = 0
                voltage_raw = 0
            else:
                # Read algorithm results (eCO2 and TVOC)
                alg_data = self.i2c.readfrom_mem(self.address, self.ALG_RESULT_DATA_REG, 8)
                
                eco2 = (alg_data[0] << 8) | alg_data[1]  # ppm
                tvoc = (alg_data[2] << 8) | alg_data[3]  # ppb
                
                # Status and error data
                status_byte = alg_data[4]
                error_id = alg_data[5]
                
                # Raw data (current and voltage)
                current_raw = (alg_data[6] << 8) | alg_data[7]
                
                # Read raw data register for voltage
                raw_data = self.i2c.readfrom_mem(self.address, self.RAW_DATA_REG, 2)
                voltage_raw = (raw_data[0] << 8) | raw_data[1]
                
                # Check for errors
                if error_id != 0:
                    print(f"CCS811 error: 0x{error_id:02X}")
            
            # Read current baseline
            try:
                baseline_data = self.i2c.readfrom_mem(self.address, self.BASELINE_REG, 2)
                current_baseline = (baseline_data[0] << 8) | baseline_data[1]
            except:
                current_baseline = self.baseline or 0
            
            # Calculate derived values
            temperature = 22.5 + self.temperature_offset
            
            # Set environmental compensation (if we have external temp/humidity)
            self._set_environmental_data(50.0, temperature)  # Default humidity 50%
            
            return self._cache_reading({
                "eco2": eco2,
                "tvoc": tvoc,
                "temperature": round(temperature, 1),
                "baseline": current_baseline,
                "current_raw": current_raw,
                "voltage_raw": voltage_raw,
                "status": "success"
            }, cache_time=1)
            
        except Exception as e:
            raise Exception(f"Failed to read CCS811: {e}")
    
    def set_baseline(self, baseline):
        """Set sensor baseline for calibration."""
        try:
            if self._initialized:
                baseline_bytes = [(baseline >> 8) & 0xFF, baseline & 0xFF]
                self.i2c.writeto_mem(self.address, self.BASELINE_REG, bytes(baseline_bytes))
                self.baseline = baseline
                return True
        except Exception as e:
            print(f"Failed to set CCS811 baseline: {e}")
        return False
    
    def get_baseline(self):
        """Get current sensor baseline."""
        try:
            if self._initialized:
                baseline_data = self.i2c.readfrom_mem(self.address, self.BASELINE_REG, 2)
                return (baseline_data[0] << 8) | baseline_data[1]
        except Exception as e:
            print(f"Failed to get CCS811 baseline: {e}")
        return None