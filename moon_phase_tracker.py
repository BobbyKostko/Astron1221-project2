"""
Moon Phase Tracker - Using Skyfield
"""

from datetime import datetime, timezone, timedelta
from skyfield.api import load, Topos
import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo
import os

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
    start_altitude = None
    
    # Check at start of day
    alt, az, distance = observer.at(t0).observe(moon).apparent().altaz()
    start_altitude = alt.degrees
    previous_altitude = start_altitude
    
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
    
    # Determine if moon is up all day (starts up and never sets)
    moon_up_all_day = start_altitude >= 0 and not set_times
    
    # Determine if moon is down all day (starts down and never rises)
    moon_down_all_day = start_altitude < 0 and not rise_times
    
    # Return first rise and first set times (in UTC)
    rise_time = rise_times[0] if rise_times else None
    set_time = set_times[0] if set_times else None
    
    return rise_time, set_time, moon_up_all_day, moon_down_all_day


# Main program!
if __name__ == "__main__":
    print("=" * 60)
    print("Moon Phase Tracker - 1 Year Data Generator")
    print("=" * 60)
    
    # Get current date at 11PM Eastern time
    eastern = ZoneInfo('America/New_York')
    current_et = datetime.now(eastern)
    start_date = current_et.replace(hour=23, minute=0, second=0, microsecond=0)
    
    # Convert to UTC
    start_date_utc = start_date.astimezone(timezone.utc)
    
    print(f"\nStarting from: {start_date.strftime('%Y-%m-%d %H:%M:%S')} Eastern Time")
    print(f"                     ({start_date_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
    print("\nGenerating data for the next 365 days...")
    
    # Initialize lists to store data
    dates = []
    phases = []
    illuminations = []
    rise_times = []
    set_times = []
    moon_up_all_days = []
    moon_down_all_days = []
    
    # Generate data for next 365 days
    for day in range(365):
        # Calculate the date for lunar phase (11PM Eastern)
        date_utc = start_date_utc + timedelta(days=day)
        date_local = date_utc.astimezone(eastern)
        
        # Get lunar phase at 11PM Eastern
        phase, illumination = get_lunar_phase(date_utc)
        
        # Get moon rise/set times for the calendar day
        date_str = date_utc.strftime('%Y-%m-%d')
        rise_time, set_time, moon_up_all_day, moon_down_all_day = get_moon_rise_set(date_str)
        
        # Format times for display
        rise_str = "All day" if moon_up_all_day else ("No rise" if rise_time is None else rise_time.strftime('%H:%M:%S UTC'))
        set_str = "Down all day" if moon_down_all_day else ("No set" if set_time is None else set_time.strftime('%H:%M:%S UTC'))
        
        # Store data
        dates.append(date_local.strftime('%Y-%m-%d'))
        phases.append(phase)
        illuminations.append(illumination)
        rise_times.append(rise_str)
        set_times.append(set_str)
        moon_up_all_days.append(moon_up_all_day)
        moon_down_all_days.append(moon_down_all_day)
        
        # Progress indicator
        if (day + 1) % 50 == 0:
            print(f"  Generated data for {day + 1}/365 days...")
    
    # Create pandas DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Phase': phases,
        'Illumination_%': illuminations,
        'Moon_Rise': rise_times,
        'Moon_Set': set_times,
        'Up_All_Day': moon_up_all_days,
        'Down_All_Day': moon_down_all_days
    })
    
    print("\nData generation complete!")
    print("\nFirst 10 rows:")
    print(df.head(10))
    print(f"\nTotal rows: {len(df)}")
    print("=" * 60)
    
    # Save to CSV (will overwrite if file exists)
    csv_filename = 'lunar_data_1year.csv'
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
        print(f"\nRemoved existing file: {csv_filename}")
    
    df.to_csv(csv_filename, index=False)
    print(f"Data saved to: {csv_filename}")
    print("=" * 60)

