# MQTT LED Indicator Fix

## Issue
LED not turning on when MQTT connection succeeds and subscription is established.

## Root Cause
1. **Pin Conflict**: Both `BLEProvisioner` and `CyberflySdk` use GPIO Pin 2 for LED
2. **Method Mismatch**: Used `.value(1)` instead of `.on()` method
3. **Missing Initialization**: LED not explicitly turned off during initialization
4. **Incomplete _DummyLed**: Fallback class missing `.on()` and `.off()` methods

## Analysis
- **BLE Provisioning**: Uses Pin 2 with `.on()/.off()` for blinking during provisioning
- **BLE Cleanup**: Turns LED off with `self._led_pin.off()` when provisioning completes
- **MQTT Connection**: Tried to use `self.led.value(1)` to turn LED on
- **Problem**: After BLE cleanup turns LED off, MQTT connection couldn't turn it back on properly

## Solution

### 1. Fixed LED Initialization (cyberflySdk.py:35-58)
```python
if HAS_MACHINE:
    try:
        self.led = Pin(2, Pin.OUT)
        self.led.off()  # Start with LED off ← ADDED
        print(f"[INFO] Running on platform: {PLATFORM}")
    except Exception as e:
        print(f"[WARN] LED init failed: {e}")
        class _DummyLed:
            def value(self, *_):
                return 0
            def on(self):      # ← ADDED
                pass
            def off(self):     # ← ADDED
                pass
        self.led = _DummyLed()
else:
    class _DummyLed:
        def value(self, *_):
            return 0
        def on(self):          # ← ADDED
            pass
        def off(self):         # ← ADDED
            pass
    self.led = _DummyLed()
```

**Changes**:
- Added `self.led.off()` after Pin initialization to ensure clean start state
- Added `.on()` and `.off()` methods to `_DummyLed` fallback class
- Ensures consistent LED API whether hardware Pin or dummy

### 2. Fixed on_connect() Method (cyberflySdk.py:563-571)
**Before**:
```python
def on_connect(self):
    print("Connected")
    self.mqtt_client.subscribe(self.topic)
    api.subscribe(self.topic)
    self.led.value(1)  # Wrong method
    print("Subscribed to "+self.topic)
```

**After**:
```python
def on_connect(self):
    print("Connected")
    self.mqtt_client.subscribe(self.topic)
    api.subscribe(self.topic)
    try:
        self.led.on()  # ← Use .on() method
        print("LED turned ON (MQTT connected)")  # ← Status feedback
    except Exception as e:
        print(f"[WARN] Failed to turn LED on: {e}")  # ← Error handling
    print("Subscribed to "+self.topic)
```

**Changes**:
- Changed from `self.led.value(1)` to `self.led.on()`
- Added try-except for error handling
- Added status print for debugging
- Consistent with BLE provisioning LED API

## LED Usage Pattern

### During Boot:
1. **Initialization**: LED turned OFF (`self.led.off()`)
2. **Config Check**: No LED activity
3. **BLE Provision** (if needed):
   - LED blinks at 2Hz (500ms on/off)
   - Indicates device in provisioning mode
4. **BLE Cleanup**: LED turned OFF

### After Provisioning:
5. **MQTT Connect**: LED remains OFF until connected
6. **MQTT Connected**: LED turned ON (`self.led.on()`)
7. **Status Indicator**: LED stays ON while MQTT connected

## Pin Sharing Strategy
- **Single Pin**: Both BLE and MQTT use GPIO Pin 2
- **Sequential Usage**: BLE uses during provisioning, then MQTT uses after
- **Clean Handoff**: BLE turns LED off during cleanup, MQTT turns on when connected
- **No Conflict**: Usage is mutually exclusive (never overlap)

## Testing Checklist
- [ ] LED off during boot
- [ ] LED blinks during BLE provisioning mode
- [ ] LED off after provisioning completes
- [ ] LED off while connecting to MQTT
- [ ] LED turns ON when MQTT connection succeeds
- [ ] LED stays ON while MQTT connected
- [ ] No errors in log about LED control
- [ ] _DummyLed fallback works if Pin init fails

## Related Files
- `cyberfly_sdk/cyberflySdk.py`: MQTT LED control (lines 35-58, 563-571)
- `cyberfly_sdk/ble_provision.py`: BLE LED blinking (lines 94-125, 147-160)

## Expected Behavior
1. **Boot**: LED off
2. **BLE Mode**: LED blinks (if provisioning needed)
3. **MQTT Connecting**: LED off
4. **MQTT Connected**: LED on (solid)
5. **Normal Operation**: LED on (indicates cloud connection)

## Benefits
- ✅ Consistent LED API (`.on()/.off()` everywhere)
- ✅ Clear status indication (blinking = provisioning, solid = connected)
- ✅ Proper error handling with try-except
- ✅ Debug logging for troubleshooting
- ✅ Clean pin sharing between BLE and MQTT
- ✅ Fallback support with _DummyLed

## Implementation Notes
- LED Pin 2 is shared but usage is sequential (BLE → MQTT)
- Both systems use `.on()/.off()` methods consistently
- Initialization ensures clean starting state
- Error handling prevents LED failures from crashing system
- Debug prints help verify LED state changes
