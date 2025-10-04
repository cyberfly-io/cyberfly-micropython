# Reading Time from RTC in MicroPython

## Overview

This guide explains how to read time from the Real-Time Clock (RTC) in MicroPython, especially when `time.time()` is not synced with the RTC.

## Quick Reference

### Method 1: Use Helper Functions (Recommended)

```python
import cntptime

# Get Unix timestamp from RTC
timestamp = cntptime.get_rtc_time()
print(f"Current timestamp: {timestamp}")

# Get readable datetime from RTC
dt = cntptime.get_rtc_datetime()
if dt:
    year, month, day, hour, minute, second = dt
    print(f"Current time: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
```

### Method 2: Direct RTC Access

```python
import machine

# Read RTC
rtc = machine.RTC()
dt = rtc.datetime()

# dt format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
year, month, day, weekday, hour, minute, second, subsecond = dt

print(f"RTC Time: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
print(f"Weekday: {weekday} (1=Monday, 7=Sunday)")
print(f"Subseconds: {subsecond}")
```

### Method 3: Convert RTC to Unix Timestamp

```python
import machine
from time import mktime

def rtc_to_timestamp():
    rtc = machine.RTC()
    dt = rtc.datetime()
    # dt: (year, month, day, weekday, hours, minutes, seconds, subseconds)
    
    # Convert weekday from RTC format (1-7) to mktime format (0-6)
    weekday = (dt[3] - 1) % 7
    
    # mktime expects: (year, month, day, hour, min, sec, weekday, yearday, isdst)
    time_tuple = (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], weekday, 0, 0)
    
    return mktime(time_tuple)

timestamp = rtc_to_timestamp()
print(f"Unix timestamp: {timestamp}")
```

## RTC DateTime Format

The RTC datetime tuple has **8 elements**:

| Index | Field | Description | Range |
|-------|-------|-------------|-------|
| 0 | year | Full year | e.g., 2025 |
| 1 | month | Month | 1-12 |
| 2 | day | Day of month | 1-31 |
| 3 | weekday | Day of week | 1-7 (1=Monday, 7=Sunday) |
| 4 | hours | Hour | 0-23 |
| 5 | minutes | Minute | 0-59 |
| 6 | seconds | Second | 0-59 |
| 7 | subseconds | Subsecond | Platform-dependent |

**Example**:
```python
(2025, 10, 4, 5, 14, 30, 45, 0)
# 2025-10-04 (Friday) 14:30:45.000
```

## Setting RTC Time

### From Unix Timestamp

```python
import machine
from time import gmtime

def set_rtc_from_timestamp(timestamp):
    tm = gmtime(timestamp)
    # tm: (year, month, day, hour, min, sec, weekday, yearday, isdst)
    
    # RTC expects: (year, month, day, weekday, hour, min, sec, subsec)
    # weekday: tm[6] is 0-6 (Monday=0), RTC needs 1-7 (Monday=1)
    rtc_tuple = (tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0)
    
    rtc = machine.RTC()
    rtc.datetime(rtc_tuple)
    print(f"RTC set to: {tm[0]}-{tm[1]:02d}-{tm[2]:02d} {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}")

# Example
set_rtc_from_timestamp(1728048000)
```

### From NTP

```python
import cntptime

# This automatically sets RTC from NTP server
cntptime.settime()
```

## Helper Functions in cntptime Module

### get_rtc_time()

Returns Unix timestamp from RTC, with fallback to `time.time()` if RTC unavailable.

```python
import cntptime

timestamp = cntptime.get_rtc_time()
print(f"Timestamp: {timestamp}")
```

**Use cases**:
- Sensor readings
- Log timestamps
- MQTT message timestamps
- Authentication token timestamps

### get_rtc_datetime()

Returns readable datetime tuple `(year, month, day, hour, minute, second)`.

```python
import cntptime

dt = cntptime.get_rtc_datetime()
if dt:
    print(f"Time: {dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}")
else:
    print("RTC not available")
```

**Use cases**:
- Display time to user
- Log formatting
- Debug output
- Time-based scheduling

## Updating CyberflyClient to Use RTC

### Add Helper Method

Add to `cyberfly_sdk/cyberflySdk.py`:

```python
class CyberflyClient:
    # ... existing code ...
    
    def get_timestamp(self):
        """
        Get current timestamp from RTC or fallback to time.time().
        
        Returns:
            int: Unix timestamp
        """
        try:
            import cntptime
            return cntptime.get_rtc_time()
        except Exception as e:
            print(f"[WARN] Failed to get RTC time: {e}")
            import time
            return time.time()
    
    def get_datetime_string(self):
        """
        Get current datetime as formatted string.
        
        Returns:
            str: Datetime string in ISO format
        """
        try:
            import cntptime
            dt = cntptime.get_rtc_datetime()
            if dt:
                return f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d}T{dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}Z"
        except:
            pass
        
        # Fallback to time module
        import time
        tm = time.gmtime()
        return f"{tm[0]}-{tm[1]:02d}-{tm[2]:02d}T{tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}Z"
```

### Update Sensor Readings

In `cyberfly_sdk/sensors/base_sensors.py`:

```python
class SensorReading:
    def __init__(self, sensor_id, sensor_type, data, status="success", error=None, timestamp=None):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.data = data
        self.status = status
        self.error = error
        
        # Use RTC time instead of time.time()
        if timestamp is None:
            try:
                import cntptime
                self.timestamp = cntptime.get_rtc_time()
            except:
                import time
                self.timestamp = time.time()
        else:
            self.timestamp = timestamp
```

### Update MQTT Messages

In `cyberfly_sdk/shipper_utils.py`:

```python
def make_meta(sender, chain, gas_price, gas_limit, creation_time, ttl):
    # Use RTC time for creation_time
    try:
        import cntptime
        creation_time = cntptime.get_rtc_time()
    except:
        import time
        creation_time = time.time()
    
    # ... rest of function
```

## Comparison: time.time() vs RTC

| Aspect | time.time() | RTC |
|--------|-------------|-----|
| **Source** | System time counter | Hardware clock |
| **Persistence** | Reset on reboot | Persists (if battery-backed) |
| **Accuracy** | Drifts over time | More accurate with crystal |
| **Sync** | May not sync with RTC | Direct hardware read |
| **Availability** | Always available | Requires machine module |
| **Platform** | All platforms | Hardware-dependent |

## Testing RTC

### Test Script

```python
# test_rtc.py
import machine
import time
import cntptime

print("=" * 50)
print("RTC Test Script")
print("=" * 50)

# 1. Check current RTC value
print("\n1. Current RTC datetime:")
rtc = machine.RTC()
dt = rtc.datetime()
print(f"   Raw: {dt}")
print(f"   Formatted: {dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}")

# 2. Check time.time()
print(f"\n2. time.time(): {time.time()}")

# 3. Get RTC timestamp using helper
print(f"\n3. cntptime.get_rtc_time(): {cntptime.get_rtc_time()}")

# 4. Get RTC datetime using helper
dt = cntptime.get_rtc_datetime()
if dt:
    print(f"\n4. cntptime.get_rtc_datetime():")
    print(f"   {dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}")

# 5. Set time from NTP
print("\n5. Setting time from NTP...")
try:
    cntptime.settime()
    print("   Success!")
except Exception as e:
    print(f"   Failed: {e}")

# 6. Check values after NTP sync
print(f"\n6. After NTP sync:")
print(f"   time.time(): {time.time()}")
print(f"   RTC time: {cntptime.get_rtc_time()}")

dt = cntptime.get_rtc_datetime()
if dt:
    print(f"   Formatted: {dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}")

print("\n" + "=" * 50)
print("Test Complete")
print("=" * 50)
```

### Expected Output

```
==================================================
RTC Test Script
==================================================

1. Current RTC datetime:
   Raw: (2025, 10, 4, 5, 14, 30, 45, 0)
   Formatted: 2025-10-04 14:30:45

2. time.time(): 812876750

3. cntptime.get_rtc_time(): 1728048645

4. cntptime.get_rtc_datetime():
   2025-10-04 14:30:45

5. Setting time from NTP...
   [NTP] NTP timestamp: 1728048646
   [NTP] System time.time() before RTC set: 812876751
   [NTP] RTC set to: 2025-10-04 14:30:46 UTC
   [NTP] System time.time() after RTC set: 812876752
   [WARN] time.time() not synced with RTC! Difference: 915171894 seconds
   Success!

6. After NTP sync:
   time.time(): 812876752
   RTC time: 1728048646
   Formatted: 2025-10-04 14:30:46

==================================================
Test Complete
==================================================
```

## Platform-Specific Notes

### ESP32
- RTC available via `machine.RTC()`
- `time.time()` **usually** synced with RTC after `settime()`
- Subseconds field is microseconds

### RP2040 (Raspberry Pi Pico)
- RTC available via `machine.RTC()`
- `time.time()` **NOT** synced with RTC (known issue)
- Must use `cntptime.get_rtc_time()` for accurate time

### ESP8266
- Limited RTC support
- May lose time on reboot (no battery backup)
- Consider external RTC module (DS3231)

## Best Practices

1. **Always use RTC for critical timestamps**
   - Sensor readings
   - MQTT messages
   - Authentication tokens

2. **Set RTC at boot**
   ```python
   import cntptime
   cntptime.settime()  # Sync with NTP
   ```

3. **Use helper functions**
   ```python
   # Instead of time.time()
   timestamp = cntptime.get_rtc_time()
   ```

4. **Handle failures gracefully**
   ```python
   try:
       timestamp = cntptime.get_rtc_time()
   except:
       import time
       timestamp = time.time()
   ```

5. **Test on target hardware**
   - Behavior varies by platform
   - Verify time sync works correctly

## Summary

| Need | Use This |
|------|----------|
| Unix timestamp | `cntptime.get_rtc_time()` |
| Readable datetime | `cntptime.get_rtc_datetime()` |
| Set time from NTP | `cntptime.settime()` |
| Direct RTC access | `machine.RTC().datetime()` |
| Fallback option | `time.time()` |

**Remember**: Always use RTC-based time for accurate timestamps in IoT applications! 🕐
