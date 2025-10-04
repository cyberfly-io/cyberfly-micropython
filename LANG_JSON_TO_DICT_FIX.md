# Fix: 'Lang' object has no attribute 'json_to_dict'

## Issue

Error when creating MQTT commands:
```
'Lang' object has no attribute 'json_to_dict'
```

## Root Cause

The `make_cmd()` function in `shipper_utils.py` was incomplete and calling a non-existent method:

```python
def make_cmd(data, key_pair, ttl=10):
    data = Lang().json_to_dict(data)  # ❌ This method doesn't exist!
    try:
        import cntptime
        current_time = cntptime.get_rtc_time()
    except:
        current_time = time.time()
    data.update({"expiry_time": current_time + 10})
    # ❌ Function incomplete - doesn't sign or return anything!
```

**Problems**:
1. `Lang` class only has `mk_meta()` method, not `json_to_dict()`
2. Function doesn't sign the data
3. Function doesn't return anything
4. Hardcoded ttl to 10 seconds (ignoring parameter)

## Solution

Rewrote `make_cmd()` to properly create signed MQTT commands:

```python
def make_cmd(data, key_pair, ttl=10):
    # Convert data to dict if it's a string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            data = {"data": data}
    elif not isinstance(data, dict):
        data = {"data": data}
    
    # Add expiry time using RTC
    try:
        import cntptime
        current_time = cntptime.get_rtc_time()
    except:
        current_time = time.time()
    data.update({"expiry_time": current_time + ttl})
    
    # Sign the command
    device_exec = json.dumps(data)
    signed = Crypto().sign(device_exec.encode(), key_pair)
    signed['device_exec'] = device_exec
    
    return signed
```

## What This Does

### 1. Data Normalization
Converts input data to dictionary format:
- **String JSON**: Parses `'{"key": "value"}'` → `{"key": "value"}`
- **String**: Wraps `"hello"` → `{"data": "hello"}`
- **Dict**: Keeps as-is `{"key": "value"}` → `{"key": "value"}`
- **Other types**: Wraps in dict `123` → `{"data": 123}`

### 2. Expiry Time
Adds expiry timestamp using RTC:
```python
data.update({"expiry_time": current_time + ttl})
```

**Result**:
```python
{
    "sensor_id": "temp1",
    "data": {"temperature": 25.5},
    "expiry_time": 1728048760  # Current time + ttl
}
```

### 3. Signing
Creates cryptographic signature:
```python
signed = Crypto().sign(device_exec.encode(), key_pair)
# Returns: {"hash": "...", "sig": "...", "pubKey": "..."}

signed['device_exec'] = device_exec
# Adds: {"device_exec": "{\"sensor_id\":...}"}
```

**Final Result**:
```python
{
    "hash": "abc123...",
    "sig": "def456...",
    "pubKey": "k:abc123...",
    "device_exec": '{"sensor_id":"temp1","data":{"temperature":25.5},"expiry_time":1728048760}'
}
```

## Message Flow

### Before Fix (Broken):

```python
# 1. Call make_cmd
signed = shipper_utils.make_cmd(sensor_result, key_pair)

# 2. Error!
# 'Lang' object has no attribute 'json_to_dict'

# 3. No message sent ❌
```

### After Fix (Working):

```python
# 1. Call make_cmd
sensor_result = {
    "status": "success",
    "action": "read_system_info",
    "data": {...}
}
signed = shipper_utils.make_cmd(sensor_result, key_pair)

# 2. Returns properly signed command
# {
#   "hash": "abc123",
#   "sig": "def456",
#   "pubKey": "k:abc123",
#   "device_exec": "{...}"
# }

# 3. Publish to MQTT ✅
mqtt_publish(client, response_topic, signed)
```

## Impact on System

### Authentication Flow

**On Device (Sender)**:
```python
# 1. Create data
data = {"action": "read_sensor", "sensor_id": "temp1"}

# 2. Sign with make_cmd()
signed = make_cmd(data, device_key_pair)

# 3. Send via MQTT
mqtt_publish(client, topic, signed)
```

