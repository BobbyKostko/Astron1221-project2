import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont
import io

# Page configuration
st.set_page_config(
    page_title="30-Day Lunar Report",
    page_icon="🌙",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('lunar_data_1year.csv')
    # Convert Date to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def generate_calendar_image(report_data):
    """
    Generate a calendar image showing 30 days of lunar data
    Returns PIL Image object
    """
    # Constants
    cell_width = 150
    cell_height = 180
    header_height = 60
    title_height = 80
    padding = 20
    calendar_width = 7 * cell_width + 2 * padding
    calendar_height = title_height + header_height + 5 * cell_height + 2 * padding
    
    # Create image with white background
    img = Image.new('RGB', (calendar_width, calendar_height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts, fall back to default if not available
    try:
        title_font = ImageFont.truetype("arial.ttf", 32)
        header_font = ImageFont.truetype("arial.ttf", 20)
        day_font = ImageFont.truetype("arial.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 12)
        tiny_font = ImageFont.truetype("arial.ttf", 10)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        day_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        tiny_font = ImageFont.load_default()
    
    # Draw title
    title_text = f"30-Day Lunar Calendar"
    if len(report_data) > 0:
        start_date = report_data.iloc[0]['Date'].strftime('%B %d')
        end_date = report_data.iloc[-1]['Date'].strftime('%B %d, %Y')
        title_text = f"30-Day Lunar Calendar: {start_date} - {end_date}"
    
    # Helper function to get text width
    def get_text_width(text, font):
        try:
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), text, font=font)
                return bbox[2] - bbox[0]
            if hasattr(draw, 'textlength'):
                return int(draw.textlength(text, font=font))
            if hasattr(font, 'getbbox'):
                bbox = font.getbbox(text)
                return bbox[2] - bbox[0]
            if hasattr(font, 'getsize'):
                w, _ = font.getsize(text)
                return w
        except Exception:
            pass
        # Conservative fallback
        return max(0, len(text) * 8)

    # Helper function to get text height
    def get_text_height(text, font):
        try:
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), text, font=font)
                return bbox[3] - bbox[1]
            if hasattr(font, 'getbbox'):
                bbox = font.getbbox(text)
                return bbox[3] - bbox[1]
            if hasattr(font, 'getsize'):
                _, h = font.getsize(text)
                return h
        except Exception:
            pass
        return 14
    
    # Get text bounding box for centering
    text_width = get_text_width(title_text, title_font)
    title_x = (calendar_width - text_width) // 2
    draw.text((title_x, padding), title_text, fill='#1f3a5f', font=title_font)
    
    # Draw week headers
    week_days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    for i, day in enumerate(week_days):
        x = padding + i * cell_width
        y = title_height + padding
        draw.rectangle([x, y, x + cell_width, y + header_height], 
                      fill='#4A90E2', outline='#1f3a5f', width=2)
        # Center text
        text_width = get_text_width(day, header_font)
        text_x = x + (cell_width - text_width) // 2
        draw.text((text_x, y + 15), day, fill='white', font=header_font)
    
    # Draw calendar cells
    for idx, (_, data_row) in enumerate(report_data.iterrows()):
        day_num = idx + 1
        
        # Calculate grid position
        row_idx = (day_num - 1) // 7
        col_idx = (day_num - 1) % 7
        
        x = padding + col_idx * cell_width
        y = title_height + padding + header_height + row_idx * cell_height
        
        # Cell background color based on phase
        phase = data_row['Phase']
        if phase == 'Full Moon':
            bg_color = '#FFE4B5'
        elif phase == 'New Moon':
            bg_color = '#E6E6FA'
        elif 'Waxing' in phase:
            bg_color = '#FFF8DC'
        else:
            bg_color = '#F0F0F0'
        
        draw.rectangle([x, y, x + cell_width - 2, y + cell_height - 2], 
                      fill=bg_color, outline='#1f3a5f', width=1)
        
        # Day number
        day_str = str(day_num)
        text_width = get_text_width(day_str, day_font)
        day_x = x + (cell_width - text_width - 10)
        draw.text((day_x, y + 5), day_str, fill='#333', font=day_font)
        
        # Phase name (truncated if too long)
        phase_text = phase.replace(' ', '\n') if len(phase) > 10 else phase
        text_width = get_text_width(phase_text.split('\n')[0], small_font)
        phase_x = x + (cell_width - text_width - 10)
        draw.text((phase_x, y + 75), phase_text, fill='#555', font=small_font)
        
        # Illumination percentage
        illum_text = f"{data_row['Illumination_%']:.0f}%"
        draw.text((x + 10, y + 95), illum_text, fill='#333', font=small_font)
        
        # Rise/Set times (simplified)
        rise_time = data_row['Moon_Rise']
        set_time = data_row['Moon_Set']
        
        if rise_time not in ['All day', 'No rise', 'Down all day']:
            rise_simple = rise_time.split(' ')[0][:5]  # Get HH:MM
            draw.text((x + 10, y + 110), f"Rise: {rise_simple}", fill='#4A90E2', font=tiny_font)
        
        if set_time not in ['No set', 'Down all day', 'All day']:
            set_simple = set_time.split(' ')[0][:5]
            draw.text((x + 10, y + 125), f"Set: {set_simple}", fill='#E24A90', font=tiny_font)
        
        # Special indicators
        special_y = y + 145
        has_special = False
        
        if data_row['Supermoon']:
            draw.text((x + 10, special_y), "* Supermoon", fill='#FF6347', font=tiny_font)
            has_special = True
        
        # Only show eclipse if type is present and not 'None'
        if pd.notna(data_row['Eclipse_Type']) and data_row['Eclipse_Type'] != 'None':
            eclipse_text = f"Eclipse: {data_row['Eclipse_Type']}"
            draw.text((x + 10, special_y + 12 if has_special else special_y), 
                     eclipse_text, fill='#8B0000', font=tiny_font)
    
    return img

