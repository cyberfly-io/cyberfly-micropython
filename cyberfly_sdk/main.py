from cyberflySdk import CyberflyClient
from config import load_config
import time

cfg = load_config() or {}
key_pair = cfg.get("key_pair") or {"publicKey":"", "secretKey":""}
device_id = cfg.get("device_id", "")
ssid = cfg.get("ssid", "")
password = cfg.get("wifi_password", "")
network_id = cfg.get("network_id", "mainnet01")

client = CyberflyClient(device_id=device_id, key_pair=key_pair,
                        ssid=ssid, wifi_password=password, network_id=network_id)

@client.on_message()
def do_something(data):
    print("Received data:")
    print(data)

while True:
    client.check_msg()
    time.sleep(1)