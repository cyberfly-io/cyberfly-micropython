# cyberfly-micropython



## example usage

```python
from data_shipper import CyberflyDataShipper
import machine
import time

key_pair = {"publicKey":"37a720dcf056387df1d9c85cda3cbff55aa9084b6eaee8bb9fde20c684fd9418","secretKey":"f18adeab3f38b5531f6fcd9ae05d3fb0ea42f0314ea5b93f0d7114d14ff3daac"}
device_id="0afcff85-5b57-4136-aa6c-2897cc5b6b88"
client = CyberflyDataShipper(device_id=device_id, key_pair=key_pair, ssid="Abu",wifi_password="abu12345678", network_id="testnet04")
led = machine.Pin(2, machine.Pin.OUT)

@client.on_message()
def do_something(data):
    print(data)
    if data['state']:
        led.value(1)
    else:
        led.value(0)

    
while 1:
    client.check_msg()
    time.sleep(1)
```
