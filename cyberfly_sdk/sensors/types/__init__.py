"""
Sensor types module - organized sensor implementations by category.
"""

# Re-export all sensor classes for convenience
from .base import SensorReading, BaseSensor, I2CBaseSensor
from .basic_sensors import InternalTempSensor, DigitalInputSensor, AnalogInputSensor, SystemInfoSensor
from .environmental_sensors import DHT22Sensor, DHT11Sensor, BMP280Sensor, BME280Sensor, BME680Sensor, CCS811Sensor
from .light_sensors import BH1750Sensor, TSL2561Sensor, APDS9960Sensor
from .motion_sensors import PIRSensor, UltrasonicSensor, MPU6050Sensor, HallEffectSensor, DS18B20Sensor