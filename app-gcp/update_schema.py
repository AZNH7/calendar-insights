#!/usr/bin/env python3
"""
Update database schema to add unique constraint on event_id
"""

import os
import sys
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    """Add event_id column and unique constraint to prevent duplicates"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if event_id column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'meetings' 
                AND column_name = 'event_id'
            """)
            
            event_id_exists = cursor.fetchone()
            
            if not event_id_exists:
                print("🔧 Adding event_id column...")
                cursor.execute("ALTER TABLE meetings ADD COLUMN event_id TEXT")
                print("✅ event_id column added")
            else:
                print("✅ event_id column already exists")
            
            # Check if unique constraint already exists
            cursor.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'meetings' 
                AND constraint_type = 'UNIQUE' 
                AND constraint_name LIKE '%event_id%'
            """)
            
            existing_constraint = cursor.fetchone()
            
            if existing_constraint:
                print(f"✅ Unique constraint on event_id already exists: {existing_constraint[0]}")
                return True
            
            # Add unique constraint
            print("🔧 Adding unique constraint on event_id...")
            cursor.execute("ALTER TABLE meetings ADD CONSTRAINT unique_event_id UNIQUE (event_id)")
            
            # Create index for better performance
            print("🔧 Creating index on event_id...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_event_id ON meetings (event_id)")
            
            # Create index on start_time for better query performance
            print("🔧 Creating index on start_time...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings (start_time)")
            
            # Create index on user_email
            print("🔧 Creating index on user_email...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_user_email ON meetings (user_email)")
            
            conn.commit()
            print("✅ Schema update completed successfully")
            
            # Show current indexes
            cursor.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'meetings'
                ORDER BY indexname
            """)
            indexes = cursor.fetchall()
            
            print("\n📊 Current indexes on meetings table:")
            for index_name, index_def in indexes:
                print(f"  - {index_name}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error updating schema: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Updating database schema...")
    
    # Validate environment variables are set
    required_env_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please ensure all database connection environment variables are set.")
        sys.exit(1)
    
    success = update_schema()
    
    if success:
        print("✅ Schema update completed!")
    else:
        print("❌ Schema update failed!")
        sys.exit(1) 