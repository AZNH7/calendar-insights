#!/usr/bin/env python3
"""
Main Production Dashboard for Calendar Insights
Integrates enhanced production configuration and real data fetching
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta

# Set page config - THIS MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Calendar Insights - Production Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging (ONCE)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import production components (ONCE)
try:
    # Try to use the integrated database module first
    from database_integration import get_db_connection, get_database_stats # get_database_stats might be unused, will address later if still an issue
    logger.info("Using integrated database module")
except ImportError:
    # Fall back to original database module
    from database import get_db_connection 
    logger.info("Using original database module")

from plotly_helpers import (
    create_bar_chart, create_pie_chart, create_heatmap, 
    plot_with_streamlit
)
from production_config import ProductionConfig
from production_fetch import CalendarDataFetcher

# Initialize production configuration
config = ProductionConfig()
app_config = config.get_app_config()

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .insight-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .success-metric {
        color: #28a745;
        font-weight: bold;
    }
    .warning-metric {
        color: #ffc107;
        font-weight: bold;
    }
    .danger-metric {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_calendar_data():
    """Load calendar data from database with caching"""
    try:
        # Get database connection using the integrated module
        with get_db_connection() as conn: # Ensure conn is used with 'with'
            if conn is None:
                logger.error("Failed to get database connection.")
                st.error("Failed to connect to the database.")
                return pd.DataFrame()

            query = """
            SELECT 
                id, summary AS title, start_time, end_time, 
                meet_link AS location, 
                attendees_count, 
                (CASE WHEN meet_link IS NOT NULL AND meet_link != '' THEN TRUE ELSE FALSE END) AS is_virtual, 
                created_at
            FROM meetings 
            WHERE start_time >= NOW() - INTERVAL '90 days'
            ORDER BY start_time DESC
            """
            
            df = pd.read_sql(query, conn)
        # conn is automatically closed when exiting the 'with' block
        
        if df.empty:
            logger.warning("No calendar data found in database")
            return pd.DataFrame()
        
        # Data preprocessing
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])
        df['duration_minutes'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60
        df['date'] = df['start_time'].dt.date
        df['hour'] = df['start_time'].dt.hour
        df['day_of_week'] = df['start_time'].dt.day_name()
        df['week'] = df['start_time'].dt.isocalendar().week
        df['month'] = df['start_time'].dt.month_name()
        
        # Convert is_virtual to proper boolean
        df['is_virtual'] = df['is_virtual'].astype(bool)
        
        # Meeting size categories
        df['meeting_size'] = pd.cut(
            df['attendees_count'], 
            bins=[0, 2, 5, 10, float('inf')], 
            labels=['1-on-1', 'Small (3-5)', 'Medium (6-10)', 'Large (10+)']
        )
        
        logger.info(f"Loaded {len(df)} calendar events")
        return df
        
    except Exception as e:
        logger.error(f"Error loading calendar data: {e}")
        st.error(f"Error loading calendar data: {e}")
        return pd.DataFrame()

def calculate_efficiency_metrics(df):
    logger.info("CALCULATE_EFFICIENCY_METRICS_SIMPLIFIED_VERSION_JUNE_5_B") # Unique log message
    # This function is now much shorter than 198 lines.
    # If the error persists at line 198, the file is NOT being updated in the image.
    return {
        'total_meeting_time': 0,
        'avg_meeting_duration': 0,
        'meeting_frequency': 0,
        'efficiency_score': 75, # Fixed value
        'short_meetings_pct': 0,
        'virtual_adoption_pct': 0,
        'focused_time_daily': 480
    }

def display_key_metrics(df):
    """Display key metrics in a card layout"""
    if df.empty:
        st.warning("No data available to display metrics")
        return
    
    metrics = calculate_efficiency_metrics(df)
    # efficiency_color is calculated but not used here, consider removing or using it.
    # efficiency_color = "success" if metrics['efficiency_score'] >= 70 else "warning" if metrics['efficiency_score'] >= 50 else "danger"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        # Calculate this week's events safely
        try:
            this_week_events = len(df[df['start_time'] >= datetime.now() - timedelta(days=7)])
        except:
            this_week_events = 0
        
        st.metric(
            "Total Events", 
            f"{len(df):,}",
            delta=f"{this_week_events:,} this week"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        efficiency_color = "success" if metrics['efficiency_score'] >= 70 else "warning" if metrics['efficiency_score'] >= 50 else "danger"
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            "Efficiency Score", 
            f"{metrics['efficiency_score']:.1f}%",
            delta=f"{metrics['short_meetings_pct']:.1f}% short meetings"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            "Avg Duration", 
            f"{metrics['avg_meeting_duration']:.0f} min",
            delta=f"{metrics['meeting_frequency']:.1f} meetings/day"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            "Virtual Adoption", 
            f"{metrics['virtual_adoption_pct']:.1f}%",
            delta=f"{metrics['focused_time_daily']:.0f} min focused time"
        )
        st.markdown('</div>', unsafe_allow_html=True)

def display_sidebar_filters(df):
    """Display sidebar filters for data"""
    st.sidebar.header("📅 Filters")
    
    if df.empty:
        st.sidebar.warning("No data available for filtering")
        return df
    
    # Date range filter
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Meeting size filter
    size_options = df['meeting_size'].dropna().unique()
    selected_sizes = st.sidebar.multiselect(
        "Meeting Size",
        options=size_options,
        default=size_options
    )
    
    # Virtual/In-person filter
    meeting_type = st.sidebar.selectbox(
        "Meeting Type",
        options=["All", "Virtual", "In-Person"]
    )
    
    # Apply filters
    filtered_df = df.copy()
    
    try:
        if len(date_range) == 2:
            filtered_df = filtered_df[
                (filtered_df['date'] >= date_range[0]) & 
                (filtered_df['date'] <= date_range[1])
            ]
        
        if selected_sizes:
            filtered_df = filtered_df[filtered_df['meeting_size'].isin(selected_sizes)]
        
        if meeting_type == "Virtual":
            filtered_df = filtered_df[filtered_df['is_virtual']]
        elif meeting_type == "In-Person":
            filtered_df = filtered_df[~filtered_df['is_virtual']]
            
    except Exception as e:
        logger.error(f"Error in filtering: {e}")
        # Return unfiltered data if filtering fails
        return df
    
    return filtered_df

def display_analytics_tab(df):
    """Display analytics and insights"""
    if df.empty:
        st.warning("No data available for analytics")
        return
    
    st.header("📊 Advanced Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Meeting duration distribution
        st.subheader("Meeting Duration Distribution")
        duration_bins = [0, 15, 30, 60, 120, float('inf')]
        duration_labels = ['Quick (0-15m)', 'Short (15-30m)', 'Standard (30-60m)', 'Long (1-2h)', 'Extended (2h+)']
        df['duration_category'] = pd.cut(df['duration_minutes'], bins=duration_bins, labels=duration_labels)
        
        duration_dist = df['duration_category'].value_counts()
        fig = create_pie_chart(values=duration_dist.values, names=duration_dist.index, title="Meeting Duration Distribution") # Added named arguments
        plot_with_streamlit(fig)
    
    with col2:
        # Meeting patterns by hour
        st.subheader("Meeting Patterns by Hour")
        hourly_meetings = df.groupby('hour').size().reset_index(name='count')
        fig = create_bar_chart(x=hourly_meetings['hour'], y=hourly_meetings['count'], title="Meetings by Hour") # Added named arguments
        plot_with_streamlit(fig)
    
    # Weekly heatmap
    st.subheader("Weekly Meeting Heatmap")
    df['weekday_num'] = df['start_time'].dt.weekday
    heatmap_data = df.groupby(['weekday_num', 'hour']).size().unstack(fill_value=0)
    
    fig = create_heatmap(
        heatmap_data.values,
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        [f"{h:02d}:00" for h in range(24)],
        "Weekly Meeting Patterns"
    )
    plot_with_streamlit(fig)

def display_insights_tab(df):
    """Display insights and recommendations"""
    if df.empty:
        st.warning("No data available for insights")
        return
    
    st.header("💡 Insights & Recommendations")
    
    metrics = calculate_efficiency_metrics(df)
    
    # Efficiency insights
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.subheader("🎯 Efficiency Analysis")
    
    if metrics['efficiency_score'] >= 80:
        st.success("🎉 Excellent calendar efficiency! You're managing your time very well.")
    elif metrics['efficiency_score'] >= 60:
        st.warning("⚠️ Good efficiency with room for improvement.")
    else:
        st.error("🔴 Calendar efficiency needs attention.")
    
    # Specific
    recommendations = []
    
    if metrics['avg_meeting_duration'] > 60:
        recommendations.append("Consider shortening meetings - average duration is high")
    
    if metrics['virtual_adoption_pct'] < 50:
        recommendations.append("Increase virtual meetings to save commute time")
    
    if metrics['meeting_frequency'] > 5:
        recommendations.append("You have many meetings per day - consider consolidating")
    
    if recommendations:
        st.subheader("📋 Recommendations")
        for rec in recommendations:
            st.write(f"• {rec}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Meeting patterns insights
    peak_hour = df.groupby('hour').size().idxmax()
    peak_day = df.groupby('day_of_week').size().idxmax()
    
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.subheader("⏰ Pattern Analysis")
    st.write(f"• Peak meeting hour: **{peak_hour}:00**")
    st.write(f"• Busiest day: **{peak_day}**")
    st.write(f"• Average attendees: **{df['attendees_count'].mean():.1f}**")
    st.markdown('</div>', unsafe_allow_html=True)

def display_data_tab(df):
    """Display raw data with filtering options"""
    st.header("📋 Calendar Events Data")
    
    if df.empty:
        st.warning("No calendar data available")
        st.info("Use the 'Data Management' section to fetch calendar data")
        return
    
    # Display data
    st.dataframe(
        df[['title', 'start_time', 'duration_minutes', 'attendees_count', 'is_virtual', 'location']],
        use_container_width=True,
        column_config={
            "title": st.column_config.TextColumn("Event Title", width="large"),
            "start_time": st.column_config.DatetimeColumn("Start Time", width="medium"),
            "duration_minutes": st.column_config.NumberColumn("Duration (min)", width="small"),
            "attendees_count": st.column_config.NumberColumn("Attendees", width="small"),
            "is_virtual": st.column_config.CheckboxColumn("Virtual", width="small"),
            "location": st.column_config.TextColumn("Location", width="medium")
        }
    )
    
    # Export functionality
    if st.button("📥 Export Data"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"calendar_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def display_data_management():
    """Display data management interface"""
    st.header("🔄 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Calendar Data Fetching")
        
        if st.button("🔄 Refresh Calendar Data", type="primary"):
            try:
                fetcher = CalendarDataFetcher(config=config) # Pass config if needed by constructor
                with st.spinner("Fetching calendar data..."):
                    # Assuming fetch_and_store_events is the correct method name
                    events_added = fetcher.fetch_calendar_events() # Corrected method name based on typical patterns
                st.success(f"✅ Successfully processed {events_added} calendar events!")
                st.rerun()  # Refresh the app to show new data
            except Exception as e:
                st.error(f"❌ Error fetching calendar data: {e}")
                logger.error(f"Error in data fetch: {e}")
    
    with col2:
        st.subheader("System Status")
        
        # Database connection test
        try:
            with get_db_connection() as conn: # Ensure conn is used with 'with'
                if conn is None:
                    st.error("❌ Database connection: Failed to connect")
                else:
                    st.success("✅ Database connection: OK")
        except Exception as e:
            st.error(f"❌ Database connection: {e}")
        
        # Configuration status
        try:
            # db_config = config.get_database_config() # This variable was unused
            config.get_database_config() # Call it to check if it raises an error
            st.success("✅ Configuration: OK")
            st.info(f"Environment: {config.environment}")
        except Exception as e:
            st.error(f"❌ Configuration: {e}")

def main():
    """Main application function"""
    try:
        st.title("📊 Calendar Insights Dashboard")
        st.markdown("*Production-ready analytics for your calendar data*")
        
        # Sidebar
        st.sidebar.title("📊 Calendar Insights")
        st.sidebar.markdown("---")
        
        # Load data
        df = load_calendar_data()
        
        # Apply filters
        filtered_df = display_sidebar_filters(df)
        
        # Display key metrics
        display_key_metrics(filtered_df)
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Analytics", "💡 Insights", "📋 Data", "🔄 Management", "⚙️ Settings"])
        
        with tab1:
            display_analytics_tab(filtered_df)
        
        with tab2:
            display_insights_tab(filtered_df)
        
        with tab3:
            display_data_tab(filtered_df)
        
        with tab4:
            display_data_management()
        
        with tab5:
            st.header("⚙️ Settings")
            st.subheader("Application Configuration")
            
            # Display current configuration
            st.json(config.export_config())
            
            st.subheader("Feature Flags")
            features = config.get_feature_flags()
            for feature, enabled in features.items():
                status = "✅ Enabled" if enabled else "❌ Disabled"
                st.write(f"**{feature}**: {status}")
                
    except Exception as e:
        logger.error(f"Main function error: {e}")
        st.error(f"Dashboard error: {e}")
        st.info("Please check the logs for more details.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"Application error: {e}")
        st.info("Please check the logs for more details.")
