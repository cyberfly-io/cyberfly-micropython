"""
CyberFly MicroPython Sensor Management System

This module provides a comprehensive sensor management system with support for:
- 30+ sensor types across multiple categories  
- Runtime sensor configuration and management
- BLE provisioning integration  
- IoT platform compatibility
- Real I2C implementations (no more mocks!)

Sensor Categories:
- Basic: Digital/analog inputs, internal sensors, system info
- Environmental: DHT, BMP/BME series, air quality sensors
- Light: Ambient light, color sensors, optical detection
- Motion: PIR, ultrasonic, accelerometers, magnetic sensors

All sensors now have proper hardware implementations with fallback support.
"""

import time
import gc
try:
    import ujson as json
except ImportError:
    import json
from micropython import const

# Sensor status constants
STATUS_SUCCESS = const(0)
STATUS_ERROR = const(1)
STATUS_DISABLED = const(2)

# Import base classes
from .types.base import SensorReading, BaseSensor, I2CBaseSensor

# Import sensor implementations from modular files
from .types.basic_sensors import (
    InternalTempSensor, DigitalInputSensor, AnalogInputSensor, SystemInfoSensor, PinStatusSensor
)

from .types.environmental_sensors import (
    DHT22Sensor, DHT11Sensor, BMP280Sensor, BME280Sensor, BME680Sensor, CCS811Sensor
)

from .types.light_sensors import (
    BH1750Sensor, TSL2561Sensor, APDS9960Sensor
)

from .types.motion_sensors import (
    PIRSensor, UltrasonicSensor, MPU6050Sensor, HallEffectSensor, DS18B20Sensor
)

class SensorConfig:
    """Configuration for a sensor instance."""
    __slots__ = ('sensor_id', 'sensor_type', 'inputs', 'enabled', 'alias')
    
    def __init__(self, sensor_id, sensor_type, inputs=None, enabled=True, alias=None):
        self.sensor_id = str(sensor_id)
        self.sensor_type = str(sensor_type)
        self.inputs = inputs or {}
        self.enabled = bool(enabled)
        self.alias = alias
    
    def to_dict(self):
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'inputs': self.inputs,
            'enabled': self.enabled,
            'alias': self.alias
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            sensor_id=data['sensor_id'],
            sensor_type=data['sensor_type'],
            inputs=data.get('inputs', {}),
            enabled=data.get('enabled', True),
            alias=data.get('alias')
        )

