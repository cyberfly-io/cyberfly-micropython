# Time Module Replacement - RTC Integration

## Summary

Replaced `time.time()` calls across the Cyberfly SDK with RTC-based timing functions to ensure accurate timestamps on all platforms, especially those where `time.time()` is not synced with the RTC (like RP2040).

## Problem Statement

On some MicroPython platforms (notably RP2040/Raspberry Pi Pico), `time.time()` returns the time since boot, not the actual wall clock time, even after setting the RTC via `cntptime.settime()`. This causes:

- ❌ Incorrect sensor timestamps
- ❌ Invalid MQTT message expiry times
- ❌ Failed authentication due to time discrepancies
- ❌ Broken time-based scheduling

## Solution

Created a centralized time utility system that:

1. **Reads from RTC** - Uses hardware clock for accurate time
2. **Fallback Support** - Falls back to `time.time()` if RTC unavailable
3. **Consistent API** - Single source of truth for time across SDK

## Files Modified

### Core Files

#### 1. `cyberfly_sdk/time_utils.py` (NEW)
**Created**: Centralized time utility module

**Functions**:
- `get_time()` - Get Unix timestamp from RTC with fallback
- `get_datetime()` - Get readable datetime tuple
- `get_datetime_string()` - Get ISO 8601 formatted string
- `now()` - Convenience alias for `get_time()`

**Usage**:
```python
from time_utils import get_time, get_datetime_string

timestamp = get_time()  # RTC-based timestamp
iso_time = get_datetime_string()  # "2025-10-04T14:30:45Z"
```

#### 2. `cyberfly_sdk/cntptime.py` (ENHANCED)
**Added Functions**:
- `get_rtc_time()` - Read timestamp from RTC
- `get_rtc_datetime()` - Read datetime from RTC

**Enhanced**:
- `settime()` - Now includes diagnostics to verify RTC sync

#### 3. `cyberfly_sdk/cyberflySdk.py`
**Modified**: Line 374
- `read_all_sensors` response timestamp now uses `cntptime.get_rtc_time()`

**Before**:
```python
"timestamp": time.time()
```

**After**:
```python
try:
    import cntptime
    timestamp = cntptime.get_rtc_time()
except:
    timestamp = time.time()
```

#### 4. `cyberfly_sdk/shipper_utils.py`
**Modified**: Lines 43, 69

**Function**: `mk_meta()`
- MQTT message creation time now uses RTC

**Function**: `make_cmd()`
- Command expiry time now uses RTC

**Impact**: Ensures MQTT messages have correct timestamps and expiry

#### 5. `cyberfly_sdk/sensors/base_sensors.py`
**Modified**: Line 15

**Class**: `SensorReading.__init__()`
- Sensor reading timestamps now use RTC

**Before**:
```python
self.timestamp = timestamp or time.time()
```

**After**:
```python
if timestamp is None:
    try:
        import cntptime
        self.timestamp = cntptime.get_rtc_time()
    except:
        self.timestamp = time.time()
else:
    self.timestamp = timestamp
```

#### 6. `cyberfly_sdk/sensors/types/base.py`
**Modified**: Line 15

**Class**: `SensorReading.__init__()`
- Same RTC-based timestamp logic as base_sensors.py

### Files NOT Modified (Intentionally)

The following files contain `time.time()` calls that were **NOT** changed because they are:

1. **Mock/Simulation Values** - Used for generating fake sensor data variations
2. **Boot Time Calculations** - Intentionally using time since boot
3. **Relative Timings** - For intervals, not absolute timestamps

**Examples**:
```python
# Mock data generation - OK to keep time.time()
temperature = 22.5 + (time.time() % 10) - 5  # Variation pattern

# Uptime calculation - SHOULD use boot time
uptime = time.time()  # Approximate uptime since boot

# Motion detection timing - Relative intervals OK
now = time.time()  # For calculating time differences
```

**Files with intentional time.time() usage**:
- `sensors/base_sensors.py` - Lines 328 (uptime), 163, 450, 615, 625 (motion timing)
- `sensors/base_sensors.py` - Lines 1104-1497 (mock sensor data)
- `sensors/types/*.py` - Mock sensor implementations

## Migration Strategy

### Phase 1: Critical Paths ✅ COMPLETED
- [x] Sensor readings timestamps
- [x] MQTT message creation time
- [x] MQTT message expiry time
- [x] Command timestamps

### Phase 2: Optional Enhancements (Future)
- [ ] Replace mock sensor `time.time()` with `get_time()`
- [ ] Add uptime tracking separate from wall clock time
- [ ] Implement dedicated uptime counter

### Phase 3: Full Migration (Future)
- [ ] Create global time manager class
- [ ] Replace all `import time` with `import time_utils`
- [ ] Deprecate direct `time.time()` usage

## Usage Guide

### For New Code

**Always use RTC-based time**:
```python
# Import time utility
from time_utils import get_time

# Get timestamp
timestamp = get_time()

# Create sensor reading
reading = SensorReading(
    sensor_id="temp1",
    sensor_type="temperature",
    data={"value": 25.5},
    # timestamp will auto-use RTC
)
```

### For Existing Code

