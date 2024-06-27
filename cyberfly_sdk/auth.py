from pact import Crypto
import time

def check_auth(cmd, device_info):
    pub_key = cmd.get('pubKey')
    sig = cmd.get('sig')
    device_exec = cmd.get('device_exec')

    if pub_key and sig and device_exec:
        verify = Crypto().verify(device_exec, pub_key, sig)
        if verify:
            device = device_info
            if device.keys() and pub_key in device['guard']['keys']:
                return True
            else:
                return False
        else:
            return False
    else:
        print("Mission anyone of these variable pubKey, sig, device_exec")
        return False


def validate_expiry(msg):
    expiry_time = msg.get('expiry_time')
    if expiry_time:
        now = time.time()
        print(expiry_time, now)
        if now < expiry_time:
            return True
        else:
            print("Time expired")
            print(expiry_time, now)
            return False
    else:
        print("expiry_time required")
        return False