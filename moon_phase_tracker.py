"""
Moon Phase Tracker - Using Skyfield
"""

from datetime import datetime, timezone, timedelta
from skyfield.api import load, Topos
from skyfield import almanac
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

# Eclipse constants (angular sizes in degrees)
EARTH_ANGULAR_RADIUS_AT_MOON = 1.9   # Earth's angular radius as seen from Moon
SUN_ANGULAR_RADIUS_AT_MOON = 0.27   # Sun's angular radius as seen from Moon (~1AU)


def get_lunar_phase(date):
    """
    Get the lunar phase for a given UTC datetime.
    
    Args:
        date: UTC-aware datetime object
        
    Returns:
        phase_name: String name of the phase (e.g., "Full Moon")
        illumination: Percentage of moon illuminated (0-100%)
    """
    t = ts.utc(date)
    
    # Calculate elongation (angle between sun and moon as seen from Earth)
    # using Skyfield's built-in moon_phase function
    phase_angle = almanac.moon_phase(eph, t)
    elongation = phase_angle.degrees
    
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


def get_moon_rise_set(date, latitude=39.9612, longitude=-82.9988, elevation_m=275.0):
    """
    Get moon rise and set times for a given calendar day using Skyfield almanac.
    
    Args:
        date: UTC-aware datetime object
        latitude: Observer's latitude in degrees (default: 39.9612, Columbus, OH)
        longitude: Observer's longitude in degrees (default: -82.9988, Columbus, OH)
        elevation_m: Observer's elevation in meters (default: 275.0, Columbus, OH)
    
    Returns:
        rise_time: datetime (UTC) of first moonrise in the day, or None
        set_time: datetime (UTC) of first moonset in the day, or None
    """
    # Observer location
    site_topos = Topos(latitude_degrees=latitude,
                       longitude_degrees=longitude,
                       elevation_m=elevation_m)

    # Start/end of the UTC day
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    t0 = ts.utc(start_of_day)
    t1 = ts.utc(end_of_day)

    # Build above-horizon function and find discrete transitions
    above_horizon_fn = almanac.risings_and_settings(eph, moon, site_topos)
    times, events = almanac.find_discrete(t0, t1, above_horizon_fn)

    # Extract first rise and set times within the day
    rise_time = None
    set_time = None
    for t, ev in zip(times, events):
        if ev == 1 and rise_time is None:  # rising edge
            rise_time = t.utc_datetime()
        elif ev == 0 and set_time is None:  # setting edge
            set_time = t.utc_datetime()

        if rise_time is not None and set_time is not None:
            break

    return rise_time, set_time


def check_lunar_eclipse(date):
    """
    Check for lunar eclipse at given time.
    Returns: (eclipse_type, shadow_depth, elongation) where:
        eclipse_type: "Total", "Partial", "Penumbral", or None
        shadow_depth: 0-100 indicating shadow coverage
        elongation: angle from opposition
    """
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    t = ts.utc(date)
    sun_vec = earth.at(t).observe(sun).apparent()
    moon_vec = earth.at(t).observe(moon).apparent()
    
    # Elongation check: must be near opposition (full moon)
    elongation = sun_vec.separation_from(moon_vec).degrees
    if abs(elongation - 180) > 5:  # Not close enough to opposition
        return None, 0, abs(elongation - 180)
    
    # Shadow cone angles (in degrees) - based on angular sizes
    # Penumbra: Earth + Sun angular radii
    # Umbra: Earth - Sun angular radii  
    penumbra_radius = EARTH_ANGULAR_RADIUS_AT_MOON + SUN_ANGULAR_RADIUS_AT_MOON
    umbra_radius = EARTH_ANGULAR_RADIUS_AT_MOON - SUN_ANGULAR_RADIUS_AT_MOON
    
    # Offset from perfect opposition
    offset = abs(elongation - 180)
    
    # Classify eclipse
    if offset < umbra_radius * 0.5:
        return "Total", int(100 * (1 - offset / umbra_radius)), offset
    elif offset < umbra_radius:
        return "Partial", int(100 * (1 - offset / umbra_radius)), offset
    elif offset < penumbra_radius:
        return "Penumbral", int(50 * (1 - offset / penumbra_radius)), offset
    return None, 0, offset


def sample_night_for_eclipse(date_utc, rise_time, set_time):
    """
    Sample throughout a single night (hourly) to find maximum eclipse.
    Returns: (eclipse_type, shadow_depth, max_eclipse_time_utc)
    """
    if not rise_time or not set_time:
        return None, 0, None
    
    best_eclipse_type = None
    best_depth = 0
    best_time = None
    
    # Get the sampling window from rise/set times
    night_start = rise_time
    night_end = set_time
    # If set time is before rise time on the calendar, moon sets next day
    if night_end < night_start:
        night_end = night_end + timedelta(days=1)
    
    # Sample every hour throughout the visible period
    current_time = night_start
    max_samples = 48  # Safety: max 2 days of hourly samples
    sample_count = 0
    
    while current_time <= night_end and sample_count < max_samples:
        eclipse_type, depth, _ = check_lunar_eclipse(current_time)
        
        # Track best eclipse found
        if eclipse_type and depth > best_depth:
            best_eclipse_type = eclipse_type
            best_depth = depth
            best_time = current_time
        
        current_time += timedelta(hours=1)
        sample_count += 1
        
        # Safety check: don't sample beyond 48 hours
        if (current_time - night_start).total_seconds() > 86400 * 2:
            break
    
    return best_eclipse_type, best_depth, best_time


