import os
import logging
import pandas as pd
import streamlit as st
from contextlib import contextmanager
import psycopg2
import time

# Import production configuration
try:
    from production_config import ProductionConfig
    USING_PROD_CONFIG = True
except ImportError:
    USING_PROD_CONFIG = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_exclusions():
    """Load email and meeting exclusions from YAML configuration"""
    try:
        import yaml
        with open('config/email_exclusions.yaml', 'r') as f:
            exclusions = yaml.safe_load(f)
            
        # Load exclusions
        individual_emails = set(exclusions.get('individual_emails', []))
        domain_patterns = exclusions.get('domain_patterns', [])
        prefix_patterns = exclusions.get('prefix_patterns', [])
        department_emails = set(exclusions.get('department_emails', []))
        meeting_keywords = set(exclusions.get('meeting_keywords', []))
        
        return {
            'individual_emails': individual_emails,
            'domain_patterns': domain_patterns,
            'prefix_patterns': prefix_patterns,
            'department_emails': department_emails,
            'meeting_keywords': meeting_keywords
        }
    except Exception as e:
        logger.error(f"Error loading exclusions: {str(e)}")
        return {}

@contextmanager
def get_db_connection(max_retries=20, retry_delay=10):
    """
    Get a PostgreSQL database connection with retry logic for Cloud SQL
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between attempts in seconds
    """
    conn = None
    retries = 0
    
    # Get Cloud SQL connection parameters from environment variables
    # All sensitive values must be provided via environment variables
    db_host = os.getenv('POSTGRES_HOST', os.getenv('DB_HOST'))
    db_port = os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))
    db_name = os.getenv('POSTGRES_DB', os.getenv('DB_NAME'))
    db_user = os.getenv('POSTGRES_USER', os.getenv('DB_USER'))
    db_password = os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD'))
    
    # Validate required environment variables
    if not db_host:
        raise ValueError("POSTGRES_HOST or DB_HOST environment variable must be set")
    if not db_name:
        raise ValueError("POSTGRES_DB or DB_NAME environment variable must be set")
    if not db_user:
        raise ValueError("POSTGRES_USER or DB_USER environment variable must be set")
    if not db_password:
        raise ValueError("POSTGRES_PASSWORD or DB_PASSWORD environment variable must be set")
    
    # For Cloud SQL socket connection (preferred in Cloud Run)
    cloud_sql_connection = os.getenv('CLOUD_SQL_CONNECTION_NAME')
    
    logger.info(f"Database connection parameters:")
    logger.info(f"  Host: {db_host}")
    logger.info(f"  Port: {db_port}")
    logger.info(f"  Database: {db_name}")
    logger.info(f"  User: {db_user}")
    if cloud_sql_connection:
        logger.info(f"  Cloud SQL Connection: {cloud_sql_connection}")
    
    while retries < max_retries:
        try:
            logger.info(f"Connecting to Cloud SQL PostgreSQL (attempt {retries+1}/{max_retries})")
            
            # Check if we're using socket connection (Cloud Run) or IP connection
            if db_host.startswith('/cloudsql/'):
                logger.info(f"Using Cloud SQL socket connection: {db_host}")
                conn = psycopg2.connect(
                    host=db_host,
                    database=db_name,
                    user=db_user,
                    password=db_password,
                    connect_timeout=30
                )
            else:
                logger.info(f"Using IP connection to {db_host}:{db_port}")
                conn = psycopg2.connect(
                    host=db_host,
                    port=db_port,
                    database=db_name,
                    user=db_user,
                    password=db_password,
                    connect_timeout=30
                )
            
            # Test the connection 
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                
            if result and result[0] == 1:
                logger.info(f"Successfully connected to Cloud SQL PostgreSQL database: {db_name}")
                break
            else:
                raise Exception("Connection test failed")
                
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                logger.error(f"Failed to connect to Cloud SQL after {max_retries} attempts: {str(e)}")
                raise
            else:
                logger.warning(f"Connection attempt {retries} failed: {str(e)}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
    
    try:
        yield conn
    finally:
        if conn:
            conn.close()

def init_database():
    """Initialize the PostgreSQL database with required tables"""
    try:
        logger.info("Initializing database schema...")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create meetings table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meetings (
                    id SERIAL PRIMARY KEY,
                    user_email TEXT NOT NULL,
                    department TEXT,
                    division TEXT,
                    subdepartment TEXT,
                    is_manager BOOLEAN DEFAULT FALSE,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    duration_minutes INTEGER,
                    attendees_count INTEGER DEFAULT 0,
                    attendees_accepted INTEGER DEFAULT 0,
                    attendees_declined INTEGER DEFAULT 0,
                    attendees_tentative INTEGER DEFAULT 0,
                    attendees_needs_action INTEGER DEFAULT 0,
                    attendees_accepted_emails TEXT,
                    summary TEXT,
                    meet_link TEXT,
                    html_link TEXT,
                    is_one_on_one BOOLEAN DEFAULT FALSE,
                    has_manager_attendee BOOLEAN DEFAULT FALSE,
                    unique_departments INTEGER DEFAULT 1,
                    departments_list TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    department TEXT,
                    division TEXT,
                    subdepartment TEXT,
                    is_manager BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_user_email ON meetings(user_email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_department ON meetings(department)')
            
            conn.commit()
            logger.info("PostgreSQL database initialization complete")
            
            # Check table status
            cursor.execute("SELECT COUNT(*) FROM meetings")
            meeting_count = cursor.fetchone()[0]
            
            logger.info(f"Database initialization complete - {meeting_count} meetings in database")
            # Note: Sample data is no longer added automatically
            # Use add_sample_data() function manually if needed for testing
            
    except Exception as e:
        logger.error(f"Error initializing PostgreSQL database: {str(e)}")
        raise

def add_sample_data(conn):
    """Add sample data to the PostgreSQL database"""
    try:
        cursor = conn.cursor()
        
        # Sample users
        sample_users = [
            ('john.doe@company.com', 'Engineering', 'Technology', 'Backend', True),
            ('jane.smith@company.com', 'Marketing', 'Sales & Marketing', 'Digital', True),
            ('bob.wilson@company.com', 'Engineering', 'Technology', 'Frontend', False),
            ('alice.brown@company.com', 'HR', 'Operations', 'Talent', False),
            ('charlie.davis@company.com', 'Sales', 'Sales & Marketing', 'Enterprise', True),
        ]
        
        cursor.executemany('''
            INSERT INTO users (email, department, division, subdepartment, is_manager)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        ''', sample_users)
        
        # Sample meetings
        from datetime import datetime, timedelta
        base_date = datetime.now() - timedelta(days=30)
        
        sample_meetings = []
        for i in range(50):
            start_time = base_date + timedelta(days=i % 30, hours=9 + (i % 8), minutes=(i * 15) % 60)
            end_time = start_time + timedelta(minutes=30 + (i % 4) * 15)
            duration = int((end_time - start_time).total_seconds() / 60)
            
            meeting = (
                sample_users[i % len(sample_users)][0],  # user_email
                sample_users[i % len(sample_users)][1],  # department
                sample_users[i % len(sample_users)][2],  # division
                sample_users[i % len(sample_users)][3],  # subdepartment
                sample_users[i % len(sample_users)][4],  # is_manager
                start_time,
                end_time,
                duration,
                2 + (i % 6),  # attendees_count
                1 + (i % 4),  # attendees_accepted
                i % 2,        # attendees_declined
                i % 3,        # attendees_tentative
                i % 2,        # attendees_needs_action
                f'participant{i}@company.com',  # attendees_accepted_emails
                f'Sample Meeting {i + 1}',     # summary
                f'https://meet.google.com/abc-def-{i:03d}',  # meet_link
                f'https://calendar.google.com/event?eid={i}',  # html_link
                (i % 5) == 0,  # is_one_on_one
                (i % 3) == 0,  # has_manager_attendee
                1 + (i % 3),   # unique_departments
                sample_users[i % len(sample_users)][1],  # departments_list
            )
            sample_meetings.append(meeting)
        
        cursor.executemany('''
            INSERT INTO meetings (
                user_email, department, division, subdepartment, is_manager,
                start_time, end_time, duration_minutes, attendees_count,
                attendees_accepted, attendees_declined, attendees_tentative,
                attendees_needs_action, attendees_accepted_emails, summary,
                meet_link, html_link, is_one_on_one, has_manager_attendee,
                unique_departments, departments_list
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', sample_meetings)
        
        conn.commit()
        logger.info(f"Added {len(sample_users)} sample users and {len(sample_meetings)} sample meetings")
        
    except Exception as e:
        logger.error(f"Error adding sample data: {str(e)}")

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_meetings_data(start_date=None, end_date=None, department=None, user_email=None, limit=10000):
    """
    Retrieve meetings data from the PostgreSQL database with optimizations
    """
    try:
        # Initialize database if needed
        init_database()
        
        with get_db_connection() as conn:
            # Build dynamic WHERE conditions
            where_conditions = ["1=1"]
            params = {}
            
            # Default to last 30 days instead of 1 year for better performance
            if not start_date and not end_date:
                where_conditions.append("start_time >= (CURRENT_DATE - INTERVAL '30 days')")
            else:
                if start_date:
                    where_conditions.append("start_time >= %(start_date)s")
                    params['start_date'] = start_date
                if end_date:
                    where_conditions.append("start_time <= %(end_date)s")
                    params['end_date'] = end_date
            
            if department:
                where_conditions.append("department = %(department)s")
                params['department'] = department
                
            if user_email:
                where_conditions.append("user_email = %(user_email)s")
                params['user_email'] = user_email
            
            # Optimized query with only essential columns
            query = f"""
            SELECT
                user_email,
                department,
                division,
                is_manager, 
                start_time as start,      
                end_time as "end",      
                duration_minutes,
                attendees_count,
                attendees_accepted,
                attendees_declined,
                attendees_tentative,
                summary,
                meet_link,
                CASE 
                    WHEN attendees_count <= 2 THEN '1-on-1'
                    WHEN attendees_count <= 5 THEN 'Small (3-5)'
                    WHEN attendees_count <= 10 THEN 'Medium (6-10)'
                    WHEN attendees_count <= 20 THEN 'Large (11-20)'
                    ELSE 'Very Large (20+)'
                END as meeting_size,
                is_one_on_one
            FROM meetings
            WHERE {' AND '.join(where_conditions)}
            ORDER BY start_time DESC
            LIMIT %(limit)s
            """
            
            params['limit'] = limit
            
            df = pd.read_sql_query(query, conn, params=params, parse_dates=['start', 'end'])
            
            if not df.empty:
                # Add essential computed columns only
                df['date'] = df['start'].dt.date
                df['hour'] = df['start'].dt.hour
                df['day_of_week'] = df['start'].dt.day_name()
                df['month'] = df['start'].dt.month_name()
                df['week'] = df['start'].dt.isocalendar().week
                df['year'] = df['start'].dt.year
                
                # Time of day categories
                df['time_of_day'] = pd.cut(
                    df['hour'],
                    bins=[0, 9, 12, 17, 24],
                    labels=['Early (0-9)', 'Morning (9-12)', 'Afternoon (12-17)', 'Evening (17-24)'],
                    include_lowest=True
                )
                
                # Meeting efficiency score (participants per hour)
                df['efficiency_score'] = df['attendees_count'] / (df['duration_minutes'] / 60)
                df['efficiency_score'] = df['efficiency_score'].fillna(0)
            
            logger.info(f"Successfully retrieved {len(df)} meetings from Cloud SQL database")
            return df
            
    except Exception as e:
        logger.error(f"Error retrieving meetings data: {str(e)}")
        # Return empty DataFrame with expected columns if error occurs
        return pd.DataFrame(columns=[
            'user_email', 'department', 'division', 'is_manager',
            'start', 'end', 'duration_minutes', 'attendees_count', 'attendees_accepted',
            'attendees_declined', 'attendees_tentative', 'summary', 'meet_link',
            'meeting_size', 'is_one_on_one'
        ])

@st.cache_data(ttl=3600)  # Cache for 1 hour - this changes infrequently
def get_filter_options():
    """
    Get filter options (departments, users) with caching for better performance
    """
    try:
        with get_db_connection() as conn:
            # Get departments
            dept_query = "SELECT DISTINCT department FROM meetings WHERE department IS NOT NULL ORDER BY department"
            dept_df = pd.read_sql_query(dept_query, conn)
            departments = dept_df['department'].tolist()
            
            # Get users (limit to recent active users)
            user_query = """
            SELECT DISTINCT user_email 
            FROM meetings 
            WHERE user_email IS NOT NULL 
              AND start_time >= (CURRENT_DATE - INTERVAL '90 days')
            ORDER BY user_email 
            LIMIT 1000
            """
            user_df = pd.read_sql_query(user_query, conn)
            users = user_df['user_email'].tolist()
            
            return departments, users
            
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        return [], []

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_summary_stats():
    """
    Get summary statistics efficiently
    """
    try:
        with get_db_connection() as conn:
            query = """
            SELECT 
                COUNT(*) as total_meetings,
                COUNT(DISTINCT user_email) as total_users,
                COUNT(DISTINCT department) as total_departments,
                AVG(duration_minutes) as avg_duration,
                AVG(attendees_count) as avg_attendees,
                MIN(start_time) as earliest_meeting,
                MAX(start_time) as latest_meeting
            FROM meetings
            WHERE start_time >= (CURRENT_DATE - INTERVAL '30 days')
            """
            
            stats_df = pd.read_sql_query(query, conn, parse_dates=['earliest_meeting', 'latest_meeting'])
            return stats_df.iloc[0].to_dict()
            
    except Exception as e:
        logger.error(f"Error getting summary stats: {str(e)}")
        return {}

def save_meetings_data(meetings_df):
    """
    Save meetings data to the PostgreSQL database
    """
    if meetings_df.empty:
        logger.warning("No meetings data to save")
        return
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            inserted = 0
            
            for _, meeting in meetings_df.iterrows():
                # Build dynamic insert with only available columns
                columns = []
                values = []
                params = []
                
                for col in meeting.index:
                    if pd.notna(meeting[col]):
                        columns.append(col)
                        values.append("%s")
                        params.append(meeting[col])
                
                # Create and execute SQL statement
                sql = f"INSERT INTO meetings ({', '.join(columns)}) VALUES ({', '.join(values)})"
                cursor.execute(sql, params)
                inserted += 1
            
            # Commit transaction
            conn.commit()
            logger.info(f"Successfully saved {inserted} meetings to Cloud SQL database")
            
    except Exception as e:
        logger.error(f"Error saving meetings data: {str(e)}")
        raise

def get_user_data():
    """
    Load user data from the PostgreSQL database
    """
    try:
        with get_db_connection() as conn:
            query = """
            SELECT DISTINCT
                user_email,
                division,
                department,
                subdepartment,
                is_manager
            FROM meetings
            WHERE user_email IS NOT NULL
            ORDER BY user_email
            """
            df = pd.read_sql_query(query, conn)
            
            # Convert to dictionary for easy lookup
            user_dict = df.set_index('user_email').to_dict('index')
            logger.info(f"Retrieved data for {len(user_dict)} users from Cloud SQL")
            return user_dict
            
    except Exception as e:
        logger.error(f"Error loading user data: {str(e)}")
        return {}

def get_meetings_filtered(start_date=None, end_date=None, department=None, user_email=None):
    """
    Get filtered meetings data from the PostgreSQL database
    """
    try:
        with get_db_connection() as conn:
            # Build dynamic query
            where_conditions = ["1=1"]
            params = {}
            
            if start_date:
                where_conditions.append("start_time >= %(start_date)s")
                params['start_date'] = start_date
                
            if end_date:
                where_conditions.append("start_time <= %(end_date)s")
                params['end_date'] = end_date
                
            if department:
                where_conditions.append("department = %(department)s")
                params['department'] = department
                
            if user_email:
                where_conditions.append("user_email = %(user_email)s")
                params['user_email'] = user_email
            
            query = f"""
            SELECT *
            FROM meetings
            WHERE {' AND '.join(where_conditions)}
            ORDER BY start_time DESC
            """
            
            df = pd.read_sql_query(query, conn, params=params, parse_dates=['start_time', 'end_time'])
            logger.info(f"Retrieved {len(df)} filtered meetings from Cloud SQL")
            return df
            
    except Exception as e:
        logger.error(f"Error getting filtered meetings: {str(e)}")
        return pd.DataFrame()

def check_db_health():
    """
    Check Cloud SQL database connection health and return status
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM meetings")
                result = cursor.fetchone()
                meeting_count = result[0] if result else 0
                
                cursor.execute("SELECT COUNT(DISTINCT user_email) FROM meetings")
                result = cursor.fetchone()
                user_count = result[0] if result else 0
                
            logger.info(f"Cloud SQL health check passed. Found {meeting_count} meetings for {user_count} users.")
            return True, {'meetings': meeting_count, 'users': user_count}
            
    except Exception as e:
        logger.error(f"Cloud SQL health check failed: {str(e)}")
        return False, {'error': str(e)}

def get_db_type():
    """Return database type (always postgres for Cloud SQL)"""
    return 'postgres'

def execute_query(query, params=None):
    """
    Execute a custom query on the PostgreSQL database
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
                
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return []

# Alias for backwards compatibility
load_meetings_data = get_meetings_data
get_meetings_data_generic = get_meetings_data
load_user_data = get_user_data
get_meetings = get_meetings_filtered