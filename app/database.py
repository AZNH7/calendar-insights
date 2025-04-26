import sqlite3
import os
import logging
import pandas as pd
import yaml
import streamlit as st
from contextlib import contextmanager
from functools import lru_cache
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_exclusions():
    try:
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
def get_db_connection():
    # database connection
    conn = None
    try:
        conn = sqlite3.connect('/data/sqlite/meetings.db')
        yield conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_meetings():
    # Load meetings data from SQLite database
    try:
        with get_db_connection() as conn:
            query = """
                SELECT
                    user_email,
                    department,
                    is_manager,
                    start,
                    "end",
                    duration_minutes,
                    attendees_accepted,
                    attendees_accepted_emails,
                    summary,
                    meeting_size_category,
                    is_one_on_one,
                    has_manager_attendee,
                    unique_departments,
                    departments_list
                FROM meetings
                WHERE start >= date('now', '-1 year')  -- Limit to last year
                ORDER BY start DESC
            """
            df = pd.read_sql_query(query, conn, parse_dates=['start', 'end'])            
       
            df['day_of_week'] = pd.Categorical(df['start'].dt.day_name(), 
                categories=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
            df['hour'] = df['start'].dt.hour
            df['week'] = df['start'].dt.isocalendar().week
            
            df['department'] = df['department'].astype('category')
            df['meeting_size_category'] = df['meeting_size_category'].astype('category')
            
            return df
    except Exception as e:
        logger.error(f"Error loading meetings data: {str(e)}")
        return pd.DataFrame()

def load_meetings_data():
    # Load meetings data meetings.db
    try:
        conn = sqlite3.connect('/data/sqlite/meetings.db')
        
        # query specific columns
        query = """
            WITH meeting_departments AS (
                SELECT DISTINCT
                    m.start_time,
                    m.end_time,
                    m.duration_minutes,
                    m.attendees_accepted,
                    m.summary,
                    m.user_email,
                    m.department,
                    m.division,
                    COUNT(DISTINCT m2.department) as unique_departments
                FROM meetings m
                LEFT JOIN (
                    SELECT DISTINCT department 
                    FROM meetings 
                    WHERE department IS NOT NULL
                ) m2 ON m2.department IN (
                    SELECT DISTINCT department 
                    FROM meetings 
                    WHERE user_email = m.user_email
                )
                WHERE m.start_time >= date('now', '-6 months')
                GROUP BY 
                    m.start_time,
                    m.end_time,
                    m.duration_minutes,
                    m.attendees_accepted,
                    m.summary,
                    m.user_email,
                    m.department,
                    m.division
            )
            SELECT * FROM meeting_departments
        """

        # chunksize to avoid memory issues
        df_list = []
        for chunk in pd.read_sql_query(query, conn, chunksize=10000):

            chunk['start'] = pd.to_datetime(chunk['start_time'])
            chunk['end'] = pd.to_datetime(chunk['end_time'])
            chunk['meeting_size_category'] = chunk['attendees_accepted'].apply(
                lambda x: '1:1' if x == 2 else ('Small' if x < 8 else 'Large')
            )
            chunk['day_of_week'] = chunk['start'].dt.day_name()
            df_list.append(chunk)
        
        # all chunks
        df = pd.concat(df_list, ignore_index=True)
        
        # Convert categorical columns
        categorical_columns = ['department', 'division', 'meeting_size_category', 'day_of_week']
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype('category')
        
        conn.close()
        return df
        
    except Exception as e:
        logger.error(f"Error loading meetings data: {str(e)}")
        return pd.DataFrame()

def load_user_data():
    # Load user data from meetings.db
    try:
        conn = sqlite3.connect('/data/sqlite/meetings.db')
        query = """
            SELECT DISTINCT
                user_email,
                division,
                department,
                subdepartment,
                is_manager
            FROM meetings
            WHERE user_email IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # convert to dictionary
        user_dict = df.set_index('user_email').to_dict('index')
        return user_dict
    except Exception as e:
        logger.error(f"Error loading user data: {str(e)}")
        return {}

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_meetings(start_date=None, end_date=None, department=None):
    # Load other meetings data filtered from meetings.db
    try:
        conn = sqlite3.connect('/data/sqlite/meetings.db')
        
        base_query = """
            SELECT 
                m.start_time,
                m.end_time,
                m.duration_minutes,
                m.attendees_accepted,
                m.summary,
                m.user_email,
                m.department,
                m.division,
                COUNT(DISTINCT m2.department) as unique_departments
            FROM meetings m
            LEFT JOIN meetings m2 ON m2.user_email = m.user_email
            WHERE 1=1
        """
        
        params = []
        if start_date:
            base_query += " AND m.start_time >= ?"
            params.append(start_date)
        
        if end_date:
            base_query += " AND m.start_time <= ?"
            params.append(end_date)
            
        if department:
            base_query += " AND m.department = ?"
            params.append(department)
            
        base_query += """
            GROUP BY 
                m.start_time,
                m.end_time,
                m.duration_minutes,
                m.attendees_accepted,
                m.summary,
                m.user_email,
                m.department,
                m.division,
        """
        
        df = pd.read_sql_query(base_query, conn, params=params)
        conn.close()
        
        # datetime conversion
        df['start'] = pd.to_datetime(df['start_time'])
        df['end'] = pd.to_datetime(df['end_time'])
        df['meeting_size_category'] = df['attendees_accepted'].apply(
            lambda x: '1:1' if x == 2 else ('Small' if x < 8 else 'Large')
        )
        
        # categorical conversion
        df['meeting_size_category'] = df['meeting_size_category'].astype('category')
        df['department'] = df['department'].astype('category')
        df['division'] = df['division'].astype('category')
        
        return df
        
    except Exception as e:
        logger.error(f"Error getting meetings: {str(e)}")
        return pd.DataFrame()

def execute_query(query, params=None):
    # query on the SQLite database
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return []

class DatabaseConnection:
    def __init__(self):
        self.conn = None
        self.db_path = os.getenv('SQLITE_DB_PATH', '/data/sqlite/meetings.db')
        
        # check if the directory exists
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        os.chmod(db_dir, 0o777)  # need full permissions for the directory

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(
                self.db_path, 
                timeout=30.0,
                isolation_level='IMMEDIATE'
            )
            self.conn.row_factory = sqlite3.Row
            
            # concurrent access enabled
            self.conn.execute('PRAGMA journal_mode=WAL')
            self.conn.execute('PRAGMA busy_timeout=30000')
            
            return self.conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to SQLite database: {e}")
            logger.error(f"Database path: {self.db_path}")
            logger.error(f"Directory exists: {os.path.exists(os.path.dirname(self.db_path))}")
            logger.error(f"Directory permissions: {oct(os.stat(os.path.dirname(self.db_path)).st_mode)}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            self.conn.close() 