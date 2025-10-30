import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

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
    # Find Eclipses
    eclipses = report_data[report_data['Eclipse_Type'] != 'None']
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

# Special Events Section
st.header("🌑 Special Events")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔴 Eclipses")
    eclipse_data = report_data[report_data['Eclipse_Type'] != 'None']
    
    if len(eclipse_data) > 0:
        for idx, row in eclipse_data.iterrows():
            with st.expander(f"{row['Date'].strftime('%B %d, %Y')} - {row['Eclipse_Type']} Eclipse"):
                st.write(f"**Depth:** {row['Eclipse_Depth_%']}%")
                if row['Eclipse_Time'] != 'None':
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

# Detailed Calendar View
st.header("📅 30-Day Calendar View")

# Create a formatted table
display_data = report_data[['Date', 'Phase', 'Illumination_%', 'Moon_Rise', 'Moon_Set']].copy()
display_data['Date'] = display_data['Date'].dt.strftime('%Y-%m-%d')

# Add emojis to phases
phase_emojis = {
    'New Moon': '🌑',
    'Waxing Crescent': '🌒',
    'First Quarter': '🌓',
    'Waxing Gibbous': '🌔',
    'Full Moon': '🌕',
    'Waning Gibbous': '🌖',
    'Last Quarter': '🌗',
    'Waning Crescent': '🌘'
}
display_data['Phase'] = display_data['Phase'].apply(
    lambda x: f"{phase_emojis.get(x, '🌙')} {x}"
)

# Display the table
st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# Summary Statistics
st.header("📈 Summary Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Phase Distribution")
    phase_counts = report_data['Phase'].value_counts()
    fig = px.pie(
        values=phase_counts.values,
        names=phase_counts.index,
        title='Days per Phase'
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Illumination Stats")
    avg_illum = report_data['Illumination_%'].mean()
    max_illum = report_data['Illumination_%'].max()
    min_illum = report_data['Illumination_%'].min()
    
    st.metric("Average Illumination", f"{avg_illum:.1f}%")
    st.metric("Maximum Illumination", f"{max_illum:.1f}%")
    st.metric("Minimum Illumination", f"{min_illum:.1f}%")

with col3:
    st.subheader("Quick Facts")
    st.info(f"""
    **Period:** {report_data['Date'].min().strftime('%b %d')} - {report_data['Date'].max().strftime('%b %d, %Y')}
    
    **Days with Moon:** {len(report_data[report_data['Up_All_Day'] == True])} days visible all day
    
    **Days without Moon:** {len(report_data[report_data['Down_All_Day'] == True])} days not visible
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    <p>🌙 Lunar data generated from astronomical calculations | Project 2 - Astron 1221</p>
    </div>
    """,
    unsafe_allow_html=True
)