# Load the data
df = load_data()

# Title and header
st.title("🌙 30-Day Lunar Report")
st.markdown("### Visualizing Monthly Moon Phases from Annual Data")

# Sidebar for date selection
st.sidebar.header("📅 Date Selection")
st.sidebar.markdown("Select a start date for your 30-day report:")

# Get date range from data
min_date = df['Date'].min()
max_date = df['Date'].max() - pd.Timedelta(days=30)

# Date picker
selected_date = st.sidebar.date_input(
    "Start Date:",
    value=min_date.date(),
    min_value=min_date.date(),
    max_value=max_date.date()
)

# Filter data for the selected 30-day period
report_data = df[df['Date'] >= pd.Timestamp(selected_date)]
report_data = report_data.head(30).copy()

# Main metrics
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Find Full Moons
    full_moons = report_data[report_data['Phase'] == 'Full Moon']
    st.metric("Full Moons", len(full_moons))
    
with col2:
    # Find New Moons
    new_moons = report_data[report_data['Phase'] == 'New Moon']
    st.metric("New Moons", len(new_moons))

with col3:
    # Find Supermoons
    supermoons = report_data[report_data['Supermoon'] == True]
    st.metric("Supermoons", len(supermoons))

with col4:
    # Find Eclipses (exclude NaN and 'None')
    eclipses = report_data[pd.notna(report_data['Eclipse_Type']) & (report_data['Eclipse_Type'] != 'None')]
    st.metric("Lunar Eclipses", len(eclipses))

st.markdown("---")

# Moon Phase Visualization
st.header("📊 Moon Phase Over Time")

# Create a custom color map for moon phases
phase_colors = {
    'New Moon': '#000000',
    'Waxing Crescent': '#E6E6FA',
    'First Quarter': '#FFF8DC',
    'Waxing Gibbous': '#FFE4B5',
    'Full Moon': '#FFFFFF',
    'Waning Gibbous': '#FFE4B5',
    'Last Quarter': '#FFF8DC',
    'Waning Crescent': '#E6E6FA'
}

# Create visualization tabs
tab1, tab2, tab3 = st.tabs(["Illumination Chart", "Phase Timeline", "Rise & Set Times"])

