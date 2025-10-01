# cyberfly-micropython

### Download firmware here - https://github.com/cyberfly-io/cyberfly-micropython/releases/tag/esp32-0.2.2

## example usage

```python
from cyberflySdk import CyberflyClient
import machine
import time

key_pair={"publicKey":"be649fdc3e28848e83fc528729cfb0aa605ee0b50233906cb73d0121c5cdbc42",
         "secretKey":"865d0d6cbaec24121c99d0f7a7ff8e120131682e15b4ed3f579cbac27de78483"}
device_id="00716095-ac1e-4fe9-914e-c25cb32979fd"
client = CyberflyClient(device_id=device_id, key_pair=key_pair, ssid="your_wifi_name",
                             wifi_password="wifipassword", network_id="testnet04")


@client.on_message()
def do_something(data):
    print(data)
    led = machine.Pin(int(data['pin_no']), machine.Pin.OUT)
    led.value(data['state'])

    
while 1:
    client.check_msg()
    time.sleep(1)
```


### Build from source

git clone -b v5.4.2 --recursive https://github.com/espressif/esp-idf.git

cd esp-idf

git checkout v5.4.2

git submodule update --init --recursive

cd esp-idf

./install.sh esp32 

. ./export.sh

