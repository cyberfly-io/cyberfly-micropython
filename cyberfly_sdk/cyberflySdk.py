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
try:
    from platform_compat import Pin, HAS_MACHINE, PLATFORM
except ImportError:
    # Fallback for direct machine import
    try:
        from machine import Pin
        HAS_MACHINE = True
        PLATFORM = 'unknown'
    except ImportError:
        HAS_MACHINE = False
        PLATFORM = 'unknown'
        class Pin:
            def __init__(self, *args, **kwargs):
                pass
            def value(self, *args):
                return 0

class CyberflyClient:
    def __init__(self, device_id, key_pair, ssid, wifi_password, network_id = "mainnet01", node_url="https://node.cyberfly.io"):
        self.ssid = ssid
        self.wifi_password = wifi_password
        self.key_pair = key_pair
        self.network_id = network_id
        if HAS_MACHINE:
            try:
                self.led = Pin(2, Pin.OUT)
                self.led.off()  # Start with LED off
                print(f"[INFO] Running on platform: {PLATFORM}")
            except Exception as e:
                print(f"[WARN] LED init failed: {e}")
                class _DummyLed:
                    def value(self, *_):
                        return 0
                    def on(self):
                        pass
                    def off(self):
                        pass
                self.led = _DummyLed()
        else:
            class _DummyLed:
                def value(self, *_):
                    return 0
                def on(self):
                    pass
                def off(self):
                    pass
            self.led = _DummyLed()
        self.device_data = {}
        self.device_id = device_id
        self.account = "k:" + self.key_pair.get("publicKey")
        self.caller = self.default_caller
        self.mqtt_server = node_url.split("//")[1]
        self.node_url = node_url
        self.mqtt_client = MQTTClient(device_id, self.mqtt_server, port=31004, keepalive=60)
        self.topic = device_id
        self.mqtt_client.set_callback(self.on_received)
        self.device_info = {}
        self.last_ping = 0
        self.ping_interval = 30000  # Ping every 30 seconds
        self.last_msg_time = 0
        self.connection_timeout = 120000  # 2 minutes timeout
        self.reconnect_count = 0
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
        try:
            from platform_compat import Pin, HAS_MACHINE, reset
        except ImportError:
            try:
                from machine import Pin
                HAS_MACHINE = True
                def reset():
                    import machine
                    machine.reset()
            except ImportError:
                HAS_MACHINE = False
                class Pin:
                    IN = 0
                    PULL_UP = 2
                    def __init__(self, *args, **kwargs):
                        pass
                    def value(self):
                        return 1
                def reset():
                    pass
        
        cfg = load_config()
        
        # Check if config is valid (has required fields)
        config_valid = False
        if cfg:
            required_fields = ['device_id', 'ssid', 'key_pair']
            config_valid = all(cfg.get(field) for field in required_fields)
            if config_valid:
                # Also check key_pair has publicKey
                kp = cfg.get('key_pair', {})
                if not kp.get('publicKey'):
                    config_valid = False
        
        if config_valid:
            print("[BOOT] Found valid config")
        else:
            print("[BOOT] No valid config found")
        
        trigger = False
        # Always check button if button_pin is provided (allows reconfiguration)
        if HAS_MACHINE and button_pin is not None:
            try:
                btn = Pin(button_pin, Pin.IN, Pin.PULL_UP)
                time.sleep_ms(100)  # Let pull-up stabilize
                
                # Take multiple readings to verify pin state
                readings = []
                for _ in range(3):
                    readings.append(btn.value())
                    time.sleep_ms(20)
                
                # Check if readings are consistent
                initial_state = readings[-1]
                all_same = all(r == initial_state for r in readings)
                
                print(f"[BOOT] Button pin {button_pin} readings: {readings} -> initial_state: {initial_state}")
                
                # If pin is stuck LOW (all readings are 0), it's likely a hardware issue
                # In this case, skip button check to avoid false trigger
                if not all_same:
                    print("[BOOT] Button pin unstable, skipping button check")
                elif all(r == 0 for r in readings):
                    print("[BOOT] WARNING: Button pin stuck LOW - possible hardware issue or wrong pin")
                    print("[BOOT] Skipping button check to avoid false trigger")
                    print("[BOOT] If you need to reconfigure, use a different GPIO pin")
                # Only check for button hold if initial state is LOW AND readings are stable
                elif initial_state == 0:
                    print(f"[BOOT] Button detected pressed, checking for {long_ms}ms hold...")
                    t0 = time.ticks_ms()
                    
                    while time.ticks_diff(time.ticks_ms(), t0) < long_ms:
                        if btn.value() == 0:
                            # Button still held
                            if time.ticks_diff(time.ticks_ms(), t0) >= long_ms:
                                trigger = True
                                print("[BOOT] Button held - entering BLE provisioning mode")
                                break
                        else:
                            # Button released
                            print(f"[BOOT] Button released after {time.ticks_diff(time.ticks_ms(), t0)}ms")
                            break
                        time.sleep_ms(50)
                else:
                    print("[BOOT] Button not pressed, continuing normal boot")
            except Exception as e:
                print(f"[WARN] Button check failed: {e}")
                pass
        
        if not config_valid or trigger:
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
                        reset()
                    except Exception as e:
                        print(f"[WARN] Reset failed: {e}")
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
        
        action = command.get('action')
        
        # Handle read_pin_status command with auto-creation
        if action == 'read_pin_status':
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
        
        # Handle read_system_info command with auto-creation
        elif action == 'read_system_info':
            sensor_id = command.get('sensor_id', 'system_info')
            if sensor_id not in self.sensor_manager.sensors:
                print(f"Auto-creating system info sensor '{sensor_id}'...")
                success = self.add_sensor(
                    sensor_id=sensor_id,
                    sensor_type="system_info",
                    inputs={},
                    alias="System Information Monitor"
                )
                if not success:
                    return {
                        "status": "error",
                        "error": "Failed to create system info sensor",
                        "action": action
                    }
            
            # Read and return system info
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
        
        # Handle read_all_sensors command
        elif action == 'read_all_sensors':
            readings = self.read_all_sensors()
            try:
                import cntptime
                timestamp = cntptime.get_rtc_time()
            except:
                timestamp = time.time()
            return {
                "status": "success",
                "action": action,
                "count": len(readings),
                "sensors": readings,
                "timestamp": timestamp
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
                sensor_cfgs = cfg['sensors']
                if isinstance(sensor_cfgs, list):
                    sensor_cfgs = {
                        item['sensor_id']: item
                        for item in sensor_cfgs
                        if isinstance(item, dict) and item.get('sensor_id')
                    }
                loaded_sensors = self.sensor_manager.load_sensor_configs(sensor_cfgs)
                print(f"Loaded {len(loaded_sensors)} sensors from config")
        except Exception as e:
            print(f"Failed to load sensor configs: {e}")
    
    def read_all_modules(self):
        if not self.modules:
            return {}
        out = {}
        for m in self.modules.all():
            out[m.id] = m.read()
        return out

    def set_ntptime(self, max_retries=3):
        print("Set NTP time")
        for attempt in range(max_retries):
            try:
                print(f"[NTP] Attempt {attempt + 1}/{max_retries}")
                cntptime.settime()
                print("NTP time set successfully")
                return True
            except Exception as e:
                import sys
                print(f"NTP attempt {attempt + 1}/{max_retries} failed: {e}")
                sys.print_exception(e)
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
        print("[WARN] Failed to set NTP time after all retries")
        return False
    
    def health_check(self):
        """Perform a health check and return system status."""
        import gc
        import network
        
        status = {
            "wifi_connected": False,
            "mqtt_connected": False,
            "free_memory": 0,
            "reconnect_count": self.reconnect_count,
            "last_msg_age_ms": 0
        }
        
        try:
            # Check WiFi
            wlan = network.WLAN(network.STA_IF)
            status["wifi_connected"] = wlan.isconnected()
            
            # Check MQTT (indirect check via last message time)
            now = time.ticks_ms()
            status["last_msg_age_ms"] = time.ticks_diff(now, self.last_msg_time)
            status["mqtt_connected"] = status["last_msg_age_ms"] < self.connection_timeout
            
            # Memory status
            gc.collect()
            status["free_memory"] = gc.mem_free()
            
            # Check for potential issues
            if status["free_memory"] < 10000:
                print("[WARN] Low memory: {status['free_memory']} bytes")
            
            if not status["wifi_connected"]:
                print("[WARN] WiFi disconnected")
            
            if not status["mqtt_connected"]:
                print("[WARN] MQTT appears disconnected")
                
        except Exception as e:
            print(f"[ERROR] Health check failed: {e}")
        
        return status

    def maintain_connection(self):
        """
        Main loop helper for maintaining connections.
        Call this in your main loop along with check_msg().
        
        Example:
            while True:
                client.check_msg()
                client.maintain_connection()
                time.sleep_ms(100)
        """
        # Perform periodic health checks
        if hasattr(self, '_last_health_check'):
            if time.ticks_diff(time.ticks_ms(), self._last_health_check) > 60000:  # Every minute
                status = self.health_check()
                self._last_health_check = time.ticks_ms()
        else:
            self._last_health_check = time.ticks_ms()

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
            self.last_ping = time.ticks_ms()
            self.last_msg_time = time.ticks_ms()
            self.reconnect_count = 0
            print("[MQTT] Connected successfully")
        except Exception as e:
            print(f"[MQTT] Connection failed: {e}")
            self.reconnect_count += 1

    def check_msg(self):
        """Check for messages and maintain connection health."""
        try:
            # Check for incoming messages
            self.mqtt_client.check_msg()
            
            # Send keepalive ping if needed
            now = time.ticks_ms()
            if time.ticks_diff(now, self.last_ping) > self.ping_interval:
                try:
                    self.mqtt_client.ping()
                    self.last_ping = now
                    print("[MQTT] Keepalive ping sent")
                except Exception as ping_error:
                    print(f"[MQTT] Ping failed: {ping_error}")
                    raise  # Trigger reconnection
            
            # Check for connection timeout (no messages received)
            if time.ticks_diff(now, self.last_msg_time) > self.connection_timeout:
                print(f"[MQTT] No messages for {self.connection_timeout/1000}s - reconnecting")
                raise Exception("Connection timeout")
                
        except Exception as e:
            print(f"[MQTT] Error in check_msg: {e}")
            self._reconnect()
    
    def _reconnect(self):
        """Handle reconnection with exponential backoff."""
        try:
            print(f"[MQTT] Reconnection attempt {self.reconnect_count + 1}")
            
            # Disconnect cleanly
            try:
                self.mqtt_client.disconnect()
            except:
                pass
            
            # Check WiFi connection
            import network
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                print("[WiFi] Connection lost, reconnecting...")
                self.connect_wifi(self.ssid, self.wifi_password)
            
            # Exponential backoff (max 30 seconds)
            delay = min(2 ** self.reconnect_count, 30)
            print(f"[MQTT] Waiting {delay}s before reconnect...")
            time.sleep(delay)
            
            # Try to reconnect MQTT
            self.connect_mqtt()
            
            # Garbage collect to free memory
            import gc
            gc.collect()
            print(f"[Memory] Free: {gc.mem_free()} bytes")
            
        except Exception as e:
            print(f"[MQTT] Reconnection failed: {e}")
            self.reconnect_count += 1

    def process_data(self):
        pass

    def publish(self, topic, msg):
        signed = shipper_utils.make_cmd(msg, self.key_pair)
        shipper_utils.mqtt_publish(self.mqtt_client, topic, signed)

    def update_device(self, retry_delay=2000):
        """
        Update device info with infinite retry logic until success.
        
        Args:
            retry_delay: Delay between retries in milliseconds (default: 2000ms)
        
        Returns:
            bool: Always returns True (loops until success)
        """
        import time
        
        attempt = 0
        while True:
            attempt += 1
            try:
                print(f"[update_device] Attempt {attempt}")
                device = api.get_device(self.device_id, self.network_id)
                
                # Check if we got valid device info
                if device and isinstance(device, dict) and device:
                    self.device_info = device
                    print(f"[update_device] Success! Device info retrieved: {list(device.keys())}")
                    return True
                else:
                    print(f"[update_device] Attempt {attempt} returned empty or invalid data")
                    
            except Exception as e:
                print(f"[update_device] Attempt {attempt} failed: {e}")
            
            print(f"[update_device] Retrying in {retry_delay}ms...")
            time.sleep_ms(retry_delay)

    def on_connect(self):
        print("Connected")
        self.mqtt_client.subscribe(self.topic)
        api.subscribe(self.topic)
        try:
            self.led.on()  # Turn LED on to indicate MQTT connected
            print("LED turned ON (MQTT connected)")
        except Exception as e:
            print(f"[WARN] Failed to turn LED on: {e}")
        print("Subscribed to "+self.topic)


    def on_received(self, topic, msg):
        # Update last message time
        self.last_msg_time = time.ticks_ms()
        
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
                    import sys
                    print(f"[ERROR] Command execution failed: {e}")
                    sys.print_exception(e)
                    if response_topic:
                        try:
                            signed = shipper_utils.make_cmd({"info": "error", "error": str(e)}, self.key_pair)
                            shipper_utils.mqtt_publish(self.mqtt_client, response_topic, signed)
                        except:
                            pass
            else:
                print(self.device_info)
                print("auth failed")
        except Exception as e:
            print(e)


    def default_caller(self, data):
        pass