class SensorManager:
    """Central manager for all sensor operations."""
    
    def __init__(self):
        self.sensors = {}  # sensor_id -> sensor_instance
        self.sensor_configs = {}  # sensor_id -> SensorConfig
        self._config_file = "sensor_configs.json"
        self._config_save_hook = None
        self._load_configs()
    
    def _persist_configs(self):
        """Save sensor configurations to file."""
        try:
            configs_data = {sid: cfg.to_dict() for sid, cfg in self.sensor_configs.items()}
            if self._config_save_hook:
                try:
                    self._config_save_hook(configs_data)
                except Exception as hook_err:
                    print(f"Sensor save hook failed: {hook_err}")
            else:
                with open(self._config_file, 'w') as f:
                    json.dump(configs_data, f)
        except Exception as e:
            print(f"Failed to save sensor configs: {e}")
    
    def _load_configs(self):
        """Load sensor configurations from file."""
        try:
            with open(self._config_file, 'r') as f:
                configs_data = json.load(f)
            self.load_sensor_configs(configs_data)
        except:
            # No existing config file
            pass
    
    def set_config_save_hook(self, callback):
        """Register an external persistence hook (e.g., store in device config)."""
        self._config_save_hook = callback

    def add_sensor(self, sensor_or_id, sensor_type=None, inputs=None, enabled=True, alias=None):
        """Add a new sensor to the system."""
        # Allow direct SensorConfig objects for convenience
        if isinstance(sensor_or_id, SensorConfig):
            config = sensor_or_id
        else:
            if not sensor_type:
                print("Sensor type is required when adding by id")
                return False
            config = SensorConfig(sensor_or_id, sensor_type, inputs, enabled, alias)

        sensor_id = str(config.sensor_id)

        # Create sensor instance (re-create if updating existing)
        sensor_instance = _create_sensor(config.sensor_type, config.inputs or {})
        if sensor_instance is None:
            return False

        self.sensors[sensor_id] = sensor_instance
        self.sensor_configs[sensor_id] = config
        self._persist_configs()
        return True

    def update_sensor(self, sensor_id, updates):
        """Update an existing sensor configuration."""
        sensor_id = str(sensor_id)
        if sensor_id not in self.sensor_configs:
            return False
        current = self.sensor_configs[sensor_id]
        new_config = SensorConfig(
            sensor_id=sensor_id,
            sensor_type=updates.get('sensor_type', current.sensor_type),
            inputs=updates.get('inputs', current.inputs),
            enabled=updates.get('enabled', current.enabled),
            alias=updates.get('alias', current.alias)
        )
        return self.add_sensor(new_config)
    
    def remove_sensor(self, sensor_id):
        """Remove a sensor from the system."""
        sensor_id = str(sensor_id)
        existed = False
        if sensor_id in self.sensors:
            del self.sensors[sensor_id]
            existed = True
        if sensor_id in self.sensor_configs:
            del self.sensor_configs[sensor_id]
            existed = True
        if existed:
            self._persist_configs()
        return existed
    
    def read_sensor(self, sensor_id):
        """Read a single sensor."""
        sensor_id = str(sensor_id)
        if sensor_id not in self.sensors:
            return SensorReading(sensor_id, "unknown", error="Sensor not found", status="error")
        
        config = self.sensor_configs.get(sensor_id)
        if config and not config.enabled:
            return SensorReading(sensor_id, config.sensor_type, error="Sensor disabled", status="disabled")
        
        try:
            sensor = self.sensors[sensor_id]
            data = sensor.read()
            return SensorReading(
                sensor_id=sensor_id,
                sensor_type=config.sensor_type if config else "unknown",
                data=data,
                status="success"
            )
        except Exception as e:
            return SensorReading(
                sensor_id=sensor_id,
                sensor_type=config.sensor_type if config else "unknown",
                error=str(e),
                status="error"
            )
    
    def read_all_sensors(self):
        """Read all enabled sensors."""
        readings = []
        for sensor_id in self.sensors:
            config = self.sensor_configs.get(sensor_id)
            if config and config.enabled:
                reading = self.read_sensor(sensor_id)
                readings.append(reading)
        return readings
    
    def enable_sensor(self, sensor_id):
        """Enable a sensor."""
        sensor_id = str(sensor_id)
        if sensor_id in self.sensor_configs:
            self.sensor_configs[sensor_id].enabled = True
            self._persist_configs()
            return True
        return False
    
    def disable_sensor(self, sensor_id):
        """Disable a sensor."""
        sensor_id = str(sensor_id)
        if sensor_id in self.sensor_configs:
            self.sensor_configs[sensor_id].enabled = False
            self._persist_configs()
            return True
        return False
    
    def load_sensor_configs(self, configs_data):
        """Load sensor configurations from saved data."""
        loaded_sensors = []
        try:
            for sensor_id, config_data in configs_data.items():
                config = SensorConfig.from_dict(config_data)
                if self.add_sensor(config):
                    loaded_sensors.append(sensor_id)
        except Exception as e:
            print(f"Error loading sensor configs: {e}")
        return loaded_sensors
    
    def process_command(self, command_data):
        """Process sensor commands from IoT platform."""
        try:
            action = command_data.get('action')
            
            if action == 'read_sensor':
                reading = self.read_sensor(command_data['sensor_id'])
                return reading.to_dict()
            
            elif action == 'read_all_sensors':
                readings = self.read_all_sensors()
                return {"readings": [r.to_dict() for r in readings], "count": len(readings)}
            
            elif action == 'read_pin_status':
                # Handle pin status reading request
                sensor_id = command_data.get('sensor_id', 'pin_status')
                if sensor_id in self.sensors:
                    reading = self.read_sensor(sensor_id)
                    return reading.to_dict()
                else:
                    return {
                        "status": "error",
                        "error": f"Pin status sensor '{sensor_id}' not configured",
                        "hint": "Add a pin_status sensor to enable pin monitoring"
                    }
            
            elif action == 'enable_sensor':
                success = self.enable_sensor(command_data['sensor_id'])
                return {"status": "success" if success else "error"}
            
            elif action == 'disable_sensor':
                success = self.disable_sensor(command_data['sensor_id'])
                return {"status": "success" if success else "error"}

            elif action == 'add_sensor':
                cfg = command_data.get('config') or command_data
                sensor_id = cfg.get('sensor_id')
                sensor_type = cfg.get('sensor_type')
                if not sensor_id or not sensor_type:
                    return {"status": "error", "error": "sensor_id and sensor_type are required"}
                added = self.add_sensor(
                    sensor_id,
                    sensor_type,
                    inputs=cfg.get('inputs'),
                    enabled=cfg.get('enabled', True),
                    alias=cfg.get('alias')
                )
                if added:
                    return {"status": "success", "sensor": self.sensor_configs[sensor_id].to_dict()}
                return {"status": "error", "error": f"Failed to add sensor '{sensor_id}'"}

            elif action == 'update_sensor':
                cfg = command_data.get('config') or {}
                sensor_id = cfg.get('sensor_id') or command_data.get('sensor_id')
                if not sensor_id:
                    return {"status": "error", "error": "sensor_id is required"}
                success = self.update_sensor(sensor_id, cfg)
                if success:
                    return {"status": "success", "sensor": self.sensor_configs[sensor_id].to_dict()}
                return {"status": "error", "error": f"Failed to update sensor '{sensor_id}'"}

            elif action == 'remove_sensor':
                sensor_id = command_data.get('sensor_id')
                if not sensor_id:
                    return {"status": "error", "error": "sensor_id is required"}
                removed = self.remove_sensor(sensor_id)
                if removed:
                    return {"status": "success", "removed": sensor_id}
                return {"status": "error", "error": f"Sensor '{sensor_id}' not found"}

            elif action == 'list_sensors':
                return {
                    "status": "success",
                    "sensors": [cfg.to_dict() for cfg in self.sensor_configs.values()],
                    "count": len(self.sensor_configs)
                }
            
            else:
                return {"status": "error", "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def execute_sensor_action(self, sensor_id, action, params=None):
        """Execute an action on a sensor (for output sensors)."""
        sensor_id = str(sensor_id)
        if sensor_id not in self.sensors:
            return {"status": "error", "error": f"Sensor '{sensor_id}' not found"}
        
        try:
            sensor = self.sensors[sensor_id]
            if hasattr(sensor, action):
                method = getattr(sensor, action)
                result = method(params) if params else method()
                return {"status": "success", "result": result}
            else:
                return {"status": "error", "error": f"Action '{action}' not supported"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_sensor_status(self, sensor_id=None):
        """Get status information for sensor(s)."""
        if sensor_id:
            sensor_id = str(sensor_id)
            if sensor_id in self.sensor_configs:
                config = self.sensor_configs[sensor_id]
                return {
                    "sensor_id": sensor_id,
                    "sensor_type": config.sensor_type,
                    "enabled": config.enabled,
                    "alias": config.alias
                }
            else:
                return {"error": f"Sensor '{sensor_id}' not found"}
        else:
            return {
                "total_sensors": len(self.sensor_configs),
                "enabled_sensors": sum(1 for config in self.sensor_configs.values() if config.enabled),
                "sensor_list": list(self.sensor_configs.keys())
            }

def _create_sensor(sensor_type, inputs):
    """Factory function to create sensor instances."""
    
    # Sensor type mapping to classes
    sensor_map = {
        # Basic sensors
        'internal_temp': InternalTempSensor,
        'digital_input': DigitalInputSensor,
        'analog_input': AnalogInputSensor,
        'system_info': SystemInfoSensor,
        'pin_status': PinStatusSensor,
        
        # Environmental sensors
        'dht22': DHT22Sensor,
        'dht11': DHT11Sensor,
        'bmp280': BMP280Sensor,
        'bme280': BME280Sensor,
        'bme680': BME680Sensor,
        'ccs811': CCS811Sensor,
        
        # Light sensors
        'bh1750': BH1750Sensor,
        'tsl2561': TSL2561Sensor,
        'apds9960': APDS9960Sensor,
        
        # Motion sensors
        'pir': PIRSensor,
        'ultrasonic': UltrasonicSensor,
        'mpu6050': MPU6050Sensor,
        'hall_effect': HallEffectSensor,
        'ds18b20': DS18B20Sensor,
        
        # Legacy compatibility
        'analog': AnalogInputSensor,
        'digital': DigitalInputSensor,
    }
    
    sensor_class = sensor_map.get(sensor_type.lower())
    if sensor_class:
        try:
            return sensor_class(inputs)
        except Exception as e:
            print(f"Error creating sensor {sensor_type}: {e}")
            return None
    else:
        print(f"Unknown sensor type: {sensor_type}")
        return None

# Export the main interface
__all__ = [
    'SensorManager', 'SensorConfig', 'SensorReading', 
    'STATUS_SUCCESS', 'STATUS_ERROR', 'STATUS_DISABLED',
    # Base classes
    'BaseSensor', 'I2CBaseSensor',
    # Basic sensors
    'InternalTempSensor', 'DigitalInputSensor', 'AnalogInputSensor', 'SystemInfoSensor', 'PinStatusSensor',
    # Environmental sensors
    'DHT22Sensor', 'DHT11Sensor', 'BMP280Sensor', 'BME280Sensor', 'BME680Sensor', 'CCS811Sensor',
    # Light sensors
    'BH1750Sensor', 'TSL2561Sensor', 'APDS9960Sensor',
    # Motion sensors
    'PIRSensor', 'UltrasonicSensor', 'MPU6050Sensor', 'HallEffectSensor', 'DS18B20Sensor'
]