with tab1:
    # Illumination percentage over time
    fig = px.area(
        report_data, 
        x='Date', 
        y='Illumination_%',
        title='Moon Illumination Percentage Over 30 Days',
        labels={'Illumination_%': 'Illumination (%)', 'Date': 'Date'}
    )
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="Illumination (%)",
        hovermode='x unified'
    )
    fig.update_traces(
        fill='tonexty',
        fillcolor='rgba(200, 200, 255, 0.6)',
        line_color='#4A90E2'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Phase timeline visualization
    report_data['Phase_Num'] = report_data['Phase'].map({
        'New Moon': 0,
        'Waxing Crescent': 1,
        'First Quarter': 2,
        'Waxing Gibbous': 3,
        'Full Moon': 4,
        'Waning Gibbous': 5,
        'Last Quarter': 6,
        'Waning Crescent': 7
    })
    
    fig = px.scatter(
        report_data,
        x='Date',
        y='Phase_Num',
        color='Phase',
        size='Illumination_%',
        title='Moon Phase Timeline',
        labels={'Phase_Num': 'Phase', 'Date': 'Date'},
        hover_data=['Phase', 'Illumination_%']
    )
    fig.update_yaxes(
        tickmode='array',
        tickvals=[0, 1, 2, 3, 4, 5, 6, 7],
        ticktext=['New', 'Waxing\nCrescent', 'First\nQuarter', 'Waxing\nGibbous', 
                 'Full', 'Waning\nGibbous', 'Last\nQuarter', 'Waning\nCrescent']
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Rise and Set times
    # Clean the data for visualization
    viz_data = report_data.copy()
    
    # Filter out special cases
    viz_data = viz_data[
        (viz_data['Moon_Rise'] != 'All day') & 
        (viz_data['Moon_Rise'] != 'No rise') &
        (viz_data['Moon_Set'] != 'Down all day') &
        (viz_data['Moon_Set'] != 'No set')
    ]
    
    # Convert time strings to datetime for plotting
    def parse_time_to_hours(time_str):
        try:
            time_only = time_str.split(' ')[0]  # Get 'HH:MM:SS'
            hours, minutes, seconds = map(int, time_only.split(':'))
            return hours + minutes/60 + seconds/3600
        except:
            return None
    
    viz_data['Rise_Hour'] = viz_data['Moon_Rise'].apply(parse_time_to_hours)
    viz_data['Set_Hour'] = viz_data['Moon_Set'].apply(parse_time_to_hours)
    
    # Create line plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=viz_data['Date'],
        y=viz_data['Rise_Hour'],
        mode='lines+markers',
        name='Moon Rise',
        line=dict(color='#4A90E2', width=2),
        marker=dict(size=5)
    ))
    
    fig.add_trace(go.Scatter(
        x=viz_data['Date'],
        y=viz_data['Set_Hour'],
        mode='lines+markers',
        name='Moon Set',
        line=dict(color='#E24A90', width=2),
        marker=dict(size=5)
    ))
    
    fig.update_layout(
        title='Moon Rise and Set Times (UTC)',
        xaxis_title='Date',
        yaxis_title='Time (Hours)',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Visual Calendar Image Section
st.header("📅 Visual Calendar")

# Generate the calendar image
calendar_img = generate_calendar_image(report_data)

# Display the image
st.image(calendar_img, use_container_width=False)

# Download button
img_buffer = io.BytesIO()
calendar_img.save(img_buffer, format='PNG')
img_buffer.seek(0)

start_date_str = report_data.iloc[0]['Date'].strftime('%Y-%m-%d')
end_date_str = report_data.iloc[-1]['Date'].strftime('%Y-%m-%d')
filename = f'lunar_calendar_{start_date_str}_to_{end_date_str}.png'

st.download_button(
    label="⬇️ Download Calendar Image",
    data=img_buffer,
    file_name=filename,
    mime="image/png",
    use_container_width=True
)

st.markdown("---")

# Special Events Section
st.header("🌑 Special Events")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔴 Eclipses")
    # Exclude NaN and 'None' eclipse types
    eclipse_data = report_data[pd.notna(report_data['Eclipse_Type']) & (report_data['Eclipse_Type'] != 'None')]
    
    if len(eclipse_data) > 0:
        for idx, row in eclipse_data.iterrows():
            with st.expander(f"{row['Date'].strftime('%B %d, %Y')} - {row['Eclipse_Type']} Eclipse"):
                if pd.notna(row.get('Eclipse_Depth_%')):
                    st.write(f"**Depth:** {row['Eclipse_Depth_%']}%")
                if 'Eclipse_Time' in row and pd.notna(row['Eclipse_Time']) and row['Eclipse_Time'] != 'None':
                    st.write(f"**Time:** {row['Eclipse_Time']}")
    else:
        st.info("No lunar eclipses during this period.")

with col2:
    st.subheader("✨ Supermoons")
    supermoon_data = report_data[report_data['Supermoon'] == True]
    
    if len(supermoon_data) > 0:
        for idx, row in supermoon_data.iterrows():
            st.write(f"**{row['Date'].strftime('%B %d, %Y')}**")
            st.write(f"Illumination: {row['Illumination_%']}%")
            st.markdown("---")
    else:
        st.info("No supermoons during this period.")

st.markdown("---")

# Footer
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    <p>🌙 Lunar data generated from astronomical calculations | Project 2 - Astron 1221</p>
    </div>
    """,
    unsafe_allow_html=True
)

