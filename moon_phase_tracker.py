"""
Moon Phase Tracker - Using Skyfield
"""

from datetime import datetime, timezone, timedelta
from skyfield.api import load, Topos
import numpy as np

# Load timescale and ephemeris
ts = load.timescale()
eph = load('de421.bsp')

earth = eph['earth']
moon = eph['moon']
sun = eph['sun']


def get_lunar_phase(date):
    """
    Get the lunar phase for a given UTC datetime.
    
    Args:
        date: datetime object or string in format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
              Date/time should be in UTC
              
    Returns:
        phase_name: String name of the phase (e.g., "Full Moon")
        illumination: Percentage of moon illuminated (0-100%)
    """
    # Convert string to datetime if needed
    if isinstance(date, str):
        if len(date) <= 10:  # Just date, no time
            date = datetime.strptime(date, '%Y-%m-%d')
        else:  # Date with time
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    
    # Make sure the datetime is UTC-aware
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    t = ts.utc(date)
    
    # Calculate elongation (angle between sun and moon as seen from Earth)
    sun_pos = earth.at(t).observe(sun).apparent()
    moon_pos = earth.at(t).observe(moon).apparent()
    elongation = sun_pos.separation_from(moon_pos).degrees
    
    # Calculate illumination percentage
    # elongation: 0° (New) -> 180° (Full) -> 360° (New)
    illumination = (1 - abs(elongation - 180) / 180) * 100
    illumination = round(illumination, 1)
    
    # Determine phase name
    if elongation < 22.5 or elongation >= 337.5:
        phase_name = "New Moon"
    elif elongation < 67.5:
        phase_name = "Waxing Crescent"
    elif elongation < 112.5:
        phase_name = "First Quarter"
    elif elongation < 157.5:
        phase_name = "Waxing Gibbous"
    elif elongation < 202.5:
        phase_name = "Full Moon"
    elif elongation < 247.5:
        phase_name = "Waning Gibbous"
    elif elongation < 292.5:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"
    
    return phase_name, illumination


def binary_search_rise_set(observer, t_start, t_end):
    """
    Binary search to find the exact time when moon crosses horizon.
    Returns datetime in UTC.
    """
    # Convert time objects to datetime for easier manipulation
    dt_start = t_start.utc_datetime()
    dt_end = t_end.utc_datetime()
    
    # Binary search for horizon crossing
    for _ in range(20):  # 20 iterations for ~1 second precision
        mid = dt_start + (dt_end - dt_start) / 2
        t_mid = ts.utc(mid)
        alt, az, distance = observer.at(t_mid).observe(moon).apparent().altaz()
        altitude = alt.degrees
        
        if altitude >= 0:
            dt_end = mid
        else:
            dt_start = mid
        
        if (dt_end - dt_start).total_seconds() < 0.01:  # Stop when within 0.01 seconds
            break
    
    return dt_start + (dt_end - dt_start) / 2


