#!/usr/bin/env python3
"""
Generate Test Data for Local Development
Creates realistic meeting data for testing the Calendar Insights application
"""

import os
import sys
import random
import pandas as pd
from datetime import datetime, timedelta, time
import logging

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database, get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample data for generating realistic test data
DEPARTMENTS = [
    "Engineering", "Product Management", "Sales", "Marketing", 
    "Human Resources", "Finance", "Operations", "Customer Success",
    "Design", "Data Science", "Security", "Legal"
]

SAMPLE_USERS = [
    "john.doe@company.com", "jane.smith@company.com", "mike.johnson@company.com",
    "sarah.wilson@company.com", "david.brown@company.com", "lisa.garcia@company.com",
    "robert.miller@company.com", "emily.davis@company.com", "chris.rodriguez@company.com",
    "amanda.martinez@company.com", "kevin.anderson@company.com", "jessica.taylor@company.com",
    "ryan.thomas@company.com", "michelle.jackson@company.com", "alex.white@company.com"
]

MEETING_TITLES = [
    "Daily Standup", "Sprint Planning", "Retrospective", "1:1 Meeting",
    "Team Sync", "Project Review", "Client Meeting", "Product Demo",
    "Code Review", "Design Review", "Strategy Session", "Budget Planning",
    "Performance Review", "Training Session", "All Hands Meeting",
    "Customer Interview", "Technical Architecture Review", "Marketing Campaign Review",
    "Sales Pipeline Review", "Security Audit", "Compliance Check", "Vendor Meeting"
]

TIME_SLOTS = [
    "Morning", "Afternoon", "Evening"
]

def generate_meeting_data(num_meetings=500, days_back=90):
    """Generate realistic meeting data"""
    logger.info(f"Generating {num_meetings} meetings over the last {days_back} days")
    
    meetings = []
    start_date = datetime.now() - timedelta(days=days_back)
    
    for i in range(num_meetings):
        # Random date within the range
        days_offset = random.randint(0, days_back)
        meeting_date = start_date + timedelta(days=days_offset)
        
        # Random time (business hours: 8 AM - 6 PM)
        hour = random.randint(8, 17)
        minute = random.choice([0, 15, 30, 45])
        meeting_time = time(hour, minute)
        
        # Combine date and time
        start_datetime = datetime.combine(meeting_date.date(), meeting_time)
        
        # Random duration (15, 30, 45, 60, 90 minutes)
        duration_minutes = random.choice([15, 30, 45, 60, 90])
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        
        # Random organizer
        organizer = random.choice(SAMPLE_USERS)
        
        # Random department (assign based on organizer)
        department = random.choice(DEPARTMENTS)
        
        # Random meeting title
        title = random.choice(MEETING_TITLES)
        
        # Random attendee count (1-20, with bias toward smaller meetings)
        if random.random() < 0.3:  # 30% chance of 1-on-1
            attendee_count = 2
        elif random.random() < 0.6:  # 30% chance of small team (3-5)
            attendee_count = random.randint(3, 5)
        elif random.random() < 0.85:  # 25% chance of medium team (6-10)
            attendee_count = random.randint(6, 10)
        else:  # 15% chance of large meeting (11-20)
            attendee_count = random.randint(11, 20)
        
        # Generate response data
        total_invites = attendee_count
        accepted = random.randint(int(total_invites * 0.6), int(total_invites * 0.9))
        declined = random.randint(0, int(total_invites * 0.1))
        tentative = random.randint(0, int(total_invites * 0.2))
        needs_action = total_invites - accepted - declined - tentative
        
        # Meeting size category
        if attendee_count == 2:
            meeting_size = "1-on-1"
        elif attendee_count <= 5:
            meeting_size = "Small (2-5)"
        elif attendee_count <= 10:
            meeting_size = "Medium (6-10)"
        else:
            meeting_size = "Large (11+)"
        
        # Day of week
        day_of_week = meeting_date.strftime('%A')
        
        # Time of day
        if hour < 12:
            time_of_day = "Morning"
        elif hour < 17:
            time_of_day = "Afternoon"
        else:
            time_of_day = "Evening"
        
        # Efficiency score (attendees per hour)
        efficiency_score = attendee_count / (duration_minutes / 60)
        
        meeting = {
            'summary': title,
            'start': start_datetime,
            'end': end_datetime,
            'duration_minutes': duration_minutes,
            'user_email': organizer,
            'department': department,
            'attendees_count': attendee_count,
            'attendees_accepted': accepted,
            'attendees_declined': declined,
            'attendees_tentative': tentative,
            'attendees_needs_action': needs_action,
            'is_one_on_one': attendee_count == 2,
            'meeting_size': meeting_size,
            'day_of_week': day_of_week,
            'time_of_day': time_of_day,
            'efficiency_score': round(efficiency_score, 2)
        }
        
        meetings.append(meeting)
    
    return meetings

