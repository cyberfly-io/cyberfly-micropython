"""
Time utilities for Cyberfly SDK.
Provides RTC-based time functions with fallback to system time.
"""

def get_time():
    """
    Get current timestamp from RTC with fallback to time.time().
    
    This function ensures accurate timestamps across all platforms by:
    1. Attempting to read from RTC (hardware clock)
    2. Falling back to time.time() if RTC unavailable
    
    Returns:
        int/float: Unix timestamp in seconds
        
    Usage:
        >>> from time_utils import get_time
        >>> timestamp = get_time()
        >>> print(f"Current time: {timestamp}")
    """
    try:
        import cntptime
        return cntptime.get_rtc_time()
    except Exception:
        try:
            import time
            return time.time()
        except:
            # Last resort: return 0 (epoch)
            return 0


def get_datetime():
    """
    Get current datetime from RTC in readable format.
    
    Returns:
        tuple: (year, month, day, hour, minute, second) or None
        
    Usage:
        >>> from time_utils import get_datetime
        >>> dt = get_datetime()
        >>> if dt:
        ...     print(f"Time: {dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}")
    """
    try:
        import cntptime
        return cntptime.get_rtc_datetime()
    except:
        return None


def get_datetime_string():
    """
    Get current datetime as ISO 8601 formatted string.
    
    Returns:
        str: Datetime in format "YYYY-MM-DDTHH:MM:SSZ"
        
    Usage:
        >>> from time_utils import get_datetime_string
        >>> print(get_datetime_string())
        2025-10-04T14:30:45Z
    """
    dt = get_datetime()
    if dt:
        return f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d}T{dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}Z"
    
    # Fallback to gmtime
    try:
        from time import gmtime
        timestamp = get_time()
        tm = gmtime(timestamp)
        return f"{tm[0]}-{tm[1]:02d}-{tm[2]:02d}T{tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}Z"
    except:
        return "1970-01-01T00:00:00Z"


# Convenience alias
now = get_time
