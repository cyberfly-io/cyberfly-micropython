from time import gmtime
import socket
import struct

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
host = "pool.ntp.org"
# The NTP socket timeout can be configured at runtime by doing: ntptime.timeout = 2
timeout = 1


def time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    print(f"[NTP] Querying NTP server: {host}")
    addr = socket.getaddrinfo(host, 123)[0][-1]
    print(f"[NTP] Resolved address: {addr}")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(timeout)
        s.sendto(NTP_QUERY, addr)
        print(f"[NTP] Query sent, waiting for response...")
        msg = s.recv(48)
        print(f"[NTP] Response received: {len(msg)} bytes")
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    print(f"[NTP] Raw NTP timestamp: {val}")

    # 2024-01-01 00:00:00 converted to an NTP timestamp
    MIN_NTP_TIMESTAMP = 3913056000

    # Y2036 fix
    #
    # The NTP timestamp has a 32-bit count of seconds, which will wrap back
    # to zero on 7 Feb 2036 at 06:28:16.
    #
    # We know that this software was written during 2024 (or later).
    # So we know that timestamps less than MIN_NTP_TIMESTAMP are impossible.
    # So if the timestamp is less than MIN_NTP_TIMESTAMP, that probably means
    # that the NTP time wrapped at 2^32 seconds.  (Or someone set the wrong
    # time on their NTP server, but we can't really do anything about that).
    #
    # So in that case, we need to add in those extra 2^32 seconds, to get the
    # correct timestamp.
    #
    # This means that this code will work until the year 2160.  More precisely,
    # this code will not work after 7th Feb 2160 at 06:28:15.
    #
    if val < MIN_NTP_TIMESTAMP:
        val += 0x100000000

    # Convert timestamp from NTP format to our internal format

    EPOCH_YEAR = gmtime(0)[0]
    print(f"[NTP] Platform EPOCH_YEAR detected: {EPOCH_YEAR}")
    print(f"[NTP] gmtime(0) = {gmtime(0)}")
    
    # Always use 1970 epoch for consistency across platforms
    # ESP32/RP2040 should use Unix epoch (1970)
    NTP_DELTA = 2208988800  # (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
    
    print(f"[NTP] Using NTP_DELTA: {NTP_DELTA} (Unix epoch 1970)")
    result = val - NTP_DELTA
    print(f"[NTP] Final timestamp: {result}")
    return result


# There's currently no timezone support in MicroPython, and the RTC is set in UTC time.
def settime():
    t = time()
    import machine
    import time as time_module

    tm = gmtime(t)
    
    # Print time before setting RTC
    print(f"[NTP] NTP timestamp: {t}")
    print(f"[NTP] System time.time() before RTC set: {time_module.time()}")
    
    # Set the RTC
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    print(f"[NTP] RTC set to: {tm[0]}-{tm[1]:02d}-{tm[2]:02d} {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d} UTC")
    
    # Verify time.time() is now synced with RTC
    current_time = time_module.time()
    print(f"[NTP] System time.time() after RTC set: {current_time}")
    
    # Check if the times match (within 1 second tolerance)
    if abs(current_time - t) > 2:
        print(f"[WARN] time.time() not synced with RTC! Difference: {abs(current_time - t)} seconds")
        print(f"[WARN] Expected: {t}, Got: {current_time}")
    else:
        print(f"[NTP] time.time() successfully synced with RTC")


def get_rtc_time():
    """
    Read current time from RTC and return as Unix timestamp.
    
    This is useful when time.time() is not synced with RTC on some platforms.
    
    Returns:
        int: Unix timestamp (seconds since 1970-01-01) or MicroPython epoch timestamp
    
    Example:
        >>> import cntptime
        >>> timestamp = cntptime.get_rtc_time()
        >>> print(f"Current RTC time: {timestamp}")
    """
    try:
        import machine
    except ImportError:
        # Fallback to time.time() if machine module not available
        from time import time as fallback_time
        return fallback_time()
    
    try:
        rtc = machine.RTC()
        dt = rtc.datetime()
        # dt format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
        # Index:      0     1      2    3        4      5        6        7
        
        # Convert to Unix timestamp using gmtime inverse calculation
        from time import mktime
        
        # mktime expects: (year, month, day, hour, min, sec, weekday, yearday, isdst)
        # We have:        (year, month, day, weekday, hour, min, sec, subsec)
        
        # Convert weekday from RTC format (1-7) to mktime format (0-6)
        weekday = (dt[3] - 1) % 7
        
        # Create time tuple for mktime
        time_tuple = (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], weekday, 0, 0)
        
        timestamp = mktime(time_tuple)
        return timestamp
        
    except Exception as e:
        print(f"[WARN] Failed to read RTC: {e}")
        # Fallback to time.time()
        from time import time as fallback_time
        return fallback_time()


def get_rtc_datetime():
    """
    Read current datetime from RTC in a readable format.
    
    Returns:
        tuple: (year, month, day, hour, minute, second) or None if RTC not available
        
    Example:
        >>> import cntptime
        >>> dt = cntptime.get_rtc_datetime()
        >>> print(f"Current time: {dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}")
    """
    try:
        import machine
        rtc = machine.RTC()
        dt = rtc.datetime()
        # dt format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
        # Return: (year, month, day, hour, minute, second)
        return (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6])
    except Exception as e:
        print(f"[WARN] Failed to read RTC datetime: {e}")
        return None