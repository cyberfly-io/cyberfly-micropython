from cmqtt import MQTTClient
import shipper_utils
import api
import auth
import json
import cntptime
import machine
from module_registry import ModuleRegistry
from actuators.led import LedModule

class CyberflyClient:
    def __init__(self, device_id, key_pair, ssid, wifi_password, network_id = "mainnet01", node_url="https://node.cyberfly.io"):
        self.ssid = ssid
        self.wifi_password = wifi_password
        self.key_pair = key_pair
        self.network_id = network_id
        self.led = machine.Pin(2, machine.Pin.OUT)
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
        self.connect_wifi(ssid, wifi_password)
        self.set_ntptime()
        self.update_device()
        self.connect_mqtt()

    def register_modules(self, *mods):
        if self.modules is None:
            self.modules = ModuleRegistry()
        self.modules.add(*mods)

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