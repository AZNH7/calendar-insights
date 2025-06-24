#!/usr/bin/env python3
"""
Database Cleanup Script
Cleans up the Cloud SQL database by dropping all data and recreating fresh schema
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection_params():
    """Get database connection parameters from environment variables"""
    return {
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please ensure all database connection environment variables are set.")
        return False
    return True

def cleanup_database():
    """Clean up the database by dropping all tables and recreating schema"""
    params = get_db_connection_params()
    
    try:
        # Connect to database
        if params['host'].startswith('/cloudsql/'):
            conn = psycopg2.connect(
                host=params['host'],
                database=params['database'],
                user=params['user'],
                password=params['password'],
                connect_timeout=30
            )
        else:
            conn = psycopg2.connect(
                host=params['host'],
                port=int(params['port']),
                database=params['database'],
                user=params['user'],
                password=params['password'],
                connect_timeout=30
            )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("Connected to database successfully")
        
        # Drop existing tables if they exist
        logger.info("Dropping existing tables...")
        cursor.execute("DROP TABLE IF EXISTS meetings CASCADE")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        cursor.execute("DROP TABLE IF EXISTS fetch_history CASCADE")
        logger.info("Existing tables dropped")
        
        # Create meetings table
        logger.info("Creating meetings table...")
        cursor.execute('''
            CREATE TABLE meetings (
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_id TEXT UNIQUE,
                calendar_id TEXT,
                organizer_email TEXT
            )
        ''')
        logger.info("Meetings table created")
        
        # Create users table
        logger.info("Creating users table...")
        cursor.execute('''
            CREATE TABLE users (
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
        logger.info("Users table created")
        
        # Create fetch history table to track data fetching
        logger.info("Creating fetch_history table...")
        cursor.execute('''
            CREATE TABLE fetch_history (
                id SERIAL PRIMARY KEY,
                fetch_date DATE NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT NOT NULL,
                records_fetched INTEGER DEFAULT 0,
                error_message TEXT,
                fetch_type TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Fetch history table created")
        
        # Create indexes for performance
        logger.info("Creating indexes...")
        cursor.execute('CREATE INDEX idx_meetings_user_email ON meetings(user_email)')
        cursor.execute('CREATE INDEX idx_meetings_start_time ON meetings(start_time)')
        cursor.execute('CREATE INDEX idx_meetings_department ON meetings(department)')
        cursor.execute('CREATE INDEX idx_meetings_event_id ON meetings(event_id)')
        cursor.execute('CREATE INDEX idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX idx_fetch_history_date ON fetch_history(fetch_date)')
        logger.info("Indexes created")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        logger.info("Database cleanup and initialization complete!")
        logger.info(f"Created tables: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting database cleanup...")
    
    if not validate_environment():
        logger.error("Environment validation failed. Exiting.")
        sys.exit(1)
    
    if not cleanup_database():
        logger.error("Database cleanup failed. Exiting.")
        sys.exit(1)
    
    logger.info("Database cleanup completed successfully!")

if __name__ == "__main__":
    main() 