def insert_meeting_data(meetings):
    """Insert meeting data into the database"""
    logger.info(f"Inserting {len(meetings)} meetings into database")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Prepare the insert statement
            insert_sql = """
            INSERT INTO meetings (
                summary, start_time, end_time, duration_minutes, user_email, department,
                attendees_count, attendees_accepted, attendees_declined, attendees_tentative,
                attendees_needs_action, is_one_on_one, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            """
            
            # Insert meetings in batches
            batch_size = 100
            for i in range(0, len(meetings), batch_size):
                batch = meetings[i:i + batch_size]
                batch_data = []
                
                for meeting in batch:
                    batch_data.append((
                        meeting['summary'],
                        meeting['start'],
                        meeting['end'],
                        meeting['duration_minutes'],
                        meeting['user_email'],
                        meeting['department'],
                        meeting['attendees_count'],
                        meeting['attendees_accepted'],
                        meeting['attendees_declined'],
                        meeting['attendees_tentative'],
                        meeting['attendees_needs_action'],
                        meeting['is_one_on_one']
                    ))
                
                cursor.executemany(insert_sql, batch_data)
                conn.commit()
                logger.info(f"Inserted batch {i//batch_size + 1}/{(len(meetings) + batch_size - 1)//batch_size}")
            
            logger.info("✅ Successfully inserted all meeting data")
        
    except Exception as e:
        logger.error(f"❌ Error inserting meeting data: {e}")
        raise

def generate_user_data():
    """Generate user data for the database"""
    logger.info("Generating user data")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Clear existing users
            cursor.execute("DELETE FROM users")
            
            # Insert sample users
            insert_sql = """
            INSERT INTO users (email, department, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
            """
            
            user_data = []
            for email in SAMPLE_USERS:
                department = random.choice(DEPARTMENTS)
                user_data.append((email, department))
            
            cursor.executemany(insert_sql, user_data)
            conn.commit()
            
            logger.info(f"✅ Successfully inserted {len(SAMPLE_USERS)} users")
        
    except Exception as e:
        logger.error(f"❌ Error inserting user data: {e}")
        raise

def main():
    """Main function to generate test data"""
    print("🧪 Calendar Insights Test Data Generator")
    print("=" * 50)
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        
        # Generate user data
        generate_user_data()
        
        # Generate meeting data
        meetings = generate_meeting_data(num_meetings=1000, days_back=90)
        
        # Insert meeting data
        insert_meeting_data(meetings)
        
        print("\n🎉 Test data generation completed successfully!")
        print(f"✅ Generated {len(meetings)} meetings")
        print(f"✅ Generated {len(SAMPLE_USERS)} users")
        print(f"✅ Data spans the last 90 days")
        print("\n💡 You can now:")
        print("1. Access the dashboard at http://localhost:8080")
        print("2. Test the AI chat functionality")
        print("3. Explore the meeting analytics")
        
    except Exception as e:
        logger.error(f"❌ Failed to generate test data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
