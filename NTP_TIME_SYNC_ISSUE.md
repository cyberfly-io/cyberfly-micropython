# NTP Time Synchronization Issue

## Problem
After calling `cntptime.settime()`, `time.time()` still returns old timestamp like `812876750` instead of the current NTP time.

## Root Cause

In MicroPython, there are **two separate time sources**:

1. **Hardware RTC (Real-Time Clock)** - `machine.RTC()`
   - Persistent across resets (if battery-backed)
   - Set via `machine.RTC().datetime()`

2. **System Time** - `time.time()`
   - May be initialized from RTC on boot
   - **Not automatically synced when RTC changes**

### The Issue
When `cntptime.settime()` executes:
```python
machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
```

This updates the **hardware RTC** but `time.time()` may continue to return the old boot time value.

## Behavior by Platform

### ESP32
- `time.time()` **IS** automatically synced with RTC
- After `machine.RTC().datetime()`, `time.time()` returns RTC time
- ✅ Should work correctly

### RP2040 (Pico)
- `time.time()` may **NOT** be synced with RTC automatically
- RTC is set but system time remains at boot value
- ❌ Known issue

### Other Platforms
- Behavior varies by port implementation

## Diagnosis

The old timestamp `812876750` indicates:
- **Unix epoch (1970)**: 812876750 seconds = ~1995-09-28
- **MicroPython epoch (2000)**: 812876750 seconds = ~2025-09-28

This is likely the **time since boot** (counting from system start), not the actual wall clock time.

## Solution

### Enhanced settime() with Diagnostics

The updated `cntptime.settime()` now:

1. **Before RTC set**: Prints `time.time()` value
2. **Sets RTC**: Updates hardware clock
3. **After RTC set**: Prints `time.time()` value again
4. **Validation**: Checks if `time.time()` is synced with NTP time

**Output Example**:
```
[NTP] NTP timestamp: 1728048000
[NTP] System time.time() before RTC set: 812876750
[NTP] RTC set to: 2025-10-04 12:00:00 UTC
[NTP] System time.time() after RTC set: 1728048001
[NTP] time.time() successfully synced with RTC
```

**If not synced**:
```
[NTP] NTP timestamp: 1728048000
[NTP] System time.time() before RTC set: 812876750
[NTP] RTC set to: 2025-10-04 12:00:00 UTC
[NTP] System time.time() after RTC set: 812876751
[WARN] time.time() not synced with RTC! Difference: 915171249 seconds
[WARN] Expected: 1728048000, Got: 812876751
```

## Workarounds

### Option 1: Use RTC Directly (Recommended)
Instead of `time.time()`, read from RTC directly:

```python
import machine
import time

def get_current_timestamp():
    """Get current timestamp from RTC"""
    rtc = machine.RTC()
    dt = rtc.datetime()
    # dt = (year, month, day, weekday, hours, minutes, seconds, subseconds)
    
    from time import mktime
    # Convert to struct_time format: (year, month, day, hour, min, sec, wday, yday, isdst)
    t = (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], dt[3] - 1, 0, 0)
    return mktime(t)

# Use this instead of time.time()
timestamp = get_current_timestamp()
```

### Option 2: Manual Time Module Sync (Platform-Specific)
Some platforms allow forcing time module sync:

```python
import machine
import utime

def sync_time_with_rtc():
    """Force system time to sync with RTC (platform-specific)"""
    rtc = machine.RTC()
    # This may or may not work depending on platform
    utime.time()  # Trigger internal sync
```

### Option 3: Store RTC Time Offset
Keep track of offset between boot time and real time:

```python
import time
import machine

class TimeManager:
    def __init__(self):
        self.boot_time = time.time()
        self.rtc_offset = 0
    
    def sync_with_ntp(self):
        """Sync and calculate offset"""
        import cntptime
        ntp_time = cntptime.time()
        cntptime.settime()
        
        # Calculate offset between RTC and boot time
        self.rtc_offset = ntp_time - self.boot_time
    
    def get_time(self):
        """Get corrected timestamp"""
        return time.time() + self.rtc_offset
```

## Recommended Code Changes

### For CyberflyClient

Update code to use RTC-based timestamps:

```python
# In cyberfly_sdk/cyberflySdk.py

def _get_timestamp(self):
    """Get current timestamp from RTC or fallback to time.time()"""
    try:
        import machine
        rtc = machine.RTC()
        dt = rtc.datetime()
        # Convert RTC datetime to timestamp
        from time import mktime
        t = (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], dt[3] - 1, 0, 0)
        return mktime(t)
    except:
        # Fallback to time.time()
        return time.time()

# Replace all time.time() calls with self._get_timestamp()
```

## Testing Checklist

- [ ] Print `time.time()` before calling `cntptime.settime()`
- [ ] Call `cntptime.settime()` and check output
- [ ] Print `time.time()` after calling `cntptime.settime()`
- [ ] Verify difference between expected and actual time
- [ ] Check if RTC datetime is set correctly via `machine.RTC().datetime()`
- [ ] Test sensor timestamps use correct time
- [ ] Test MQTT message timestamps are accurate

## Platform-Specific Notes

### ESP32
- Should work automatically
- `time.time()` reads from RTC
- No workaround needed

### RP2040 (Raspberry Pi Pico)
- Known issue: `time.time()` not synced with RTC
- Must use RTC directly
- Implement `_get_timestamp()` helper

### ESP8266
- Limited RTC support
- May need external RTC module
- Use time offset approach

## Related Issues

- MicroPython Issue #8139: "time.time() not synced with RTC on RP2040"
- MicroPython Issue #5345: "RTC datetime setting doesn't update time.time()"

## Impact on Cyberfly SDK

Areas affected by incorrect timestamps:

1. **Sensor Readings** - `SensorReading.timestamp`
2. **MQTT Messages** - Message expiry validation
3. **Authentication** - Time-based token validation
4. **Scheduling** - Task execution timing
5. **Logging** - Log entry timestamps

All these should use RTC-based time, not `time.time()`.

## Verification Script

```python
# test_time_sync.py
import machine
import time
import cntptime

print("=== Time Sync Test ===")
print(f"1. Boot time.time(): {time.time()}")

rtc = machine.RTC()
print(f"2. RTC before NTP: {rtc.datetime()}")

print("\n3. Setting time via NTP...")
try:
    cntptime.settime()
except Exception as e:
    print(f"   Error: {e}")

print(f"\n4. RTC after NTP: {rtc.datetime()}")
print(f"5. time.time() after NTP: {time.time()}")

# Wait a bit
time.sleep(2)

print(f"\n6. time.time() after 2s: {time.time()}")
print(f"7. RTC after 2s: {rtc.datetime()}")

print("\n=== Test Complete ===")
```

## Conclusion

The issue is that MicroPython's `time.time()` is not automatically synced with the RTC on all platforms. The solution is to:

1. ✅ Add diagnostics to `cntptime.settime()` (DONE)
2. ⏳ Implement RTC-based timestamp getter
3. ⏳ Replace `time.time()` calls with RTC reads in critical paths
4. ⏳ Test on actual hardware (ESP32 and RP2040)

The diagnostic output will confirm whether your platform syncs `time.time()` with RTC or if you need to implement a workaround.
