"""
Timezone utilities for Stableman application.
Provides client-side timezone detection using Streamlit's native context.
"""
import streamlit as st
import pytz


def get_user_timezone():
    """
    Get the user's local timezone from Streamlit context.
    
    Returns:
        pytz.timezone: User's local timezone object, defaults to UTC if detection fails
    """
    try:
        # Get timezone from Streamlit's context
        browser_timezone = st.context.timezone
        
        if browser_timezone:
            timezone_obj = pytz.timezone(browser_timezone)
            return timezone_obj
        else:
            return pytz.UTC
    except Exception as e:
        print(f"DEBUG: Error getting timezone from context: {e}")
        return pytz.UTC


def format_timestamp(timestamp_ms, timezone_obj=None):
    """
    Format a timestamp in milliseconds to a human-readable string in local timezone.
    
    Args:
        timestamp_ms: Unix timestamp in milliseconds
        timezone_obj: Optional timezone object, gets user timezone if None
        
    Returns:
        tuple: (formatted_time_string, relative_time_string)
    """
    from datetime import datetime
    
    if timezone_obj is None:
        timezone_obj = get_user_timezone()
    
    try:
        # Convert timestamp to UTC datetime
        if isinstance(timestamp_ms, (int, float)) and timestamp_ms > 0:
            utc_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.UTC)
        else:
            # Handle non-numeric timestamps
            utc_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.UTC) if timestamp_ms else datetime.now(pytz.UTC)
            if not utc_time.tzinfo:
                utc_time = utc_time.replace(tzinfo=pytz.UTC)
        
        # Convert to local timezone
        local_time = utc_time.astimezone(timezone_obj)
        
        # Format human-readable time
        formatted_time = local_time.strftime("%B %d, %Y at %I:%M %p %Z")
        
        # Calculate relative time
        now_utc = datetime.now(pytz.UTC)
        time_diff = now_utc - utc_time
        
        if time_diff.days > 0:
            relative = f"{time_diff.days} day{'s' if time_diff.days != 1 else ''} ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            relative = "Just now"
        
        return formatted_time, relative
        
    except Exception as e:
        return f"Invalid timestamp ({timestamp_ms})", "Unknown time"


def convert_datetime_to_local(dt, timezone_obj=None):
    """
    Convert a datetime object to local timezone.
    
    Args:
        dt: Datetime object (assumed UTC if no timezone info)
        timezone_obj: Optional timezone object, gets user timezone if None
        
    Returns:
        datetime: Datetime in local timezone
    """
    if timezone_obj is None:
        timezone_obj = get_user_timezone()
    
    # Ensure datetime has timezone info
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # Convert to local timezone
    return dt.astimezone(timezone_obj)