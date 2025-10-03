import network
import time
import json
import urequests as rt
from pact import Lang, Crypto
try:
    from platform_compat import reset
except ImportError:
    try:
        import machine
        def reset():
            machine.reset()
    except ImportError:
        def reset():
            print("[WARN] Reset not available")

def connect_wifi(ssid, password):
    count = 1
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        if not wlan.isconnected():
           wlan.connect(ssid, password)
    except Exception as e:
        print(e)
    while not wlan.isconnected():
        count = count +1
        print('Waiting for wifi connection...')
        if count>10:
            print("Restarting device...")
            reset()
        time.sleep(1)

def is_cnx_active():
    try:
        rt.head("https://api.cyberfly.io")
        return True
    except:
        print("No internet")
        return False

def default_meta(sender="not real"):
    return Lang().mk_meta(sender, "1", 0.000001, 80000, time.time()-15, 28800)

def get_api_host(network_id):
    if network_id == "testnet04":
        return "https://api.testnet.chainweb.com/chainweb/0.0/testnet04/chain/{}/pact".format(1)
    else:
        return "https://api.chainweb.com/chainweb/0.0/mainnet01/chain/{}/pact".format(1)

def publish(client, data, key_pair):
    data = json.loads(data)
    device_list = make_list(data['to_devices'])
    for device_id in device_list:
        cmd = make_cmd(data['data'], key_pair)
        try:
            mqtt_publish(client, device_id, cmd)
            print("published to device {}".format(device_id))
        except Exception as e:
            print(e)


def mqtt_publish(client, topic, cmd):
    payload = json.dumps(cmd)
    client.publish(topic, payload)


def make_cmd(data, key_pair):
    data.update({"expiry_time": time.time() + 10})
    signed = Crypto().sign(json.dumps(data), key_pair)
    signed.update({"device_exec": json.dumps(data)})
    return signed


def is_number(s):
    try:
        complex(s)
    except ValueError:
        return False
    return True


def make_list(s):
    if isinstance(s, list):
        return s
    return [s]

