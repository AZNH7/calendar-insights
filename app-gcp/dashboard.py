#!/usr/bin/env python3
"""
Enhanced Calendar Insights Dashboard
Connects directly to Cloud SQL PostgreSQL database with advanced filtering and attendee analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import logging
import numpy as np

from database import get_meetings_data, get_user_data, init_database, check_db_health, get_filter_options, get_summary_stats

# Configure page
st.set_page_config(
    page_title="Calendar Insights Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_meetings_data(start_date=None, end_date=None, department=None, user_email=None, limit=10000):
    """Load meetings data from Cloud SQL PostgreSQL database with filtering and limits"""
    try:
        df = get_meetings_data(start_date, end_date, department, user_email, limit)
        logger.info(f"Loaded {len(df)} meetings from Cloud SQL database")
        return df
        
    except Exception as e:
        logger.error(f"Error loading data from Cloud SQL: {e}")
        st.error(f"Error connecting to Cloud SQL database: {e}")
        return pd.DataFrame()

def create_sidebar_filters():
    """Create optimized sidebar filters"""
    st.sidebar.header("🔍 Filters")
    
    filters = {}
    
    # Load filter options from cache
    with st.spinner("Loading filter options..."):
        departments, users = get_filter_options()
    
    # Date range filter - default to last 30 days
    st.sidebar.subheader("📅 Date Range")
    today = datetime.now().date()
    default_start = today - timedelta(days=30)
    
    filters['start_date'] = st.sidebar.date_input(
        "Start Date",
        value=default_start,
        max_value=today
    )
    
    filters['end_date'] = st.sidebar.date_input(
        "End Date",
        value=today,
        max_value=today
    )
    
    # Department filter
    if departments:
        dept_options = ['All'] + departments[:50]  # Limit to 50 departments
        filters['department'] = st.sidebar.selectbox(
            "🏢 Department",
            dept_options
        )
    
    # User filter with search
    if users:
        st.sidebar.subheader("👤 User Filter")
        user_search = st.sidebar.text_input("Search user email:")
        
        if user_search:
            filtered_users = [u for u in users if user_search.lower() in u.lower()][:20]
            if filtered_users:
                filters['user_email'] = st.sidebar.selectbox(
                    "Select User",
                    ['All'] + filtered_users
                )
            else:
                st.sidebar.warning("No users found matching search")
                filters['user_email'] = 'All'
        else:
            filters['user_email'] = 'All'
    
    # Data limit
    st.sidebar.subheader("📊 Data Limit")
    filters['limit'] = st.sidebar.selectbox(
        "Max records to load",
        [1000, 5000, 10000, 25000, 50000],
        index=2  # Default to 10,000
    )
    
    # Meeting type filters
    st.sidebar.subheader("📊 Meeting Type")
    filters['one_on_one_only'] = st.sidebar.checkbox("1-on-1 meetings only")
    
    return filters

def apply_filters(df, filters):
    """Apply filters to the dataframe"""
    if df.empty:
        return df
    
    filtered_df = df.copy()
    
    # Date range filter
    if 'start_date' in filters and filters['start_date']:
        filtered_df = filtered_df[filtered_df['start'].dt.date >= filters['start_date']]
    
    if 'end_date' in filters and filters['end_date']:
        filtered_df = filtered_df[filtered_df['start'].dt.date <= filters['end_date']]
    
    # Department filter
    if filters.get('department') and filters['department'] != 'All':
        filtered_df = filtered_df[filtered_df['department'] == filters['department']]
    
    # User filter
    if filters.get('user_email') and filters['user_email'] != 'All':
        filtered_df = filtered_df[filtered_df['user_email'] == filters['user_email']]
    
    # 1-on-1 meetings filter
    if filters.get('one_on_one_only'):
        filtered_df = filtered_df[filtered_df['is_one_on_one'] == True]
    
    return filtered_df

def display_overview_metrics(df):
    """Display enhanced key metrics"""
    if df.empty:
        st.warning("No meeting data available")
        return
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Meetings", len(df))
    
    with col2:
        total_duration = df['duration_minutes'].sum()
        hours = int(total_duration // 60)
        minutes = int(total_duration % 60)
        st.metric("Total Meeting Time", f"{hours}h {minutes}m")
    
    with col3:
        avg_attendees = df['attendees_count'].mean()
        st.metric("Avg Attendees", f"{avg_attendees:.1f}")
    
    with col4:
        avg_duration = df['duration_minutes'].mean()
        st.metric("Avg Duration", f"{avg_duration:.0f} min")
    
    with col5:
        avg_attendees = df['attendees_count'].mean()
        st.metric("Avg Attendees", f"{avg_attendees:.1f}")

def display_attendee_analysis(df):
    """Display detailed attendee analysis"""
    if df.empty:
        return
    
    st.subheader("👥 Attendee Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Response rate analysis
        if 'attendees_accepted' in df.columns and 'attendees_declined' in df.columns:
            response_data = {
                'Accepted': df['attendees_accepted'].sum(),
                'Declined': df['attendees_declined'].sum(),
                'Tentative': df['attendees_tentative'].sum() if 'attendees_tentative' in df.columns else 0,
                'No Response': df['attendees_needs_action'].sum() if 'attendees_needs_action' in df.columns else 0
            }
            
            # Only show chart if there's data
            if sum(response_data.values()) > 0:
                fig_response = px.pie(
                    values=list(response_data.values()),
                    names=list(response_data.keys()),
                    title="Meeting Response Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_response, use_container_width=True)
            else:
                st.info("No response data available")
        else:
            st.info("Attendee response data not available")
    
    with col2:
        # Meeting size distribution
        size_counts = df['meeting_size'].value_counts()
        
        fig_size = px.bar(
            x=size_counts.values,
            y=size_counts.index,
            orientation='h',
            title="Meeting Size Distribution",
            labels={'x': 'Number of Meetings', 'y': 'Meeting Size'}
        )
        st.plotly_chart(fig_size, use_container_width=True)
    
    # Attendee metrics table
    st.subheader("📊 Attendee Metrics")
    
    attendee_metrics = pd.DataFrame({
        'Metric': [
            'Total Attendees (all meetings)',
            'Average Attendees per Meeting',
            'Most Attendees in Single Meeting',
            'Average Acceptance Rate',
            'Average Decline Rate',
            'One-on-One Meetings'
        ],
        'Value': [
            f"{df['attendees_count'].sum():,}",
            f"{df['attendees_count'].mean():.1f}",
            f"{df['attendees_count'].max():,}",
            f"{(df['attendees_accepted'].sum() / df['attendees_count'].sum() * 100):.1f}%" if df['attendees_count'].sum() > 0 else "N/A",
            f"{(df['attendees_declined'].sum() / df['attendees_count'].sum() * 100):.1f}%" if df['attendees_count'].sum() > 0 else "N/A",
            f"{df['is_one_on_one'].sum():,} ({(df['is_one_on_one'].sum() / len(df) * 100):.1f}%)"
        ]
    })
    
    st.dataframe(attendee_metrics, use_container_width=True, hide_index=True)

def display_time_analysis(df):
    """Display enhanced time-based analysis"""
    if df.empty:
        return
    
    st.subheader("📅 Time Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Meetings by day of week
        day_counts = df['day_of_week'].value_counts()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = day_counts.reindex(day_order, fill_value=0)
        
        fig_days = px.bar(
            x=day_counts.index, 
            y=day_counts.values,
            title="Meetings by Day of Week",
            labels={'x': 'Day', 'y': 'Number of Meetings'},
            color=day_counts.values,
            color_continuous_scale='blues'
        )
        st.plotly_chart(fig_days, use_container_width=True)
    
    with col2:
        # Meetings by time of day
        time_counts = df['time_of_day'].value_counts()
        
        fig_time = px.pie(
            values=time_counts.values,
            names=time_counts.index,
            title="Meetings by Time of Day",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_time, use_container_width=True)
    
    # Monthly trend
    if len(df) > 0:
        monthly_data = df.groupby([df['start'].dt.to_period('M')]).agg({
            'duration_minutes': 'sum',
            'attendees_count': 'sum',
            'user_email': 'count'
        }).reset_index()
        monthly_data['start'] = monthly_data['start'].astype(str)
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=monthly_data['start'],
            y=monthly_data['user_email'],
            mode='lines+markers',
            name='Number of Meetings',
            line=dict(color='blue')
        ))
        
        fig_trend.update_layout(
            title="Monthly Meeting Trend",
            xaxis_title="Month",
            yaxis_title="Number of Meetings"
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)

def display_efficiency_analysis(df):
    """Display meeting efficiency analysis"""
    if df.empty:
        return
    
    st.subheader("⚡ Meeting Efficiency")
    
    # Ensure required columns exist
    if 'duration_minutes' not in df.columns:
        st.warning("Duration data not available for efficiency analysis")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Duration distribution
        fig_duration = px.histogram(
            df,
            x='duration_minutes',
            nbins=20,
            title="Meeting Duration Distribution",
            labels={'duration_minutes': 'Duration (minutes)', 'count': 'Number of Meetings'}
        )
        st.plotly_chart(fig_duration, use_container_width=True)
    
    with col2:
        # Efficiency scatter plot
        # Filter out invalid efficiency scores for better visualization
        plot_df = df[df['efficiency_score'] > 0].copy()
        
        if not plot_df.empty:
            fig_efficiency = px.scatter(
                plot_df,
                x='duration_minutes',
                y='attendees_count',
                size='efficiency_score',
                title="Meeting Efficiency (Size = Attendees per Hour)",
                labels={
                    'duration_minutes': 'Duration (minutes)',
                    'attendees_count': 'Number of Attendees'
                },
                hover_data=['summary'] if 'summary' in plot_df.columns else None
            )
            st.plotly_chart(fig_efficiency, use_container_width=True)
        else:
            st.info("No efficiency data available for visualization")

def display_detailed_meetings_table(df):
    """Display detailed meetings table with attendee information"""
    if df.empty:
        return
    
    st.subheader("📋 Detailed Meetings")
    
    # Prepare detailed data
    detailed_df = df.copy()
    
    # Select and rename columns for display
    display_columns = {
        'summary': 'Meeting Title',
        'start': 'Start Time',
        'duration_minutes': 'Duration (min)',
        'attendees_count': 'Total Attendees',
        'attendees_accepted': 'Accepted',
        'attendees_declined': 'Declined',
        'attendees_tentative': 'Tentative',
        'user_email': 'Organizer',
        'department': 'Department',
        'meeting_size': 'Size Category'
    }
    
    # Filter to available columns
    available_columns = {k: v for k, v in display_columns.items() if k in detailed_df.columns}
    
    display_df = detailed_df[list(available_columns.keys())].copy()
    display_df = display_df.rename(columns=available_columns)
    
    # Format datetime
    if 'Start Time' in display_df.columns:
        display_df['Start Time'] = display_df['Start Time'].dt.strftime('%Y-%m-%d %H:%M')
    
    # Sort by start time (most recent first)
    display_df = display_df.sort_values('Start Time', ascending=False)
    
    # Display with pagination
    st.dataframe(
        display_df.head(50),  # Show first 50 rows
        use_container_width=True,
        hide_index=True
    )
    
    if len(display_df) > 50:
        st.info(f"Showing first 50 of {len(display_df)} meetings. Use filters to narrow down results.")

def display_attendee_insights(df):
    """Display insights about meeting attendees"""
    if df.empty:
        return
    
    st.subheader("🎯 Attendee Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Most active organizers
        if 'user_email' in df.columns:
            organizer_counts = df['user_email'].value_counts().head(10)
            st.write("**Top Meeting Organizers**")
            for email, count in organizer_counts.items():
                st.write(f"• {email}: {count} meetings")
    
    with col2:
        # Department participation
        if 'department' in df.columns and df['department'].notna().any():
            dept_counts = df['department'].value_counts().head(10)
            st.write("**Most Active Departments**")
            for dept, count in dept_counts.items():
                st.write(f"• {dept}: {count} meetings")
    
    with col3:
        # Meeting patterns
        avg_duration_by_size = df.groupby('meeting_size')['duration_minutes'].mean().round(1)
        st.write("**Avg Duration by Size**")
        for size, duration in avg_duration_by_size.items():
            st.write(f"• {size}: {duration}m")

def display_quick_stats():
    """Display quick stats from cached summary"""
    st.subheader("📊 Quick Overview (Last 30 Days)")
    
    with st.spinner("Loading statistics..."):
        stats = get_summary_stats()
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Meetings", f"{stats.get('total_meetings', 0):,}")
        
        with col2:
            st.metric("Active Users", f"{stats.get('total_users', 0):,}")
        
        with col3:
            avg_duration = stats.get('avg_duration', 0)
            st.metric("Avg Duration", f"{avg_duration:.0f} min")
        
        with col4:
            avg_attendees = stats.get('avg_attendees', 0)
            st.metric("Avg Attendees", f"{avg_attendees:.1f}")
    else:
        st.warning("Unable to load quick statistics")

def main():
    """Main dashboard function with performance optimizations"""
    st.title("📊 Calendar Insights Dashboard")
    
    # Add AI Chat button in the header
    col1, col2, col3 = st.columns([3, 1, 1])
    with col2:
        if st.button("🤖 AI Chat Assistant", use_container_width=True, help="Get AI-powered insights about your meeting data"):
            st.switch_page("pages/ai_chat.py")
    with col3:
        if st.button("📊 Dashboard", use_container_width=True, help="Return to main dashboard"):
            st.switch_page("dashboard.py")
    
    st.markdown("---")
    
    # Quick stats first (cached and fast)
    display_quick_stats()
    st.markdown("---")
    
    # Create sidebar filters (optimized)
    filters = create_sidebar_filters()
    
    # Build parameters for data loading
    start_date = filters.get('start_date')
    end_date = filters.get('end_date')
    department = filters.get('department') if filters.get('department') != 'All' else None
    user_email = filters.get('user_email') if filters.get('user_email') != 'All' else None
    limit = filters.get('limit', 10000)
    
    # Load data with filters
    with st.spinner(f"Loading up to {limit:,} meetings..."):
        df = load_meetings_data(start_date, end_date, department, user_email, limit)
    
    if df.empty:
        st.error("No meeting data found. Please check your database connection or adjust filters.")
        return
    
    # Apply additional filters
    df = apply_filters(df, filters)
    
    # Display data info
    if not df.empty:
        st.success(f"✅ Showing {len(df):,} meetings")
        if len(df) >= limit:
            st.warning(f"⚠️ Showing maximum limit of {limit:,} records. Use filters to see different data.")
        
        date_range = f"{df['start'].min().date()} to {df['start'].max().date()}"
        st.info(f"📅 Date range: {date_range}")
    else:
        st.warning("No meetings found with the current filters. Try adjusting your filter criteria.")
        return
    
    # Performance warning for large datasets
    if len(df) > 25000:
        st.warning("⚠️ Large dataset loaded. Some visualizations may be slow. Consider using more specific filters.")
    
    # Display analysis sections
    display_overview_metrics(df)
    st.markdown("---")
    
    display_attendee_analysis(df)
    st.markdown("---")
    
    display_time_analysis(df)
    st.markdown("---")
    
    display_efficiency_analysis(df)
    st.markdown("---")
    
    display_attendee_insights(df)
    st.markdown("---")
    
    # Limit detailed table for performance
    if len(df) <= 1000:
        display_detailed_meetings_table(df)
    else:
        st.subheader("📋 Detailed Meetings")
        st.info(f"Too many meetings ({len(df):,}) to display detailed table. Use filters to reduce the dataset to 1,000 or fewer meetings.")
        
        if st.button("Show Sample (First 100 rows)"):
            display_detailed_meetings_table(df.head(100))
    
    # Export functionality
    if st.button("📥 Export Filtered Data to CSV"):
        if len(df) <= 50000:
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"calendar_insights_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        else:
            st.error("Dataset too large for export. Please use filters to reduce to 50,000 or fewer records.")
    
    # Debug info
    with st.expander("🔧 Debug Information"):
        st.write(f"Total records loaded: {len(df):,}")
        st.write(f"Data limit used: {limit:,}")
        if not df.empty:
            st.write(f"Columns: {list(df.columns)}")
            st.write("Applied filters:", filters)
            st.write("Memory usage:", f"{df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

if __name__ == "__main__":
    main() 