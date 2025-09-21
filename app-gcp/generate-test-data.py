#!/usr/bin/env python3

"""
📊 Calendar Insights - Test Data Generator
Generates realistic fake data for development and testing
"""

import os
import sys
import random
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple
import psycopg2
import argparse

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import get_db_connection, init_database
    from faker import Faker
    import pandas as pd
except ImportError as e:
    print(f"❌ Missing required dependencies: {e}")
    print("📦 Please install: pip install faker pandas psycopg2-binary")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

class TestDataGenerator:
    """Generates realistic test data for calendar insights application"""
    
    def __init__(self):
        self.departments = [
            ('Engineering', 'Technology'),
            ('Product', 'Technology'),
            ('Design', 'Technology'),
            ('Marketing', 'Growth'),
            ('Sales', 'Growth'),
            ('Customer Success', 'Growth'),
            ('HR', 'Operations'),
            ('Finance', 'Operations'),
            ('Legal', 'Operations'),
            ('Operations', 'Operations'),
            ('Security', 'Technology'),
            ('Data Science', 'Technology'),
        ]
        
        self.subdepartments = {
            'Engineering': ['Backend', 'Frontend', 'DevOps', 'Mobile', 'Platform', 'QA'],
            'Product': ['Growth', 'Core', 'Platform', 'Analytics'],
            'Design': ['UX', 'UI', 'Research', 'Brand'],
            'Marketing': ['Digital', 'Content', 'Growth', 'Brand'],
            'Sales': ['Enterprise', 'SMB', 'Inside Sales', 'Solutions'],
            'Customer Success': ['Support', 'Onboarding', 'Account Management'],
            'HR': ['Talent', 'People Ops', 'Learning'],
            'Finance': ['Accounting', 'FP&A', 'Treasury'],
            'Legal': ['Corporate', 'Compliance', 'IP'],
            'Operations': ['IT', 'Facilities', 'Business Ops'],
            'Security': ['InfoSec', 'Compliance', 'Risk'],
            'Data Science': ['Analytics', 'ML', 'Data Engineering'],
        }
        
        self.meeting_types = [
            ('Daily Standup', 15, 3, 0.8),
            ('Weekly Team Meeting', 60, 8, 0.7),
            ('Sprint Planning', 120, 6, 0.9),
            ('Sprint Retrospective', 60, 6, 0.8),
            ('Project Sync', 30, 4, 0.7),
            ('1:1 Meeting', 30, 2, 0.9),
            ('All Hands', 60, 50, 0.6),
            ('Architecture Review', 90, 5, 0.8),
            ('Code Review', 30, 3, 0.8),
            ('Client Meeting', 60, 4, 0.9),
            ('Design Review', 45, 4, 0.8),
            ('Product Demo', 30, 10, 0.7),
            ('Training Session', 90, 15, 0.6),
            ('Interview', 45, 3, 0.9),
            ('Board Meeting', 120, 8, 0.95),
            ('Strategy Session', 180, 6, 0.8),
            ('Town Hall', 45, 25, 0.5),
            ('Customer Call', 30, 3, 0.9),
            ('Vendor Meeting', 60, 4, 0.8),
            ('Emergency Meeting', 30, 5, 0.95),
        ]
        
        self.company_domains = [
            'company.com', 'corp.com', 'tech.io', 'startup.co'
        ]
        
        self.external_domains = [
            'gmail.com', 'yahoo.com', 'outlook.com', 'client-company.com',
            'vendor-corp.com', 'partner.org', 'contractor.net'
        ]
    
    def generate_users(self, count: int = 100) -> List[Dict]:
        """Generate realistic user data"""
        users = []
        
        for i in range(count):
            # Select department and division
            dept, division = random.choice(self.departments)
            subdept = random.choice(self.subdepartments.get(dept, ['General']))
            
            # Generate realistic name and email
            first_name = fake.first_name()
            last_name = fake.last_name()
            domain = random.choice(self.company_domains)
            email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
            
            # Manager probability based on department size
            is_manager = random.random() < 0.15  # 15% are managers
            
            users.append({
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'department': dept,
                'division': division,
                'subdepartment': subdept,
                'is_manager': is_manager
            })
        
        return users
    
    def generate_external_attendees(self, count: int) -> List[str]:
        """Generate external attendee emails"""
        attendees = []
        for _ in range(count):
            domain = random.choice(self.external_domains)
            email = f"{fake.first_name().lower()}.{fake.last_name().lower()}@{domain}"
            attendees.append(email)
        return attendees
    
    def generate_meetings(self, users: List[Dict], days_back: int = 90, meetings_per_day: int = 50) -> List[Dict]:
        """Generate realistic meeting data"""
        meetings = []
        
        # Create date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        current_date = start_date
        meeting_id = 1
        
        while current_date <= end_date:
            # Skip weekends for most meetings
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                daily_meetings = self.generate_daily_meetings(
                    users, current_date, meetings_per_day, meeting_id
                )
                meetings.extend(daily_meetings)
                meeting_id += len(daily_meetings)
            
            # Add some weekend meetings (much fewer)
            elif random.random() < 0.1:  # 10% chance of weekend meetings
                weekend_meetings = self.generate_daily_meetings(
                    users, current_date, max(1, meetings_per_day // 10), meeting_id
                )
                meetings.extend(weekend_meetings)
                meeting_id += len(weekend_meetings)
            
            current_date += timedelta(days=1)
        
        return meetings
    
    def generate_daily_meetings(self, users: List[Dict], date: datetime, count: int, start_id: int) -> List[Dict]:
        """Generate meetings for a specific day"""
        meetings = []
        
        # Working hours: 8 AM to 6 PM
        work_start = 8
        work_end = 18
        
        for i in range(count):
            # Select meeting type
            meeting_name, base_duration, base_attendees, acceptance_rate = random.choice(self.meeting_types)
            
            # Vary duration slightly
            duration = base_duration + random.randint(-15, 15)
            duration = max(15, duration)  # Minimum 15 minutes
            
            # Generate meeting time (business hours bias)
            if random.random() < 0.8:  # 80% during business hours
                hour = random.randint(work_start, work_end - 1)
            else:  # 20% outside business hours
                hour = random.choice(list(range(6, work_start)) + list(range(work_end, 22)))
            
            minute = random.choice([0, 15, 30, 45])  # Start on quarter hours
            
            start_time = datetime.combine(date.date(), datetime.min.time()) + timedelta(hours=hour, minutes=minute)
            end_time = start_time + timedelta(minutes=duration)
            
            # Select organizer
            organizer = random.choice(users)
            
            # Generate attendees
            attendee_count = max(2, base_attendees + random.randint(-2, 4))
            
            # Select internal attendees (including organizer)
            internal_attendees = [organizer]
            
            # Add more internal attendees
            if attendee_count > 1:
                # Bias towards same department
                same_dept_users = [u for u in users if u['department'] == organizer['department'] and u != organizer]
                other_users = [u for u in users if u['department'] != organizer['department']]
                
                remaining_internal = min(attendee_count - 1, len(users) - 1)
                
                # 70% from same department, 30% from other departments
                same_dept_count = int(remaining_internal * 0.7)
                other_dept_count = remaining_internal - same_dept_count
                
                if same_dept_users and same_dept_count > 0:
                    internal_attendees.extend(random.sample(same_dept_users, min(same_dept_count, len(same_dept_users))))
                
                if other_users and other_dept_count > 0:
                    internal_attendees.extend(random.sample(other_users, min(other_dept_count, len(other_users))))
            
            # Add external attendees (20% chance)
            external_count = 0
            if random.random() < 0.2:
                external_count = random.randint(1, 3)
            
            total_attendees = len(internal_attendees) + external_count
            
            # Calculate acceptance rates
            accepted = int(total_attendees * acceptance_rate)
            declined = random.randint(0, total_attendees - accepted)
            tentative = random.randint(0, total_attendees - accepted - declined)
            needs_action = total_attendees - accepted - declined - tentative
            
            # Generate external attendee emails
            external_emails = self.generate_external_attendees(external_count)
            all_attendee_emails = [u['email'] for u in internal_attendees] + external_emails
            
            # Determine meeting characteristics
            is_one_on_one = total_attendees == 2
            has_manager = any(u['is_manager'] for u in internal_attendees)
            unique_departments = len(set(u['department'] for u in internal_attendees))
            departments_list = ', '.join(set(u['department'] for u in internal_attendees))
            
            # Generate meeting summary with realistic variation
            summary_variations = [
                meeting_name,
                f"{meeting_name} - {organizer['department']}",
                f"{organizer['department']} {meeting_name}",
                f"Q{(date.month-1)//3 + 1} {meeting_name}",
                f"{meeting_name} (Weekly)",
                f"{meeting_name} - Follow-up",
            ]
            summary = random.choice(summary_variations)
            
            meeting = {
                'user_email': organizer['email'],
                'department': organizer['department'],
                'division': organizer['division'],
                'subdepartment': organizer['subdepartment'],
                'is_manager': organizer['is_manager'],
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': duration,
                'attendees_count': total_attendees,
                'attendees_accepted': accepted,
                'attendees_declined': declined,
                'attendees_tentative': tentative,
                'attendees_needs_action': needs_action,
                'attendees_accepted_emails': ', '.join(all_attendee_emails[:accepted]),
                'summary': summary,
                'meet_link': f"https://meet.google.com/{fake.lexify('???-????-???')}",
                'html_link': f"https://calendar.google.com/event?eid={fake.uuid4()}",
                'is_one_on_one': is_one_on_one,
                'has_manager_attendee': has_manager,
                'unique_departments': unique_departments,
                'departments_list': departments_list,
            }
            
            meetings.append(meeting)
        
        return meetings
    
    def save_users_to_db(self, users: List[Dict]) -> int:
        """Save users to database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insert users
                inserted = 0
                for user in users:
                    try:
                        cursor.execute("""
                            INSERT INTO users (email, department, division, subdepartment, is_manager)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (email) DO UPDATE SET
                                department = EXCLUDED.department,
                                division = EXCLUDED.division,
                                subdepartment = EXCLUDED.subdepartment,
                                is_manager = EXCLUDED.is_manager,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            user['email'],
                            user['department'],
                            user['division'], 
                            user['subdepartment'],
                            user['is_manager']
                        ))
                        inserted += 1
                    except Exception as e:
                        logger.warning(f"Failed to insert user {user['email']}: {e}")
                        continue
                
                conn.commit()
                logger.info(f"✅ Successfully saved {inserted} users to database")
                return inserted
                
        except Exception as e:
            logger.error(f"❌ Error saving users to database: {e}")
            return 0
    
    def save_meetings_to_db(self, meetings: List[Dict]) -> int:
        """Save meetings to database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insert meetings
                inserted = 0
                for meeting in meetings:
                    try:
                        cursor.execute("""
                            INSERT INTO meetings (
                                user_email, department, division, subdepartment, is_manager,
                                start_time, end_time, duration_minutes, attendees_count,
                                attendees_accepted, attendees_declined, attendees_tentative,
                                attendees_needs_action, attendees_accepted_emails, summary,
                                meet_link, html_link, is_one_on_one, has_manager_attendee,
                                unique_departments, departments_list
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            meeting['user_email'],
                            meeting['department'],
                            meeting['division'],
                            meeting['subdepartment'],
                            meeting['is_manager'],
                            meeting['start_time'],
                            meeting['end_time'],
                            meeting['duration_minutes'],
                            meeting['attendees_count'],
                            meeting['attendees_accepted'],
                            meeting['attendees_declined'],
                            meeting['attendees_tentative'],
                            meeting['attendees_needs_action'],
                            meeting['attendees_accepted_emails'],
                            meeting['summary'],
                            meeting['meet_link'],
                            meeting['html_link'],
                            meeting['is_one_on_one'],
                            meeting['has_manager_attendee'],
                            meeting['unique_departments'],
                            meeting['departments_list']
                        ))
                        inserted += 1
                    except Exception as e:
                        logger.warning(f"Failed to insert meeting: {e}")
                        continue
                
                conn.commit()
                logger.info(f"✅ Successfully saved {inserted} meetings to database")
                return inserted
                
        except Exception as e:
            logger.error(f"❌ Error saving meetings to database: {e}")
            return 0
    
    def clear_existing_data(self, confirm: bool = False):
        """Clear existing test data"""
        if not confirm:
            print("⚠️  This will delete ALL existing data from the database!")
            response = input("Are you sure? Type 'yes' to confirm: ").lower()
            if response != 'yes':
                print("❌ Operation cancelled")
                return False
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Clear meetings first (foreign key dependency)
                cursor.execute("DELETE FROM meetings")
                meetings_deleted = cursor.rowcount
                
                # Clear users
                cursor.execute("DELETE FROM users")
                users_deleted = cursor.rowcount
                
                conn.commit()
                logger.info(f"🗑️  Cleared {meetings_deleted} meetings and {users_deleted} users")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error clearing data: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get current database statistics"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get counts
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM meetings")
                meeting_count = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute("SELECT MIN(start_time), MAX(start_time) FROM meetings")
                date_result = cursor.fetchone()
                min_date = date_result[0] if date_result[0] else None
                max_date = date_result[1] if date_result[1] else None
                
                # Get departments
                cursor.execute("SELECT COUNT(DISTINCT department) FROM users WHERE department IS NOT NULL")
                dept_count = cursor.fetchone()[0]
                
                return {
                    'users': user_count,
                    'meetings': meeting_count,
                    'departments': dept_count,
                    'date_range': {
                        'min': min_date,
                        'max': max_date
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {}

def main():
    """Main function to run the test data generator"""
    parser = argparse.ArgumentParser(description='Generate test data for Calendar Insights')
    parser.add_argument('--users', type=int, default=100, help='Number of users to generate (default: 100)')
    parser.add_argument('--days', type=int, default=90, help='Number of days of meeting history (default: 90)')
    parser.add_argument('--meetings-per-day', type=int, default=50, help='Average meetings per day (default: 50)')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before generating new data')
    parser.add_argument('--stats-only', action='store_true', help='Only show database statistics')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    print("📊 Calendar Insights - Test Data Generator")
    print("=" * 50)
    
    generator = TestDataGenerator()
    
    # Show current stats
    print("\n📈 Current Database Statistics:")
    stats = generator.get_database_stats()
    if stats:
        print(f"  👥 Users: {stats['users']:,}")
        print(f"  📅 Meetings: {stats['meetings']:,}")
        print(f"  🏢 Departments: {stats['departments']}")
        if stats['date_range']['min'] and stats['date_range']['max']:
            print(f"  📆 Date Range: {stats['date_range']['min'].date()} to {stats['date_range']['max'].date()}")
    
    if args.stats_only:
        return
    
    try:
        # Initialize database
        print("\n🔧 Initializing database...")
        init_database()
        
        # Clear existing data if requested
        if args.clear:
            print("\n🗑️  Clearing existing data...")
            if not generator.clear_existing_data(confirm=args.yes):
                return
        
        # Generate users
        print(f"\n👥 Generating {args.users} users...")
        users = generator.generate_users(args.users)
        users_saved = generator.save_users_to_db(users)
        
        # Generate meetings
        total_meetings = args.days * args.meetings_per_day
        print(f"\n📅 Generating ~{total_meetings:,} meetings over {args.days} days...")
        meetings = generator.generate_meetings(users, args.days, args.meetings_per_day)
        meetings_saved = generator.save_meetings_to_db(meetings)
        
        # Show final stats
        print("\n🎉 Data generation complete!")
        print("=" * 50)
        final_stats = generator.get_database_stats()
        if final_stats:
            print(f"📊 Final Statistics:")
            print(f"  👥 Total Users: {final_stats['users']:,}")
            print(f"  📅 Total Meetings: {final_stats['meetings']:,}")
            print(f"  🏢 Departments: {final_stats['departments']}")
            if final_stats['date_range']['min'] and final_stats['date_range']['max']:
                print(f"  📆 Date Range: {final_stats['date_range']['min'].date()} to {final_stats['date_range']['max'].date()}")
        
        print(f"\n🚀 Ready for testing! Access your app at http://localhost:8080")
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