def get_moon_rise_set(date, latitude=39.9612, longitude=-82.9988, elevation_m=275.0):
    """
    Get moon rise and set times for a given calendar day.
    
    Args:
        date: String in format 'YYYY-MM-DD' or datetime object
              Date should be in UTC
        latitude: Observer's latitude in degrees (default: 39.9612, Columbus, OH)
        longitude: Observer's longitude in degrees (default: -82.9988, Columbus, OH)
        elevation_m: Observer's elevation in meters (default: 275.0, Columbus, OH)
    
    Returns:
        rise_time: datetime object of moon rise time (UTC), or None if moon doesn't rise
        set_time: datetime object of moon set time (UTC), or None if moon doesn't set
        moon_up_all_day: Boolean indicating if moon is up all day
        moon_down_all_day: Boolean indicating if moon is down all day
    """
    # Convert string to datetime if needed
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    
    # Make sure the datetime is UTC-aware
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    # Create observer location
    observer = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude, 
                             elevation_m=elevation_m)
    
    # Get the start and end of the day (00:00 and 23:59:59.999...)
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999000)
    
    # Convert to skyfield times
    t0 = ts.utc(start_of_day)
    t1 = ts.utc(end_of_day)
    
    # Sample the day to find horizon crossings
    # Split the day into increments and check moon altitude
    num_samples = 288  # Check every 5 minutes (288 samples per day)
    step_days = 1 / num_samples
    
    rise_times = []
    set_times = []
    previous_altitude = None
    
    # Check at start of day
    alt, az, distance = observer.at(t0).observe(moon).apparent().altaz()
    previous_altitude = alt.degrees
    moon_up_all_day = previous_altitude >= 0
    
    # Sample throughout the day
    for i in range(1, num_samples):
        t = ts.utc(start_of_day.replace(tzinfo=timezone.utc) + timedelta(days=i*step_days))
        alt, az, distance = observer.at(t).observe(moon).apparent().altaz()
        current_altitude = alt.degrees
        
        # Detect horizon crossing
        if previous_altitude is not None:
            if previous_altitude < 0 and current_altitude >= 0:
                # Rise: crossing from below to above horizon
                # Binary search for more accurate time
                t_prev = ts.utc(start_of_day.replace(tzinfo=timezone.utc) + timedelta(days=(i-1)*step_days))
                rise_time = binary_search_rise_set(observer, t_prev, t)
                if rise_time:
                    rise_times.append(rise_time)
            elif previous_altitude >= 0 and current_altitude < 0:
                # Set: crossing from above to below horizon
                t_prev = ts.utc(start_of_day.replace(tzinfo=timezone.utc) + timedelta(days=(i-1)*step_days))
                set_time = binary_search_rise_set(observer, t_prev, t)
                if set_time:
                    set_times.append(set_time)
        
        previous_altitude = current_altitude
    
    # Check if moon is down all day
    moon_down_all_day = previous_altitude < 0 and not rise_times
    
    # Return first rise and first set times (in UTC)
    rise_time = rise_times[0] if rise_times else None
    set_time = set_times[0] if set_times else None
    
    return rise_time, set_time, moon_up_all_day, moon_down_all_day


# Main program!
if __name__ == "__main__":
    print("=" * 60)
    print("Moon Phase Tracker")
    print("=" * 60)
    print("\nEnter a UTC date and time to get the lunar phase.")
    print("Format: YYYY-MM-DD HH:MM:SS")
    print("Example: 2024-01-15 12:30:00")
    print("(or just press Enter for current time)")
    print()
    
    user_input = input("Enter UTC datetime: ").strip()
    
    if not user_input:
        # Use current time if empty input
        date_obj = datetime.now(timezone.utc)
    else:
        # Parse user input
        date_obj = datetime.strptime(user_input, '%Y-%m-%d %H:%M:%S')
        date_obj = date_obj.replace(tzinfo=timezone.utc)
    
    # Get lunar phase
    phase, illumination = get_lunar_phase(date_obj)
    
    # Get moon rise/set times for the day
    date_str = date_obj.strftime('%Y-%m-%d')
    rise_time, set_time, moon_up_all_day, moon_down_all_day = get_moon_rise_set(date_str)
    
    # Display result
    print("\n" + "=" * 60)
    print(f"Date: {date_obj.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Phase: {phase}")
    print(f"Illumination: {illumination}%")
    print("-" * 60)
    print("Moon Rise/Set Times (Columbus, OH):")
    if moon_up_all_day:
        print("  Moon is up all day")
    elif moon_down_all_day:
        print("  Moon is down all day")
    else:
        if rise_time:
            print(f"  Moon rises at: {rise_time.strftime('%H:%M:%S')} UTC")
        else:
            print("  No moon rise")
        if set_time:
            print(f"  Moon sets at: {set_time.strftime('%H:%M:%S')} UTC")
        else:
            print("  No moon set")
    print("=" * 60)