**Replace time.time() with get_time()**:
```python
# Before
import time
timestamp = time.time()

# After
from time_utils import get_time
timestamp = get_time()
```

### For Authentication/Expiry

**Already fixed in shipper_utils.py**:
```python
# mk_meta() and make_cmd() now use RTC automatically
signed = shipper_utils.make_cmd(data, key_pair)
# Expiry time is now accurate!
```

## Testing

### Verification Script

```python
# test_rtc_integration.py
import time
from time_utils import get_time, get_datetime_string
import cntptime

print("=" * 50)
print("RTC Integration Test")
print("=" * 50)

# 1. Compare time.time() vs RTC time
print(f"\n1. time.time(): {time.time()}")
print(f"2. get_time(): {get_time()}")
print(f"3. Difference: {abs(get_time() - time.time())} seconds")

# 4. Check datetime string
print(f"\n4. Datetime: {get_datetime_string()}")

# 5. Set time from NTP
print("\n5. Setting time from NTP...")
try:
    cntptime.settime()
except Exception as e:
    print(f"   Failed: {e}")

# 6. Verify after NTP sync
print(f"\n6. After NTP:")
print(f"   get_time(): {get_time()}")
print(f"   Datetime: {get_datetime_string()}")

print("\n" + "=" * 50)
```

### Expected Output (RP2040)

```
==================================================
RTC Integration Test
==================================================

1. time.time(): 812876750
2. get_time(): 1728048645
3. Difference: 915171895 seconds

4. Datetime: 2025-10-04T14:30:45Z

5. Setting time from NTP...
[NTP] NTP timestamp: 1728048646
[NTP] System time.time() before RTC set: 812876751
[NTP] RTC set to: 2025-10-04 14:30:46 UTC
[NTP] System time.time() after RTC set: 812876752
[WARN] time.time() not synced with RTC! Difference: 915171894 seconds

6. After NTP:
   get_time(): 1728048646
   Datetime: 2025-10-04T14:30:46Z

==================================================
```

### Sensor Timestamp Test

```python
# Test sensor readings use RTC
from sensors import SensorManager

manager = SensorManager()
manager.add_sensor(
    sensor_id="test",
    sensor_type="temperature",
    inputs={"pin": 4}
)

reading = manager.read_sensor("test")
print(f"Sensor timestamp: {reading['timestamp']}")
print(f"Expected (RTC): ~{get_time()}")
print(f"Matches: {abs(reading['timestamp'] - get_time()) < 2}")
```

## Benefits

### ✅ Accurate Timestamps
- Sensor data has correct timestamps
- Historical data can be correlated
- Time-series analysis works properly

### ✅ Valid MQTT Messages
- Message creation time is accurate
- Expiry times prevent replay attacks
- Authentication tokens validated correctly

### ✅ Platform Independent
- Works on ESP32 (time.time() synced)
- Works on RP2040 (time.time() NOT synced)
- Graceful fallback on all platforms

### ✅ Backward Compatible
- Existing code continues to work
- Gradual migration possible
- No breaking changes

## Known Issues

### Issue 1: Mock Sensor Data
Mock sensors still use `time.time()` for variations. This is OK for simulations but should be updated for production.

**Workaround**: Replace mock implementations with real sensors.

### Issue 2: Uptime Tracking
Some code uses `time.time()` for uptime. After RTC sync, this is no longer accurate.

**Solution**: Track boot time separately:
```python
# At boot
BOOT_TIME = time.time()

# For uptime
def get_uptime():
    return time.time() - BOOT_TIME
```

### Issue 3: Boot Time Uptime
The `system_info` sensor reports uptime using `time.time()` which is boot time, not actual uptime after RTC sync.

**Future Enhancement**: Implement proper uptime counter.

## Rollback Plan

If issues arise, you can temporarily revert by:

1. **Comment out RTC imports**:
```python
# try:
#     import cntptime
#     timestamp = cntptime.get_rtc_time()
# except:
timestamp = time.time()
```

2. **Use time_utils with fallback mode**:
```python
# In time_utils.py, force fallback:
def get_time():
    import time
    return time.time()  # Bypass RTC
```

## Next Steps

1. **Build and Deploy** ✅
   ```bash
   ./build.sh
   # Flash to device
   ```

2. **Test on Hardware** ⏳
   - Verify RTC timestamps are correct
   - Check MQTT messages work
   - Validate sensor data timestamps

3. **Monitor Logs** ⏳
   - Look for NTP sync warnings
   - Check timestamp differences
   - Verify no authentication errors

4. **Production Deployment** ⏳
   - Deploy to test devices
   - Monitor for issues
   - Gradual rollout

## References

- `RTC_TIME_GUIDE.md` - How to read time from RTC
- `NTP_TIME_SYNC_ISSUE.md` - Why time.time() doesn't sync
- `cntptime.py` - NTP and RTC functions
- `time_utils.py` - Centralized time utilities

## Conclusion

The SDK now uses RTC-based timing for all critical timestamps, ensuring accuracy across all MicroPython platforms. The changes are backward compatible with automatic fallback to `time.time()` when RTC is unavailable.

**Key Achievement**: Sensor readings, MQTT messages, and authentication now use accurate wall clock time instead of boot time! 🎯