**On Platform (Receiver)**:
```python
# 1. Receive MQTT message
msg = json.loads(mqtt_payload)

# 2. Extract device_exec
device_exec = json.loads(msg['device_exec'])

# 3. Validate expiry
if validate_expiry(device_exec):  # Checks expiry_time
    
    # 4. Verify signature
    if check_auth(msg, device_info):  # Verifies hash, sig, pubKey
        # Process command ✅
```

### Where This Is Used

1. **Sensor Command Responses** (`cyberflySdk.py:531`)
   ```python
   sensor_result = self.process_sensor_command(device_exec['sensor_command'])
   signed = shipper_utils.make_cmd(sensor_result, self.key_pair)
   ```

2. **Action Results** (`cyberflySdk.py:552`)
   ```python
   payload = {"info": "success", "result": result}
   signed = shipper_utils.make_cmd(payload, self.key_pair)
   ```

3. **Error Responses** (`cyberflySdk.py:555`)
   ```python
   signed = shipper_utils.make_cmd({"info": "error"}, self.key_pair)
   ```

4. **Device Publishing** (`cyberflySdk.py:465`)
   ```python
   signed = shipper_utils.make_cmd(msg, self.key_pair)
   ```

## Testing

### Test 1: Basic Command Creation

```python
from shipper_utils import make_cmd

key_pair = {
    "publicKey": "abc123...",
    "secretKey": "def456..."
}

# Test dict data
result1 = make_cmd({"test": "data"}, key_pair)
print(result1.keys())  # Should have: hash, sig, pubKey, device_exec

# Test string data
result2 = make_cmd("hello", key_pair)
print(result2)  # device_exec should contain {"data": "hello"}

# Test with custom ttl
result3 = make_cmd({"test": "data"}, key_pair, ttl=60)
exec_data = json.loads(result3['device_exec'])
print(exec_data['expiry_time'])  # Should be ~60 seconds from now
```

### Test 2: Signature Verification

```python
from pact import Crypto

# Create signed command
signed = make_cmd({"test": "data"}, key_pair)

# Verify signature
device_exec = signed['device_exec']
is_valid = Crypto().verify(
    device_exec,
    signed['pubKey'],
    signed['sig']
)

print(f"Signature valid: {is_valid}")  # Should be True
```

### Test 3: Full MQTT Flow

```python
# On device
from cyberflySdk import CyberflyClient

client = CyberflyClient(...)

# Send sensor data
sensor_data = {"temperature": 25.5, "humidity": 60}
client.publish("sensor/data", sensor_data)

# Should NOT see 'Lang' error anymore ✅
```

## Related Timestamp Issue

Also noticed in the logs:
```
1759580220 812895411
```

This shows:
- **First number** (1759580220): Expiry time from RTC ✅ Correct!
- **Second number** (812895411): Current time from `time.time()` ❌ Boot time!

This confirms that:
1. ✅ `make_cmd()` is correctly using RTC time for expiry
2. ❌ `validate_expiry()` in `auth.py` was using boot time

**Already fixed** in `auth.py` to use RTC time for validation.

## Verification Checklist

- [x] Fix `make_cmd()` to properly sign commands
- [x] Remove non-existent `json_to_dict()` call
- [x] Add proper return statement
- [x] Use RTC time for expiry
- [x] Honor ttl parameter
- [ ] Test MQTT command publishing
- [ ] Verify authentication works end-to-end
- [ ] Check no more 'Lang' errors in logs

## Files Modified

- `cyberfly_sdk/shipper_utils.py` - Fixed `make_cmd()` function

## Related Fixes

- `auth.py` - Fixed `validate_expiry()` to use RTC
- `pact.py` - Fixed `prepare_exec_cmd()` to use RTC
- `schedule.py` - Fixed `now()` to use RTC
- `logging.py` - Fixed `LogRecord` to use RTC

## Summary

The `make_cmd()` function was incomplete and broken. It's now properly:
1. ✅ Normalizes input data to dict format
2. ✅ Adds accurate RTC-based expiry time
3. ✅ Signs the command with Ed25519 signature
4. ✅ Returns complete signed MQTT message
5. ✅ Respects ttl parameter

This fixes the `'Lang' object has no attribute 'json_to_dict'` error and enables proper authenticated MQTT communication! 🔐✨
