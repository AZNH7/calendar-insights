import psycopg2
import os
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the PostgreSQL database with schema"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    try:
        # Parse the database URL
        url = urlparse(database_url)
        
        logger.info(f"Initializing database at {url.hostname}")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
            
        # Drop existing table if it exists
        cursor.execute("DROP TABLE IF EXISTS meetings")
            
        # Create table with proper schema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id SERIAL PRIMARY KEY,
            start_time TIMESTAMPTZ NOT NULL,
            end_time TIMESTAMPTZ NOT NULL,
            duration_minutes INTEGER,
            attendees_accepted INTEGER,
            attendees_accepted_emails TEXT[],
            attendees_tentative INTEGER,
            attendees_declined INTEGER,
            attendees_emails TEXT[],
            attendees_needs_action INTEGER,
            summary TEXT,
            user_email VARCHAR(255) NOT NULL,
            division VARCHAR(255),
            department VARCHAR(255),
            subdepartment VARCHAR(255),
            unique_departments INTEGER,
            departments_list TEXT[],
            meeting_size_category VARCHAR(50),
            is_one_on_one BOOLEAN,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )""")
            
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_user_email ON meetings(user_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_department ON meetings(department)")
            
        conn.commit()
        logger.info("Database schema created successfully")
            
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        logger.info(f"Created tables: {tables}")
            
        # Verify schema
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'meetings'
        """)
        columns = cursor.fetchall()
        logger.info(f"Table schema: {columns}")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_db() 