"""
Moon Phase Tracker - Using Skyfield
"""

from datetime import datetime, timezone
from skyfield.api import load

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
    
    # Display result
    print("\n" + "=" * 60)
    print(f"Date: {date_obj.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Phase: {phase}")
    print(f"Illumination: {illumination}%")
    print("=" * 60)

