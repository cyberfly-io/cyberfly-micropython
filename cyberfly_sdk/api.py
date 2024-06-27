import shipper_utils
import urequests as rt
def get_device(device_id, network_id):
    conn = False
    while not conn:
        if shipper_utils.is_cnx_active():
            conn = True         
            try:
                device = rt.get("https://node.cyberfly.io/api/device/"+device_id+"?network_id="+network_id).json()
                if isinstance(device, dict):
                    print(device)
                    return device
                else:
                    return {}
            except Exception as e:
                print(e)
                return {}
        else:
            print("no internet")



def subscribe(topic):
    rt.get('https://node.cyberfly.io/api/subscribe/'+topic)