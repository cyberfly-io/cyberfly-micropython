from cmqtt import MQTTClient
import shipper_utils
import api
import auth
import cntptime
import time
from module_registry import ModuleRegistry
from actuators.led import LedModule
from sensors import SensorManager, SensorConfig
from config import load_config, save_config
import json
import machine

class CyberflyClient:
    def __init__(self, device_id, key_pair, ssid, wifi_password, network_id = "mainnet01", node_url="https://node.cyberfly.io"):
        self.ssid = ssid
        self.wifi_password = wifi_password
        self.key_pair = key_pair
        self.network_id = network_id
        if machine:
            self.led = machine.Pin(2, machine.Pin.OUT)
        else:
            class _DummyLed:
                def value(self, *_):
                    return 0
            self.led = _DummyLed()
        self.device_data = {}
        self.device_id = device_id
        self.account = "k:" + self.key_pair.get("publicKey")
        self.caller = self.default_caller
        self.mqtt_server = node_url.split("//")[1]
        self.node_url = node_url
        self.mqtt_client = MQTTClient(device_id, self.mqtt_server, port=31004)
        self.topic = device_id
        self.mqtt_client.set_callback(self.on_received)
        self.device_info = {}
        # optional module system for dynamic read/execute
        try:
            self.modules = ModuleRegistry()
            # Auto-register available modules from actuators/ and sensors/
            self.modules.register_all()
            # Ensure a basic LED exists as a fallback
            if not self.modules.get('led'):
                self.modules.add(LedModule("led", pin=2, active_high=True))
        except Exception:
            # Safe if support files not present during import-time checks
            self.modules = None
        
        # Initialize sensor management
        try:
            self.sensor_manager = SensorManager()
            # Set up config save hook to persist sensor configurations
            self.sensor_manager.set_config_save_hook(self._save_sensor_configs)
            # Load any existing sensor configurations
            self._load_sensor_configs()
        except Exception as e:
            print(f"Failed to initialize sensor manager: {e}")
            self.sensor_manager = None
        self.connect_wifi(ssid, wifi_password)
        self.set_ntptime()
        self.update_device()
        self.connect_mqtt()

    @staticmethod
    def boot(button_pin=0, long_ms=3000, ble=True, ble_timeout=300):
        import time
        import machine
        cfg = load_config()
        trigger = False
        if machine:
            try:
                btn = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
                if btn.value() == 0:
                    t0 = time.ticks_ms()
                    while btn.value() == 0:
                        if time.ticks_diff(time.ticks_ms(), t0) > long_ms:
                            trigger = True
                            break
                        time.sleep_ms(50)
            except Exception:
                pass
        if not cfg or trigger:
            if ble:
                try:
                    from .ble_provision import provision
                except Exception:
                    from ble_provision import provision
                print("Entering BLE provisioning...")
                saved = provision(timeout_s=ble_timeout, log=True, auto_reset=True)
                if saved:
                    return None  # device will reset
                else:
                    print("BLE provisioning timeout; rebooting")
                    try:
                        import machine
                        machine.reset()
                    except:
                        pass
                    return None
        kp = cfg.get('key_pair') or {"publicKey": "", "secretKey": ""}
        return CyberflyClient(
            device_id=cfg.get('device_id', ''),
            key_pair=kp,
            ssid=cfg.get('ssid', ''),
            wifi_password=cfg.get('wifi_password', ''),
            network_id=cfg.get('network_id', 'mainnet01'),
        )

    def register_modules(self, *mods):
        if self.modules is None:
            self.modules = ModuleRegistry()
        self.modules.add(*mods)
    
    # Sensor Management Methods
    
    def add_sensor(self, sensor_id, sensor_type, inputs=None, enabled=True, alias=None):
        """Add a sensor to this device."""
        if not self.sensor_manager:
            print("Sensor manager not available")
            return False
        
        config = SensorConfig(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            inputs=inputs or {},
            enabled=enabled,
            alias=alias
        )
        return self.sensor_manager.add_sensor(config)
    
    def remove_sensor(self, sensor_id):
        """Remove a sensor from this device."""
        if not self.sensor_manager:
            return False
        return self.sensor_manager.remove_sensor(sensor_id)
    
    def read_sensor(self, sensor_id):
        """Read data from a specific sensor."""
        if not self.sensor_manager:
            return {"error": "Sensor manager not available"}
        reading = self.sensor_manager.read_sensor(sensor_id)
        return reading.to_dict()
    
    def read_all_sensors(self):
        """Read data from all enabled sensors."""
        if not self.sensor_manager:
            return []
        readings = self.sensor_manager.read_all_sensors()
        return [r.to_dict() for r in readings]
    
    def execute_sensor_action(self, sensor_id, action, params=None):
        """Execute an action on a sensor (for output sensors)."""
        if not self.sensor_manager:
            return {"error": "Sensor manager not available"}
        return self.sensor_manager.execute_sensor_action(sensor_id, action, params)
    
    def get_sensor_status(self, sensor_id=None):
        """Get status information for sensor(s)."""
        if not self.sensor_manager:
            return {"error": "Sensor manager not available"}
        return self.sensor_manager.get_sensor_status(sensor_id)
    
    def enable_sensor(self, sensor_id):
        """Enable a sensor."""
        if not self.sensor_manager:
            return False
        return self.sensor_manager.enable_sensor(sensor_id)
    
    def disable_sensor(self, sensor_id):
        """Disable a sensor."""
        if not self.sensor_manager:
            return False
        return self.sensor_manager.disable_sensor(sensor_id)
    
    def load_sensor_configs(self, configs):
        """Load multiple sensor configurations."""
        if not self.sensor_manager:
            return []
        return self.sensor_manager.load_sensor_configs(configs)
    
    def process_sensor_command(self, command):
        """Process a sensor command from the IoT platform."""
        if not self.sensor_manager:
            return {"error": "Sensor manager not available"}
        
        # Check for read_pin_status command with auto-creation
        action = command.get('action')
        if action == 'read_pin_status':
            # Auto-create pin status sensor if not exists
            sensor_id = command.get('sensor_id', 'pin_status')
            if sensor_id not in self.sensor_manager.sensors:
                print(f"Auto-creating pin status sensor '{sensor_id}'...")
                # Create with default common GPIO pins
                default_pins = [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23]
                success = self.add_sensor(
                    sensor_id=sensor_id,
                    sensor_type="pin_status",
                    inputs={"pins": default_pins, "mode": "auto"},
                    alias="GPIO Pin Status Monitor"
                )
                if not success:
                    return {
                        "status": "error",
                        "error": "Failed to create pin status sensor",
                        "action": action
                    }
            
            # Read and return pin status
            reading = self.read_sensor(sensor_id)
            if reading.get('status') == 'success':
                return {
                    "status": "success",
                    "action": action,
                    "sensor_id": sensor_id,
                    "data": reading.get('data', {}),
                    "timestamp": reading.get('timestamp')
                }
            else:
                return {
                    "status": "error",
                    "error": reading.get('error', 'Unknown error'),
                    "action": action
                }
        
        # Process other sensor commands through sensor manager
        return self.sensor_manager.process_command(command)
    
    def _save_sensor_configs(self, configs):
        """Save sensor configurations to persistent storage."""
        try:
            # Load existing config and update sensor section
            cfg = load_config() or {}
            cfg['sensors'] = configs
            save_config(cfg)
        except Exception as e:
            print(f"Failed to save sensor configs: {e}")
    
    def _load_sensor_configs(self):
        """Load sensor configurations from persistent storage."""
        try:
            cfg = load_config()
            if cfg and 'sensors' in cfg:
                loaded_sensors = self.sensor_manager.load_sensor_configs(cfg['sensors'])
                print(f"Loaded {len(loaded_sensors)} sensors from config")
        except Exception as e:
            print(f"Failed to load sensor configs: {e}")
    
    def publish_sensor_reading(self, sensor_id, topic=None):
        """Publish a sensor reading to the platform."""
        reading = self.read_sensor(sensor_id)
        if reading.get('status') == 'success':
            publish_topic = topic or f"{self.topic}/sensors/{sensor_id}"
            self.publish(publish_topic, reading)
            return True
        return False
    
    def publish_all_sensor_readings(self, topic=None):
        """Publish all sensor readings to the platform."""
        readings = self.read_all_sensors()
        if readings:
            publish_topic = topic or f"{self.topic}/sensors/all"
            self.publish(publish_topic, {"sensors": readings, "count": len(readings)})
            return True
        return False
    
    def publish_pin_status(self, pin_sensor_id="pin_status", topic=None):
        """Publish GPIO pin status to the dashboard."""
        if not self.sensor_manager:
            return False
        
        try:
            # Check if pin status sensor exists, create if not
            if pin_sensor_id not in self.sensor_manager.sensors:
                print(f"Pin status sensor '{pin_sensor_id}' not found, creating default...")
                # Create a default pin status sensor for common GPIO pins
                # These are commonly used pins on ESP32/RP2040 platforms
                default_pins = [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23]
                success = self.add_sensor(
                    sensor_id=pin_sensor_id,
                    sensor_type="pin_status", 
                    inputs={"pins": default_pins, "mode": "auto"},
                    alias="GPIO Pin Status Monitor"
                )
                if not success:
                    print("Failed to create default pin status sensor")
                    return False
            
            # Read pin status
            reading = self.read_sensor(pin_sensor_id)
            if reading.get('status') == 'success':
                publish_topic = topic or f"{self.topic}/dashboard/pin_status"
                
                # Format data for dashboard consumption
                dashboard_data = {
                    "device_id": self.device_id,
                    "timestamp": reading['data'].get('timestamp'),
                    "pin_summary": {
                        "total_pins": reading['data'].get('total_pins', 0),
                        "configured_pins": reading['data'].get('configured_pins', 0),
                        "error_pins": reading['data'].get('error_pins', 0)
                    },
                    "pins": reading['data'].get('pins', {}),
                    "status": "success"
                }
                
                self.publish(publish_topic, dashboard_data)
                return True
            else:
                print(f"Failed to read pin status: {reading.get('error', 'unknown error')}")
                return False
                
        except Exception as e:
            print(f"Error publishing pin status: {e}")
            return False
    
    def publish_dashboard_summary(self, topic=None):
        """Publish comprehensive dashboard data including sensors and pin status."""
        try:
            # Get all sensor readings
            sensor_readings = self.read_all_sensors()
            
            # Get pin status
            pin_status = None
            try:
                pin_reading = self.read_sensor("pin_status")
                if pin_reading.get('status') == 'success':
                    pin_status = pin_reading['data']
            except:
                pass  # Pin status sensor may not be configured
            
            # Get system info if available
            system_info = None
            try:
                sys_reading = self.read_sensor("system_info")
                if sys_reading.get('status') == 'success':
                    system_info = sys_reading['data']
            except:
                pass
            
            dashboard_data = {
                "device_id": self.device_id,
                "timestamp": time.time(),
                "sensors": {
                    "count": len(sensor_readings),
                    "readings": sensor_readings
                },
                "pins": pin_status,
                "system": system_info,
                "status": "success"
            }
            
            publish_topic = topic or f"{self.topic}/dashboard/summary"
            self.publish(publish_topic, dashboard_data)
            return True
            
        except Exception as e:
            print(f"Error publishing dashboard summary: {e}")
            return False

    def read_all_modules(self):
        if not self.modules:
            return {}
        out = {}
        for m in self.modules.all():
            out[m.id] = m.read()
        return out

    def set_ntptime(self):
        print("Set NTP time")
        try:
            cntptime.settime()
        except:
            self.set_ntptime()

    def update_data(self, key: str, value):
        self.device_data.update({key: value})

    def on_message(self):
        def decorator(callback_function):
            self.caller = callback_function
        return decorator

    def connect_wifi(self, ssid, password):
        shipper_utils.connect_wifi(ssid, password)

    def connect_mqtt(self):
        try:
            print("trying to connect mqtt server")
            self.mqtt_client.connect()
            self.on_connect()
        except Exception as e:
            print(e)

    def check_msg(self):
        try:
           self.mqtt_client.check_msg()
        except Exception as e:
            self.connect_wifi(self.ssid, self.wifi_password)
            self.mqtt_client.disconnect()
            self.connect_mqtt()

    def process_data(self):
        pass

    def publish(self, topic, msg):
        signed = shipper_utils.make_cmd(msg, self.key_pair)
        shipper_utils.mqtt_publish(self.mqtt_client, topic, signed)

    def update_device(self):
        device = api.get_device(self.device_id, self.network_id)
        self.device_info = device

    def on_connect(self):
        print("Connected")
        self.mqtt_client.subscribe(self.topic)
        api.subscribe(self.topic)
        self.led.value(1)
        print("Subscribed to "+self.topic)


    def on_received(self, topic, msg):
        json_string = msg.decode("utf-8")
        if isinstance(json_string, str):
            json_string = json.loads(json_string)
        try:
            json_data = json.loads(json_string)
            device_exec = json.loads(json_data['device_exec'])
            response_topic = device_exec.get('response_topic')
            if auth.validate_expiry(device_exec) \
                    and auth.check_auth(json_data, self.device_info):
                try:
                    if device_exec.get('update_device'):
                        self.update_device()
                    
                    # Handle sensor commands
                    if device_exec.get('sensor_command') and self.sensor_manager:
                        sensor_result = self.process_sensor_command(device_exec['sensor_command'])
                        if response_topic:
                            signed = shipper_utils.make_cmd(sensor_result, self.key_pair)
                            shipper_utils.mqtt_publish(self.mqtt_client, response_topic, signed)
                        return
                    
                    # dynamic dispatch: read/execute/read_all
                    result = None
                    action = (device_exec.get('action') or '').lower()
                    module_id = device_exec.get('module')
                    if action and self.modules:
                        if action == 'read' and module_id:
                            result = self.modules.read(module_id)
                        elif action == 'execute' and module_id:
                            result = self.modules.execute(module_id, device_exec.get('cmd'), device_exec.get('params'))
                        elif action == 'read_all':
                            result = self.read_all_modules()
                    # Fallback to user callback if no dynamic action handled
                    if result is None:
                        self.caller(device_exec)
                        result = {"handled": "callback"}
                    if response_topic:
                        payload = {"info": "success", "result": result}
                        signed = shipper_utils.make_cmd(payload, self.key_pair)
                        shipper_utils.mqtt_publish(self.mqtt_client, response_topic, signed)
                except Exception as e:
                    signed = shipper_utils.make_cmd({"info": "error"}, self.key_pair)
                    shipper_utils.mqtt_publish(self.mqtt_client, response_topic, signed)
                    print(e)
            else:
                print(self.device_info)
                print("auth failed")
        except Exception as e:
            print(e)


    def default_caller(self, data):
        pass