import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import time
import altair as alt
import logging
import json
import sqlite3

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# DB config
DB_HOST = os.getenv('DB_HOST', 'meeting-report-cluster.cluster-c9amyi24guc0.us-east-1.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'meetings')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# retry settings
DB_MAX_RETRIES = 10
DB_RETRY_DELAY = 10

# page config at top
st.set_page_config(page_title="Meeting Analytics", layout="wide")

class DatabaseConnection:
    def __init__(self):
        self.db_path = '/data/sqlite/meetings.db'
        self.conn = None
        self.cursor = None

    def __enter__(self):
        try:
            # check directory
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return self
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            self.conn.close()

@st.cache_resource
def get_db_engine():
    max_retries = DB_MAX_RETRIES
    retry_delay = DB_RETRY_DELAY
    
    for attempt in range(max_retries):
        try:
            connection_string = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
            logger.info(f"Attempting to connect to database at {DB_HOST}:{DB_PORT}/{DB_NAME}")
            engine = create_engine(connection_string)
            # test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to database")
            return engine
        except Exception as e:
            logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All database connection attempts failed")
                st.error("Unable to connect to the database. Please check your connection settings.")
                raise

@st.cache_resource
def load_user_data():
    try:
        user_file = '/app/data/users.json'
        logger.info(f"Attempting to load user data from: {user_file}")
        
        # check if file exists
        if not os.path.exists(user_file):
            logger.warning(f"User data file not found at {user_file}")
            # another path
            user_file = 'app/data/users.json'
            logger.info(f"Trying alternate path: {user_file}")
            if not os.path.exists(user_file):
                logger.warning(f"User data file not found at alternate path either")
                logger.info("Proceeding without user data")
                return {}
            
        with open(user_file, 'r') as f:
            users = json.load(f)
            logger.info(f"Successfully loaded JSON data with {len(users)} users")
            
            # Debug: print first user data
            if users:
                logger.info(f"First user data sample: {json.dumps(users[0], indent=2)}")
            
        # dictionary mapping email to user
        user_dict = {}
        manager_count = 0
        for user in users:
            email = user.get('email')
                
            if email:
                user_dict[email] = {
                    'department': user.get('department', 'N/A'),
                    'title': user.get('title', 'N/A'),
                    'full_name': user.get('full_name', 'N/A')
                }
        
        logger.info(f"Successfully processed {len(user_dict)} users")
        logger.info(f"Found {manager_count} managers in the data")
        
        return user_dict
    except Exception as e:
        logger.error(f"Error loading user data: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        logger.info("Proceeding without user data")
        return {}

def auto_refresh():
    time.sleep(300)  # 5 minutes
    st.rerun()

def add_meeting_categories(df):
    try:
        # meeting size categories
        df['meeting_size_category'] = pd.cut(
            df['attendees_accepted'],
            bins=[-float('inf'), 2, 7, float('inf')],
            labels=['1:1', '3-7', '8+']
        )
            
        return df
    except Exception as e:
        logger.error(f"Error adding meeting categories: {str(e)}")
        return df

@st.cache_data(ttl=300)  # cache expires after 5 minutes
def load_meetings_data():
    try:
        with DatabaseConnection() as db:
            query = """
                SELECT
                    id,
                    user_email,
                    department,
                    division,
                    subdepartment,
                    user_is_manager,
                    start_time,
                    end_time,
                    duration_minutes,
                    attendees_accepted,
                    attendees_accepted_emails,
                    attendees_tentative,
                    attendees_declined,
                    attendees_emails,
                    attendees_needs_action,
                    summary,
                    year
                FROM meetings
                ORDER BY start_time DESC
            """
            df = pd.read_sql_query(query, db.conn)
            
            # convert timestamp columns
            df['start'] = pd.to_datetime(df['start_time'])
            df['end'] = pd.to_datetime(df['end_time'])

            # duration_minutes is numeric
            df['duration_minutes'] = pd.to_numeric(df['duration_minutes'], errors='coerce')
            
            # meeting categories
            df = add_meeting_categories(df)
            
            # Debug log the columns
            logger.info(f"Columns in dataframe: {df.columns.tolist()}")
            logger.info(f"Sample of duration_minutes: {df['duration_minutes'].head()}")
            
            return df
    except Exception as e:
        logger.error(f"Error loading meetings data: {str(e)}")
        return pd.DataFrame()

def filter_dataframe(df, date_range, selected_departments, show_manager_only):
    try:
        # check required columns exist
        required_columns = ['start', 'department', 'is_manager', 'duration_minutes']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return pd.DataFrame()
        
        # date_range is a tuple or list with two elements, need to improve validation
        if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
            logger.error(f"Invalid date range format: {date_range}")
            return pd.DataFrame()
            
        # date and department filter mask
        mask = (
            (df['start'].dt.date >= date_range[0]) &
            (df['start'].dt.date <= date_range[1])
        )
        
        # department filter if departments are selected
        if selected_departments:
            mask = mask & (df['department'].isin(selected_departments))
        
        # initial filter
        filtered_df = df[mask].copy()
            
        # check all required columns are present in filtered dataframe
        for col in required_columns:
            if col not in filtered_df.columns:
                logger.error(f"Column {col} missing after filtering")
                return pd.DataFrame()
                
        return filtered_df
        
    except Exception as e:
        logger.error(f"Error filtering dataframe: {str(e)}")
        return pd.DataFrame()

def get_meeting_stats(df):
    try:
        if df.empty:
            return {}
            
        # date range
        min_date = df['start'].min().date()
        max_date = df['start'].max().date()
        
        # daily meeting counts
        daily_meetings = df.groupby(df['start'].dt.date).size().reset_index()
        daily_meetings.columns = ['date', 'count']
        
        # hour distribution
        hour_dist = df['start'].dt.hour.value_counts().sort_index()
        
        # day of week distribution
        day_map = {
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
            6: 'Sunday'
        }
        df['day_of_week'] = df['start'].dt.dayofweek.map(day_map)
        
        return {
            'min_date': min_date,
            'max_date': max_date,
            'daily_meetings': daily_meetings,
            'hour_dist': hour_dist,
            'day_dist': df['day_of_week'].value_counts()
        }
    except Exception as e:
        logger.error(f"Error calculating meeting stats: {str(e)}")
        raise

def get_user_stats(df):
    try:
        if df.empty:
            return {}
            
        # date range
        min_date = df['start'].min().date()
        max_date = df['start'].max().date()
        
        # user metrics
        user_stats = df.groupby('user_email').agg({
            'duration_minutes': ['count', 'sum'],
            'attendees_accepted': 'mean'
        }).round(2)
        
        user_stats.columns = ['meeting_count', 'total_minutes', 'avg_attendees']
        user_stats = user_stats.reset_index()
        
        return {
            'min_date': min_date,
            'max_date': max_date,
            'user_stats': user_stats
        }
    except Exception as e:
        logger.error(f"Error calculating user stats: {str(e)}")
        raise

def get_meeting_details(df):
    try:
        if df.empty:
            return pd.DataFrame()
            
        # filter and format columns for display
        display_df = df[[
            'user_email',
            'department',
            'division',
            'subdepartment',
            'start',
            'end',
            'duration_minutes',
            'attendees_accepted',
            'summary'
        ]].copy()
        
        # column to display
        st.dataframe(
            display_df,
            column_config={
                "start": st.column_config.DatetimeColumn(
                    "Start Time",
                    format="MM/DD/YYYY HH:mm",
                    help="Meeting start time"
                ),
                "end": st.column_config.DatetimeColumn(
                    "End Time",
                    format="MM/DD/YYYY HH:mm",
                    help="Meeting end time"
                )
            }
        )
        
        return display_df
    except Exception as e:
        logger.error(f"Error getting meeting details: {str(e)}")
        raise

def get_department_stats():
    try:
        with DatabaseConnection() as db:
            query = """
                SELECT
                    d.department,
                    COUNT(DISTINCT m.user_email) as total_users,
                    COUNT(DISTINCT DATE(m.start)) as days_with_meetings,
                    COUNT(*) as total_meetings,
                    AVG(m.duration_minutes) as avg_duration,
                    AVG(m.attendees_accepted) as avg_attendees
                FROM meetings m
                JOIN departments d ON m.department = d.department
                WHERE m.start >= :start_date
                AND m.start <= :end_date
                GROUP BY d.department
                ORDER BY total_meetings DESC
            """
            
            params = {
                'start_date': datetime.now() - timedelta(days=30),
                'end_date': datetime.now()
            }
            
            db.cursor.execute(query, params)
            columns = [desc[0] for desc in db.cursor.description]
            data = db.cursor.fetchall()
            return pd.DataFrame(data, columns=columns)
    except Exception as e:
        logger.error(f"Error getting department stats: {str(e)}")
        raise

def process_department_metrics(dept_data):
    total_meetings = len(dept_data)
    unique_users = dept_data['user_email'].nunique()
    total_minutes = dept_data['duration_minutes'].sum()
    
    # no 0 division
    avg_weekly_hours = 0 if unique_users == 0 else round(total_minutes / (unique_users * 52 * 60), 1)
    
    meeting_sizes = {
        '1:1': (dept_data['attendees_accepted'] == 2).sum(),
        '3-7': ((dept_data['attendees_accepted'] >= 3) & 
                (dept_data['attendees_accepted'] <= 7)).sum(),
        '8+': (dept_data['attendees_accepted'] >= 8).sum()
    }
    
    return {
        'department': dept_data['department'].iloc[0],
        'total_meetings': total_meetings,
        'avg_weekly_hours': avg_weekly_hours,
        'meeting_sizes': meeting_sizes
    }

@st.cache_data(ttl=3600)
def calculate_department_metrics(df):
    if df is None or df.empty:
        return None
        
    metrics = []
    for dept in df['department'].unique():
        dept_df = df[df['department'] == dept]
        
        # metrics
        total_meetings = len(dept_df)
        total_hours = dept_df['duration_minutes'].sum() / 60
        avg_weekly_hours = total_hours / 52  # Assuming 52 weeks
        
        # meetungs size
        size_dist = dept_df['meeting_size_category'].value_counts(normalize=True) * 100
        one_on_one_pct = size_dist.get('1:1', 0)
        small_group_pct = size_dist.get('3-7', 0)
        large_group_pct = size_dist.get('8+', 0)
        
        # unique participants
        unique_participants = len(dept_df['user_email'].unique())
        
        metrics.append({
            'Department': dept,
            'Total Meetings': total_meetings,
            'Average Weekly Hours': round(avg_weekly_hours, 1),
            '1:1 Meetings %': round(one_on_one_pct, 1),
            '3-7 People %': round(small_group_pct, 1),
            '8+ People %': round(large_group_pct, 1),
            'Unique Participants': unique_participants,
            'Total Hours': round(total_hours, 1)
        })
    
    return pd.DataFrame(metrics)

@st.cache_data
def prepare_weekly_hours(filtered_data):
    time.sleep(1) 
    
    weekly_data = filtered_data.groupby(['week', 'department']).agg({
        'user_email': 'nunique',
        'duration_minutes': 'sum'
    }).reset_index()
    
    weekly_data['avg_hours_per_person'] = weekly_data['duration_minutes'] / (weekly_data['user_email'] * 60)
    
    pivot_table = weekly_data.pivot(
        index='week',
        columns='department',
        values='avg_hours_per_person'
    ).fillna(0)
    
    return pivot_table

@st.cache_data
def prepare_meeting_patterns(filtered_data):
    time.sleep(1)
    
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hours = range(24)
    
    pattern_data = pd.DataFrame(
        0,
        index=weekday_order,
        columns=[f"{int(hour):02d}:00" for hour in hours]
    )
    
    for day in weekday_order:
        day_data = filtered_data[filtered_data['weekday'].str.strip() == day]
        hour_counts = day_data.groupby('hour').size()
        for hour in hour_counts.index:
            pattern_data.at[day, f"{int(hour):02d}:00"] = hour_counts[hour]
    
    return pattern_data

def create_empty_chart():
    # single-point DataFrame
    df = pd.DataFrame({'x': [0], 'y': [0]})
    
    # chart with a text mark
    chart = alt.Chart(df).mark_text(
        text='No data available',
        fontSize=20,
        color='gray'
    ).encode(
        x=alt.X('x:Q', axis=None),
        y=alt.Y('y:Q', axis=None)
    ).properties(
        width=400,
        height=300
    )
    
    return chart

def display_chart(data, chart_type='line', title=None):
    if data is None:
        st.write(create_empty_chart())
        return

    # handle different input types
    if isinstance(data, pd.DataFrame):
        if data.empty:
            st.write(create_empty_chart())
            return
            
        # dataframe, create appropriate visualizations based on structure
        if len(data.columns) == 1:
            # Single column DataFrame - show as bar chart
            fig = px.bar(data)
        elif 'week' in data.index.names or isinstance(data.index, pd.DatetimeIndex):
            # Time series data - show as line chart
            fig = px.line(data)
        elif len(data.columns) == 2 and data.dtypes.iloc[1].kind in 'iuf':
            # Two columns with numeric second column - show as bar chart
            fig = px.bar(data)
        elif len(data.columns) <= 4:  
            st.dataframe(data, use_container_width=True)
            return
        else:
            # Default to heatmap for complex DataFrames
            fig = px.imshow(data, aspect='auto')
            
        st.plotly_chart(fig, use_container_width=True)
        return
        
    elif isinstance(data, pd.Series):
        if data.empty:
            st.write(create_empty_chart())
            return
            
        # Convert Series to DataFrame for plotting
        df = data.reset_index()
        fig = px.bar(df, x=df.columns[0], y=df.columns[1])
        st.plotly_chart(fig, use_container_width=True)
        return

    # handle Plotly figures directly
    elif isinstance(data, go.Figure):
        st.plotly_chart(data, use_container_width=True)
        return

    # handle other types or show error
    else:
        st.error(f"Unsupported data type for chart: {type(data)}")
        st.write(data)  # fallback to raw display

def display_department_metrics(metrics_df):
    if metrics_df is None or metrics_df.empty:
        st.info("No department metrics available")
        return
        
    display_df = metrics_df.copy()
    
    percentage_columns = ['1:1 Meetings %', '3-7 People %', '8+ People %', 'Manager Participation %']
    for col in percentage_columns:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%")
    
    display_df['Average Weekly Hours'] = display_df['Average Weekly Hours'].apply(lambda x: f"{x:.1f}")
    display_df['Total Hours'] = display_df['Total Hours'].apply(lambda x: f"{x:.1f}")
    
    column_order = [
        'Department',
        'Total Meetings',
        'Unique Participants',
        'Unique Managers',
        'Manager Participation %',
        'Average Weekly Hours',
        'Total Hours',
        '1:1 Meetings %',
        '3-7 People %',
        '8+ People %'
    ]
    display_df = display_df[column_order]
    
    # dashboard with formatting
    st.dataframe(
        display_df,
        column_config={
            "Department": st.column_config.TextColumn(
                "Department",
                width="medium"
            ),
            "Manager Participation %": st.column_config.TextColumn(
                "Manager Participation %",
                help="Percentage of meetings with manager participation (either as organizer or attendee)",
                width="medium"
            ),
            "Unique Managers": st.column_config.NumberColumn(
                "Unique Managers",
                help="Number of unique managers who organized meetings",
                width="small"
            )
        },
        hide_index=True
    )

def display_duration_distribution(df):
    if df is None or df.empty:
        st.info("No data available")
        return
        
    fig = px.histogram(
        df,
        x='duration_minutes',
        nbins=50,
        title='Meeting Duration Distribution'
    )
    st.plotly_chart(fig)

def display_meeting_size_distribution(df):
    if df is None or df.empty:
        st.info("No data available")
        return
        
    size_dist = df['meeting_size_category'].value_counts()
    fig = px.pie(
        values=size_dist.values,
        names=size_dist.index,
        title='Meeting Size Distribution'
    )
    st.plotly_chart(fig)

def display_day_of_week_distribution(df):
    if df is None or df.empty:
        st.info("No data available")
        return
        
    df['day_of_week'] = df['start'].dt.day_name()
    day_dist = df['day_of_week'].value_counts()
    
    # Ensure proper day order
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_dist = day_dist.reindex(days, fill_value=0)
    
    fig = px.bar(
        x=day_dist.index,
        y=day_dist.values,
        title='Meetings by Day of Week'
    )
    st.plotly_chart(fig)

def display_hour_distribution(df):
    if df is None or df.empty:
        st.info("No data available")
        return
        
    df['hour'] = df['start'].dt.hour
    hour_dist = df['hour'].value_counts().sort_index()
    
    fig = px.bar(
        x=hour_dist.index,
        y=hour_dist.values,
        title='Meetings by Hour'
    )
    fig.update_xaxes(ticktext=[f"{h:02d}:00" for h in hour_dist.index], tickvals=hour_dist.index)
    st.plotly_chart(fig)

def display_meeting_patterns():
    st.subheader("📊 Meeting Patterns by Time and Day")
    
    # Load and prepare data
    df = load_meetings_data()
    if df.empty:
        st.error("No data available")
        return
        
    try:
        df['hour'] = df['start'].dt.hour
        df['weekday'] = df['start'].dt.day_name()
        
        # pivot table for heatmap
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hour_labels = [f"{i:02d}:00" for i in range(24)]
        
        # update pivot_table
        heatmap_data = pd.pivot_table(
            df,
            values='id',
            index='weekday',
            columns='hour',
            aggfunc='count',
            fill_value=0,
            observed=True
        ).reindex(weekday_order)
        
        # rename hour labels
        heatmap_data.columns = hour_labels
        
        # use plotly for heatmap
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=hour_labels,
            y=weekday_order,
            colorscale='YlOrRd',
            hoverongaps=False,
            hovertemplate='Day: %{y}<br>Time: %{x}<br>Meetings: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Meeting Distribution by Time and Day',
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # summary statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Busiest Times")
            # top 5 busiest hours
            hourly_totals = heatmap_data.sum()
            busiest_hours = hourly_totals.nlargest(5)
            
            st.write("Top 5 Meeting Hours:")
            for hour, count in busiest_hours.items():
                st.write(f"• {hour}: {int(count)} meetings")
                
        with col2:
            st.subheader("Busiest Days")
            # busiest days
            daily_totals = heatmap_data.sum(axis=1)
            busiest_days = daily_totals.nlargest(5)
            
            st.write("Top 5 Meeting Days:")
            for day, count in busiest_days.items():
                st.write(f"• {day}: {int(count)} meetings")
        
        # detailed statistics
        st.subheader("Detailed Statistics")
        
        # average meetings per hour for each day
        avg_by_day = heatmap_data.mean(axis=1).round(1)
        
        # peak hours for each day
        peak_hours = heatmap_data.idxmax(axis=1)
        
        # summary
        summary_df = pd.DataFrame({
            'Total Meetings': heatmap_data.sum(axis=1),
            'Average Meetings per Hour': avg_by_day,
            'Peak Hour': peak_hours,
            'Peak Hour Count': [heatmap_data.loc[day, hour] for day, hour in peak_hours.items()]
        })
        
        st.dataframe(
            summary_df,
            column_config={
                "Total Meetings": st.column_config.NumberColumn(format="%d"),
                "Average Meetings per Hour": st.column_config.NumberColumn(format="%.1f"),
                "Peak Hour Count": st.column_config.NumberColumn(format="%d")
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating meeting patterns visualization: {str(e)}")
        st.error("Error creating visualization")

def display_dashboard():
    st.title("Meeting Analytics Dashboard")
    
    if st.checkbox("Enable Auto-Refresh (5 minutes)", value=True):
        st.write("Dashboard will refresh every 5 minutes")
        auto_refresh()

    df = load_meetings_data()
    if df.empty:
        st.error("No data available")
        return
        
    # last update time
    st.sidebar.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # get min/max dates
        min_date = df['start'].min().date()
        max_date = df['start'].max().date()
        
        # default to last month
        default_start = datetime.now().date() - timedelta(days=30)
        default_end = datetime.now().date()
        
        # be sure the default dates are within the available data range
        default_start = max(default_start, min_date)
        default_end = min(default_end, max_date)
        
        # sidebar filters
        st.sidebar.header("Filters")
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(default_start, default_end),
            min_value=min_date,
            max_value=max_date
        )
        
        # dept filter
        departments = sorted(df['department'].unique().tolist())
        selected_departments = st.sidebar.multiselect(
            "Select Departments",
            departments,
            default=departments[:1]
        )
        
        # Filter the dataframe
        filtered_df = filter_dataframe(df, date_range, selected_departments)
        
        if filtered_df.empty:
            st.warning("No data available for the selected filters")
            return
            
        # high-level metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_meetings = len(filtered_df)
            st.metric("Total Meetings", f"{total_meetings:,}")
            
        with col2:
            unique_participants = filtered_df['user_email'].nunique()
            st.metric("Unique Participants", f"{unique_participants:,}")
            
        with col3:
            total_hours = filtered_df['duration_minutes'].sum() / 60
            st.metric("Total Hours", f"{total_hours:,.1f}")
            
        with col4:
            avg_duration = filtered_df['duration_minutes'].mean()
            st.metric("Avg Duration (min)", f"{avg_duration:.1f}")
        
        # meetings Patterns Section
        st.markdown("---")
        st.subheader("📊 Meeting Patterns")
        
        tab1, tab2, tab3 = st.tabs(["Time Patterns", "Meeting Sizes", "Department Analysis"])
        
        with tab1:
            display_meeting_patterns()
            
        with tab2:
            # size distribution
            size_dist = filtered_df['meeting_size_category'].value_counts()
            fig = px.pie(
                values=size_dist.values,
                names=size_dist.index,
                title="Meeting Size Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # avg duration by meeting size
            avg_duration = filtered_df.groupby('meeting_size_category')['duration_minutes'].mean()
            fig = px.bar(
                x=avg_duration.index,
                y=avg_duration.values,
                title="Average Duration by Meeting Size",
                labels={'x': 'Meeting Size', 'y': 'Average Duration (minutes)'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with tab3:
            if len(selected_departments) > 0:
                # dept meeting counts
                dept_counts = filtered_df['department'].value_counts()
                fig = px.bar(
                    x=dept_counts.index,
                    y=dept_counts.values,
                    title="Meetings by Department",
                    labels={'x': 'Department', 'y': 'Number of Meetings'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # avg meeting duration by department
                dept_duration = filtered_df.groupby('department')['duration_minutes'].mean()
                fig = px.bar(
                    x=dept_duration.index,
                    y=dept_duration.values,
                    title="Average Meeting Duration by Department",
                    labels={'x': 'Department', 'y': 'Average Duration (minutes)'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Meeting Table
        st.markdown("---")
        st.subheader("📋 Detailed Meeting Data")
        
        # most recent meetings
        recent_meetings = filtered_df.sort_values('start', ascending=False).head(10)
        st.dataframe(
            recent_meetings[['start', 'summary', 'department', 'duration_minutes', 'meeting_size_category']],
            column_config={
                "start": st.column_config.DatetimeColumn("Start Time", format="MM/DD/YYYY HH:mm"),
                "summary": "Summary",
                "department": "Department",
                "duration_minutes": st.column_config.NumberColumn("Duration (min)"),
                "meeting_size_category": "Size"
            },
            hide_index=True
        )
        
    except Exception as e:
        logger.error(f"Error in dashboard display: {str(e)}")
        st.error("Error displaying dashboard")

def display_raw_data_page():
    st.title("Meeting Data - Raw View")
    
    df = load_meetings_data()
    if df is None or df.empty:
        st.error("No data available")
        return

    # sidebar filters
    st.sidebar.header("Filters")
    
    # date range filter
    min_date = df['start'].min().date()
    max_date = df['start'].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="raw_data_date_range"
    )

    # dept filter
    departments = sorted(df['department'].unique().tolist())
    selected_departments = st.sidebar.multiselect(
        "Departments",
        departments,
        default=departments,
        key="raw_data_departments"
    )

    # meetings size filter
    meeting_sizes = sorted(df['meeting_size_category'].unique().tolist())
    selected_sizes = st.sidebar.multiselect(
        "Meeting Sizes",
        meeting_sizes,
        default=meeting_sizes,
        key="raw_data_meeting_sizes"
    )

    # search function
    search_term = st.text_input("Search (email, summary, or department)", "")
    if search_term:
        search_mask = (
            filtered_df['user_email'].str.contains(search_term, case=False, na=False) |
            filtered_df['summary'].str.contains(search_term, case=False, na=False) |
            filtered_df['department'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]

    # display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Meetings", len(filtered_df))
    with col2:
        st.metric("Unique Users", filtered_df['user_email'].nunique())
    with col3:
        total_hours = filtered_df['duration_minutes'].sum() / 60
        st.metric("Total Hours", f"{total_hours:,.1f}")

    # data table with formatting
    st.dataframe(
        filtered_df,
        column_config={
            "start": st.column_config.DatetimeColumn(
                "Start Time",
                format="MM/DD/YYYY HH:mm",
                help="Meeting start time"
            ),
            "end": st.column_config.DatetimeColumn(
                "End Time",
                format="MM/DD/YYYY HH:mm",
                help="Meeting end time"
            ),
            "duration_minutes": st.column_config.NumberColumn(
                "Duration (min)",
                width="small"
            ),
            "user_email": st.column_config.TextColumn(
                "Email",
                width="medium"
            ),
            "department": st.column_config.TextColumn(
                "Department",
                width="medium"
            ),
            "meeting_size_category": st.column_config.TextColumn(
                "Size",
                width="small"
            ),
            "summary": st.column_config.TextColumn(
                "Summary",
                width="large"
            ),
            "is_manager": st.column_config.CheckboxColumn(
                "Is Manager",
                width="small",
                default=False
            )
        },
        hide_index=True,
        use_container_width=True
    )

    # export function
    if st.button("Export to CSV"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="meeting_data.csv",
            mime="text/csv"
        )

def display_dashboards_page():
    st.title("Meeting Analytics Dashboards")
    
    # Load user data for manager information
    user_dict = load_user_data()
    
    # Add tabs for different dashboard views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overall Metrics", 
        "Manager Metrics", 
        "Department Metrics",
        "Meeting Patterns"
    ])
    
    with tab1:
        display_overall_metrics()
        
    with tab2:
        display_department_metrics()
        
    with tab3:
        display_meeting_patterns()

def create_meeting_distribution_chart(df, selected_metric, show_manager_only):
    try:
        if selected_metric == 'Day of Week':
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=days_order, ordered=True)
            
            chart_data = df['day_of_week'].value_counts().reindex(days_order)
            title = 'Meeting Distribution by Day of Week'
            x_label = 'Day of Week'
            
        elif selected_metric == 'Hour of Day':
            chart_data = df['hour'].value_counts().sort_index()
            title = 'Meeting Distribution by Hour of Day'
            x_label = 'Hour'
            
        else:
            raise ValueError(f"Unknown metric: {selected_metric}")
            
        # bar chart
        fig = go.Figure(data=[
            go.Bar(x=chart_data.index, 
                  y=chart_data.values,
                  marker_color='#1f77b4')
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title='Number of Meetings',
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating meeting distribution chart: {str(e)}")
        return None

def check_database_connection():
    try:
        with DatabaseConnection() as db:
            db.cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='meetings'
            """)
            if not db.cursor.fetchone():
                logger.error("Meetings table does not exist")
                return False
                
            # check for data
            db.cursor.execute("SELECT COUNT(*) FROM meetings")
            count = db.cursor.fetchone()[0]
            logger.info(f"Found {count} meetings in database")
            
            if count == 0:
                logger.error("No meetings found in database")
                return False
                
            return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

def display_overall_metrics():
    st.header("Overall Meeting Metrics")
    
    df = load_meetings_data()
    if df.empty:
        st.error("No data available")
        return
        
    # display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Meetings", len(df))
    with col2:
        st.metric("Unique Users", df['user_email'].nunique())
    with col3:
        total_hours = df['duration_minutes'].sum() / 60
        st.metric("Total Hours", f"{total_hours:,.1f}")
    with col4:
        avg_duration = df['duration_minutes'].mean()
        st.metric("Avg Duration (min)", f"{avg_duration:.1f}")

def debug_database():
    try:
        with DatabaseConnection() as db:
            # get schema
            db.cursor.execute("PRAGMA table_info(meetings)")
            schema = db.cursor.fetchall()
            st.write("Database Schema:", schema)
            
            # row count
            db.cursor.execute("SELECT COUNT(*) FROM meetings")
            count = db.cursor.fetchone()
            st.write(f"Total rows in database: {count[0]}")
            
            # sample data
            db.cursor.execute("""
                SELECT * FROM meetings 
                WHERE user_email != '' 
                LIMIT 5
            """)
            sample = db.cursor.fetchall()
            st.write("Sample Data:", sample)
            
    except Exception as e:
        st.error(f"Debug Error: {str(e)}")

def calculate_metrics(df, group_type='All'):
    if df.empty:
        return {
            "Group": group_type,
            "Total Meetings": 0,
            "Unique Participants": 0,
            "Avg Weekly Hours": 0,
            "1:1 Meetings %": 0,
            "Manager Participation %": 0
        }
    
    total_meetings = len(df)
    unique_participants = df['user_email'].nunique()
    total_hours = df['duration_minutes'].sum() / 60
    avg_weekly_hours = total_hours / 52 if unique_participants > 0 else 0
    one_on_one_pct = (df['meeting_size_category'] == '1:1').mean() * 100
    manager_participation = (df['has_manager_attendee'].sum() / total_meetings * 100) if total_meetings > 0 else 0
    
    return {
        "Group": group_type,
        "Total Meetings": total_meetings,
        "Unique Participants": unique_participants,
        "Avg Weekly Hours": round(avg_weekly_hours, 1),
        "1:1 Meetings %": round(one_on_one_pct, 1),
        "Manager Participation %": round(manager_participation, 1)
    }

def main():
    # page navigation
    page = st.sidebar.selectbox(
        "Select Page",
        ["Dashboard", "Raw Data"],
        key="page_navigation"
    )

    if page == "Dashboard":
        if not check_database_connection():
            st.error("No data available. Please check the database connection.")
            st.code("""
            Possible issues:
            1. Database file not created
            2. No data loaded
            3. Permissions issue
            
            Check the container logs using:
            docker-compose logs app
            """)
            st.stop()
        display_dashboard()
    else:
        display_raw_data_page()

if __name__ == "__main__":
    if st.checkbox("Show Database Debug Info"):
        debug_database()
    main() 