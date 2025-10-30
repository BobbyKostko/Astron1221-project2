# Astron1221-project2

A lunar phase tracking project that generates a year's worth of moon data and provides an interactive 30-day report viewer.

## Features

### Data Generation (`moon_phase_tracker.py`)
- Generates 365 days of lunar phase data using Skyfield astronomical calculations
- Includes moon phases, illumination percentages, rise/set times
- Detects lunar eclipses and supermoons
- Exports data to CSV format

### 30-Day Lunar Report App (`lunar_report_app.py`)
An interactive Streamlit web application that visualizes any 30-day period from the annual lunar data:

- **Interactive Date Selection**: Choose any 30-day window from the year
- **Visual Charts**: 
  - Moon illumination percentage over time
  - Phase timeline with size-coded illumination
  - Rise and set times visualization
- **Special Events Tracking**: 
  - Lunar eclipse information with details
  - Supermoon occurrences
- **Phase Distribution**: Pie chart showing days per phase
- **Detailed Calendar View**: Complete 30-day breakdown with times

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Generate the lunar data (if not already present):
```bash
python moon_phase_tracker.py
```

## Usage

### Generate Lunar Data
```bash
python moon_phase_tracker.py
```
This will create `lunar_data_1year.csv` with 365 days of moon data starting from 11 PM Eastern Time.

### Run the Web App
```bash
streamlit run lunar_report_app.py
```

The app will open in your web browser. Use the sidebar to select any 30-day period from the year and explore the interactive visualizations.

## Data Fields

The CSV contains the following columns:
- **Date**: Calendar date (Eastern Time)
- **Phase**: Moon phase name (e.g., "Full Moon", "Waxing Crescent")
- **Illumination_%**: Percentage of moon illuminated
- **Moon_Rise**: Time of moonrise (UTC)
- **Moon_Set**: Time of moonset (UTC)
- **Up_All_Day**: True if moon is visible all day
- **Down_All_Day**: True if moon is not visible at all during the day
- **Eclipse_Type**: Type of lunar eclipse (if any)
- **Eclipse_Depth_%**: Percentage of shadow coverage
- **Eclipse_Time**: Time of eclipse (Eastern Time)
- **Supermoon**: True if full moon occurs at perigee (≤360,000 km)

## Files

- `moon_phase_tracker.py` - Data generation script
- `lunar_report_app.py` - Streamlit web application
- `lunar_data_1year.csv` - Generated lunar data (365 days)
- `de421.bsp` - JPL ephemeris data file (required for Skyfield)
- `requirements.txt` - Python package dependencies

## Requirements

- Python 3.7+
- skyfield (astronomical calculations)
- numpy, pandas (data processing)
- streamlit (web interface)
- plotly (interactive charts)