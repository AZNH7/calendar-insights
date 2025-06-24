#!/usr/bin/env python3
# Script to fetch latest meeting data when container starts
import os
import logging
import sys
from datetime import datetime, timezone, timedelta
import argparse
import sqlite3
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

def load_meetings(db_path, days_back=30):
    """Load meetings from the database for processing"""
    try:
        logger.info(f"Loading meetings from database: {db_path}")
        conn = sqlite3.connect(db_path)
        # Query to get recent Google Meet meetings
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        cutoff_date_str = cutoff_date.isoformat()
        
        query = """
        SELECT 
            rowid as id, summary, start_time, end_time, meet_link, 
            user_email, is_google_meet
        FROM meetings 
        WHERE is_google_meet = 1 
        AND start_time >= ?
        ORDER BY start_time DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(cutoff_date_str,))
        conn.close()
        
        if df.empty:
            logger.warning("No meetings found in the database for the specified time period")
            return pd.DataFrame()
            
        # Extract meeting code from meet_link
        df['meeting_code'] = df['meet_link'].apply(lambda x: x.split('/')[-1].split('?')[0] if x and isinstance(x, str) else None)
        
        # Convert timestamps
        df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
        df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')
        
        logger.info(f"Loaded {len(df)} meetings from the database")
        return df
    except Exception as e:
        logger.error(f"Error loading meetings from database: {e}")
        return pd.DataFrame()

def fetch_latest_data(days_back=7):
    """Fetch latest meeting data"""
    logger.info(f"Starting data fetch for the last {days_back} days")
    
    # Resolve database path using environment variables
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Try DATABASE_URL first (sqlite:///path)
    db_url_env = os.getenv("DATABASE_URL")
    sqlite_db_path_env = os.getenv("SQLITE_DB_PATH")
    
    if db_url_env:
        if db_url_env.startswith("sqlite:///"):
            db_path_temp = db_url_env[len("sqlite:///"):]
            if not os.path.isabs(db_path_temp):
                db_path = os.path.join(project_root, db_path_temp)
            else:
                db_path = db_path_temp
        else:
            # Assume DATABASE_URL is a path relative to project root
            db_path = os.path.join(project_root, db_url_env)
        logger.info(f"Using DATABASE_URL='{db_url_env}', resolved to absolute path: {os.path.abspath(db_path) if db_path else 'None'}")
    elif sqlite_db_path_env:
        db_path = sqlite_db_path_env  # Use the environment path as-is (it's already absolute in Docker)
        logger.info(f"Using SQLITE_DB_PATH='{sqlite_db_path_env}'")
    else:
        # Fallback to a hardcoded default
        db_path = os.path.join(project_root, "data/sqlite/meetings.db")
        logger.info(f"No database path specified in environment. Using default: {db_path}")
    
    try:
        # Load recent meetings from the database
        meetings_df = load_meetings(db_path, days_back=days_back)
        
        if meetings_df.empty:
            logger.warning("No meetings found for the specified time period")
            return
        
        logger.info(f"Processed {len(meetings_df)} meetings")
        return meetings_df
    except Exception as e:
        logger.error(f"Error during data fetching: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch the latest meeting data')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back for meetings')
    args = parser.parse_args()
    
    try:
        fetch_latest_data(days_back=args.days)
        logger.info("Data fetching completed successfully")
    except Exception as e:
        logger.error(f"Error in data fetching process: {e}")
        sys.exit(1)
