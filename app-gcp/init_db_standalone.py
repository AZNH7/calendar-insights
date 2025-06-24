#!/usr/bin/env python3
"""
Standalone database initialization script for PostgreSQL Cloud SQL
"""

import os
import sys
import psycopg2
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

def test_connection():
    """Test database connection"""
    if not validate_environment():
        return False
        
    params = get_db_connection_params()
    
    try:
        logger.info("Testing database connection...")
        conn = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            database=params['database'],
            user=params['user'],
            password=params['password'],
            connect_timeout=30
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        logger.info(f"✅ Connected to PostgreSQL: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

def init_database():
    """Initialize database with required tables"""
    if not validate_environment():
        return False
        
    params = get_db_connection_params()
    
    try:
        logger.info("Initializing database schema...")
        conn = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            database=params['database'],
            user=params['user'],
            password=params['password'],
            connect_timeout=30
        )
        
        cursor = conn.cursor()
        
        # Create meetings table
        logger.info("Creating meetings table...")
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
                event_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create users table
        logger.info("Creating users table...")
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
        
        # Create indexes
        logger.info("Creating indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_user_email ON meetings(user_email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_department ON meetings(department)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_event_id ON meetings(event_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        # Add unique constraint on event_id if not exists
        logger.info("Adding unique constraint on event_id...")
        try:
            cursor.execute('ALTER TABLE meetings ADD CONSTRAINT unique_event_id UNIQUE (event_id)')
        except psycopg2.errors.DuplicateTable:
            logger.info("Unique constraint already exists")
        
        conn.commit()
        logger.info("✅ Database initialization completed successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

if __name__ == '__main__':
    logger.info("🚀 Starting database initialization...")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test connection only
        success = test_connection()
    else:
        # Full initialization
        success = init_database()
    
    if success:
        logger.info("✅ Operation completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Operation failed!")
        sys.exit(1) 