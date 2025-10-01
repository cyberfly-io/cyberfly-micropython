"""
Sensor management module for CyberFly MicroPython SDK.
"""

try:
    import ujson as json
except ImportError:
    import json

import time
import gc
from micropython import const

# Sensor status constants
STATUS_SUCCESS = const(0)
STATUS_ERROR = const(1)
STATUS_DISABLED = const(2)

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

class SensorReading:
    """Standardized sensor reading with metadata."""
    __slots__ = ('sensor_id', 'sensor_type', 'data', 'timestamp', 'status', 'error')
    
    def __init__(self, sensor_id, sensor_type, data=None, timestamp=None, status="success", error=None):
        import time
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

class SensorManager:
    """Manages sensor instances."""
    
    def __init__(self):
        self.sensors = {}
        self.sensor_configs = {}
        self._config_save_hook = None
    
    def set_config_save_hook(self, callback):
        """Register a callback to persist sensor configurations."""
        self._config_save_hook = callback
    
    def _persist_configs(self):
        """Save configuration to persistent storage if callback is set."""
        if self._config_save_hook:
            try:
                configs_data = {
                    sensor_id: config.to_dict() 
                    for sensor_id, config in self.sensor_configs.items()
                }
                self._config_save_hook(configs_data)
            except Exception as e:
                print(f"Error persisting configs: {e}")
    
    def add_sensor(self, sensor_config):
        """Add a new sensor configuration."""
        if hasattr(sensor_config, 'sensor_id'):
            # New style: SensorConfig object
            sensor_id = str(sensor_config.sensor_id)
            sensor_type = sensor_config.sensor_type
            inputs = sensor_config.inputs or {}
            enabled = sensor_config.enabled
            alias = sensor_config.alias
            config = sensor_config
        else:
            # Legacy style: direct parameters
            sensor_id = str(sensor_config)
            sensor_type = inputs = enabled = alias = None
            return False
        
        # Create sensor instance
        sensor_instance = _create_sensor(sensor_type, inputs)
        if sensor_instance is None:
            raise ValueError(f"Unknown sensor type: {sensor_type}")
        
        self.sensor_configs[sensor_id] = config
        self.sensors[sensor_id] = sensor_instance
        self._persist_configs()
        
        return True
    
    def remove_sensor(self, sensor_id):
        """Remove a sensor configuration."""
        sensor_id = str(sensor_id)
        if sensor_id in self.sensor_configs:
            del self.sensor_configs[sensor_id]
            if sensor_id in self.sensors:
                del self.sensors[sensor_id]
            self._persist_configs()
            return True
        return False
    
    def read_sensor(self, sensor_id):
        """Read data from a specific sensor."""
        from .base_sensors import SensorReading
        
        sensor_id = str(sensor_id)
        if sensor_id not in self.sensors:
            return SensorReading(sensor_id, "unknown", status="error", error=f"Sensor '{sensor_id}' not found")
        
        config = self.sensor_configs[sensor_id]
        if not config.enabled:
            return SensorReading(sensor_id, config.sensor_type, status="disabled")
        
        try:
            sensor = self.sensors[sensor_id]
            data = sensor.read()
            return SensorReading(sensor_id, config.sensor_type, data=data, status="success")
        except Exception as e:
            return SensorReading(sensor_id, config.sensor_type, status="error", error=str(e))
    
    def read_all_sensors(self):
        """Read data from all enabled sensors."""
        readings = []
        for sensor_id, config in self.sensor_configs.items():
            if config.enabled and sensor_id in self.sensors:
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
                sensor_instance = _create_sensor(config.sensor_type, config.inputs)
                if sensor_instance is not None:
                    self.sensor_configs[sensor_id] = config
                    self.sensors[sensor_id] = sensor_instance
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
            
            elif action == 'enable_sensor':
                success = self.enable_sensor(command_data['sensor_id'])
                return {"status": "success" if success else "error"}
            
            elif action == 'disable_sensor':
                success = self.disable_sensor(command_data['sensor_id'])
                return {"status": "success" if success else "error"}
            
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
    from .base_sensors import AnalogSensor, DigitalSensor
    
    sensor_map = {
        'analog': AnalogSensor,
        'digital': DigitalSensor,
    }
    
    sensor_class = sensor_map.get(sensor_type.lower())
    if sensor_class:
        try:
            return sensor_class(inputs)
        except Exception as e:
            print(f"Error creating sensor {sensor_type}: {e}")
            return None
    return None

# Export the main interface
__all__ = ['SensorManager', 'SensorConfig', 'SensorReading', 'STATUS_SUCCESS', 'STATUS_ERROR', 'STATUS_DISABLED']