def main():
    print("=" * 60)
    print("Moon Phase Tracker - Data Generator (1900-2035)")
    print("=" * 60)
    
    # Set date range: January 1, 1900 to December 31, 2035 at 11PM Eastern time
    eastern = ZoneInfo('America/New_York')
    start_date = datetime(1900, 1, 1, 23, 0, 0, tzinfo=eastern)
    end_date = datetime(2035, 12, 31, 23, 0, 0, tzinfo=eastern)
    # Convert to UTC
    start_date_utc = start_date.astimezone(timezone.utc)
    end_date_utc = end_date.astimezone(timezone.utc)
    
    # Calculate number of days
    total_days = (end_date_utc - start_date_utc).days + 1
    
    print(f"\nStarting from: {start_date.strftime('%Y-%m-%d %H:%M:%S')} Eastern Time")
    print(f"                     ({start_date_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
    print(f"\nEnding at: {end_date.strftime('%Y-%m-%d %H:%M:%S')} Eastern Time")
    print(f"                 ({end_date_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
    print(f"\nGenerating data for {total_days} days (1900-2035)...")
    # Initialize lists to store data
    dates = []
    phases = []
    illuminations = []
    rise_times = []
    set_times = []
    eclipse_types = []
    eclipse_depths = []
    eclipse_times = []
    supermoon_flags = []
    # Dictionary to store eclipses by their calendar date (Eastern time)
    # Key: date string "YYYY-MM-DD", Value: (eclipse_type, depth, time_str)
    eclipse_dict = {}
    # Generate data for all days from 1900 to 2035
    for day in range(total_days):
        # Calculate the date for lunar phase (11PM Eastern)
        date_utc = start_date_utc + timedelta(days=day)
        date_local = date_utc.astimezone(eastern)
        # Get lunar phase at 11PM Eastern
        phase, illumination = get_lunar_phase(date_utc)
        # --- SUPERMOON CHECK ---
        # Compute geocentric distance at 11PM Eastern (UTC)
        t = ts.utc(date_utc)
        moon_apparent = earth.at(t).observe(moon).apparent()
        distance_km = moon_apparent.distance().km  # Skyfield distance is in AU by default; .km gets km
        # Supermoon definition: Full Moon and ≤360,000 km
        is_supermoon = phase == "Full Moon" and distance_km <= 360000
        supermoon_flags.append(is_supermoon)
        # --- END SUPERMOON CHECK ---
        # Get moon rise/set times for the calendar day
        rise_time, set_time = get_moon_rise_set(date_utc)
        # Check for lunar eclipse - sample hourly throughout the night if near full moon
        eclipse_type, eclipse_depth, eclipse_time_utc = None, 0, None
        if illumination > 85:  # Only check during near full moons
            eclipse_type, eclipse_depth, eclipse_time_utc = sample_night_for_eclipse(
                date_utc, rise_time, set_time
            )
            # Store eclipse info keyed by its actual calendar date (in Eastern time)
            if eclipse_time_utc:
                eclipse_local = eclipse_time_utc.astimezone(eastern)
                eclipse_date = eclipse_local.strftime('%Y-%m-%d')
                eclipse_time_str = eclipse_local.strftime('%Y-%m-%d %H:%M ET')
                # Store in dictionary by actual date (keep the one with highest depth if multiple)
                if eclipse_date not in eclipse_dict or eclipse_depth > eclipse_dict[eclipse_date][1]:
                    eclipse_dict[eclipse_date] = (eclipse_type, eclipse_depth, eclipse_time_str)
        # Format times for display
        rise_str = "No rise" if rise_time is None else rise_time.strftime('%H:%M:%S UTC')
        set_str = "No set" if set_time is None else set_time.strftime('%H:%M:%S UTC')
        current_date = date_local.strftime('%Y-%m-%d')
        # Store data
        dates.append(current_date)
        phases.append(phase)
        illuminations.append(illumination)
        rise_times.append(rise_str)
        set_times.append(set_str)
    # After all days, map eclipse info for each calendar date
    for i, current_date in enumerate(dates):
        if current_date in eclipse_dict:
            eclipse_type, eclipse_depth, eclipse_time_str = eclipse_dict[current_date]
            eclipse_types.append(eclipse_type)
            eclipse_depths.append(eclipse_depth)
            eclipse_times.append(eclipse_time_str)
        else:
            eclipse_types.append("None")
            eclipse_depths.append(0)
            eclipse_times.append("None")
        # Progress indicator
        if (i + 1) % 500 == 0:
            print(f"  Generated data for {i + 1}/{total_days} days...")
    # Create pandas DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Phase': phases,
        'Illumination_%': illuminations,
        'Moon_Rise': rise_times,
        'Moon_Set': set_times,
        'Eclipse_Type': eclipse_types,
        'Eclipse_Depth_%': eclipse_depths,
        'Eclipse_Time': eclipse_times,
        'Supermoon': supermoon_flags
    })
    print("\nData generation complete!")
    print("\nFirst 10 rows:")
    print(df.head(10))
    print(f"\nTotal rows: {len(df)}")
    print("=" * 60)
    # Save to CSV (will overwrite if file exists)
    csv_filename = 'lunar_data_1900_2035.csv'
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
        print(f"\nRemoved existing file: {csv_filename}")
    df.to_csv(csv_filename, index=False)
    print(f"Data saved to: {csv_filename}")
    print("=" * 60)

if __name__ == "__main__":
    main()

