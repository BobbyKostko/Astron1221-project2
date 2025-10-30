# 30-Day Lunar Report App - Quick Start Guide

## Running the App

1. **Make sure you have all dependencies installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure the CSV file exists:**
   - The app requires `lunar_data_1year.csv` to be in the same directory
   - If you don't have it, run: `python moon_phase_tracker.py`

3. **Launch the Streamlit app:**
   ```bash
   streamlit run lunar_report_app.py
   ```

4. **The app will open in your default web browser automatically!**

## Using the App

### Main Features

#### 📅 Date Selection (Sidebar)
- Click on the date picker to choose any start date
- The app will show you the next 30 days from your selected date
- The date range is automatically limited based on available data

#### 📊 Key Metrics (Top Section)
- **Full Moons**: Number of full moon occurrences
- **New Moons**: Number of new moon occurrences  
- **Supermoons**: Number of supermoon events
- **Lunar Eclipses**: Number of eclipse occurrences

#### 🌙 Visualization Tabs

**1. Illumination Chart**
- Area chart showing how moon illumination changes
- Hover to see exact values for each day
- Clear visualization of lunar cycle progression

**2. Phase Timeline**
- Scatter plot with moon phases on Y-axis
- Point size represents illumination percentage
- Color-coded by phase type
- Quick visual reference for phase progression

**3. Rise & Set Times**
- Line chart showing when moon rises and sets
- Blue line = moonrise
- Pink line = moonset
- Times shown in UTC
- Grayed out when moon is always up or down

#### 🌑 Special Events

**Eclipses Section:**
- Shows all lunar eclipses in your 30-day window
- Click to expand and see:
  - Eclipse type (Total, Partial, Penumbral)
  - Depth percentage
  - Time of occurrence

**Supermoon Section:**
- Lists all supermoon occurrences
- Shows date and illumination percentage

#### 📅 Calendar View
- Complete table of all 30 days
- Includes:
  - Emoji representing each phase
  - Phase name
  - Illumination percentage
  - Rise and set times

#### 📈 Summary Statistics

**Left Column - Phase Distribution:**
- Pie chart showing how many days each phase appears
- Visual breakdown of your 30-day period

**Center Column - Illumination Stats:**
- Average, maximum, and minimum illumination
- Quick numerical summary

**Right Column - Quick Facts:**
- Date range of your report
- Days with moon visible all day
- Days with moon not visible

## Tips for Best Experience

1. **Try Different Dates:** Explore different 30-day periods to see how lunar cycles vary throughout the year

2. **Look for Patterns:** Watch how illumination smoothly transitions through phases

3. **Check Special Events:** Look for months with eclipses or multiple supermoons

4. **Interactive Charts:** Hover over data points, zoom in, and pan around charts

5. **Compare Periods:** Switch between different months to compare lunar activity

## Troubleshooting

**App won't start?**
- Make sure `lunar_data_1year.csv` exists in the same folder as the app
- Verify all packages are installed: `pip list` and check for streamlit, plotly, pandas

**No data showing?**
- Check that the CSV file was generated correctly
- Try regenerating: `python moon_phase_tracker.py`

**Charts look wrong?**
- Make sure your browser is up to date
- Try refreshing the page (F5)
- Clear browser cache if needed

## Need Help?

Check the main README.md for more information about:
- Data generation
- CSV file format
- Project overview

