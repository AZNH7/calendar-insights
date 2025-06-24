#!/usr/bin/env python3
"""
Dynamic calendar data fetcher - supports both historical and incremental fetching
Usage:
  python dynamic_fetch.py --years 3     # Fetch 3 years of historical data
  python dynamic_fetch.py --daily       # Fetch yesterday's data (for cron)
  python dynamic_fetch.py --days 30     # Fetch last 30 days
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta, timezone
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from calendar_service import GoogleCalendarService
from database import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_historical_data(years_back=1):
    """Fetch X years of historical calendar data in monthly batches"""
    try:
        service = GoogleCalendarService()
        
        if not service.authenticate():
            logger.error("Failed to authenticate with Google Calendar")
            return False
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=years_back*365)
        
        print(f"🔍 FETCHING {years_back} YEAR(S): {start_date.date()} to {end_date.date()}")
        print(f"📅 This covers {(end_date - start_date).days} days of calendar history")
        
        all_meetings = []
        total_batches = years_back * 12  # months
        current_batch = 0
        
        # Process in monthly batches
        current_start = start_date
        
        while current_start < end_date:
            current_batch += 1
            current_end = min(current_start + timedelta(days=31), end_date)
            
            print(f"\n📦 Batch {current_batch}/{total_batches}: {current_start.date()} to {current_end.date()}")
            
            try:
                batch_meetings = service.fetch_calendar_data(current_start, current_end)
                
                if batch_meetings:
                    all_meetings.extend(batch_meetings)
                    print(f"   ✅ Found {len(batch_meetings)} events")
                else:
                    print(f"   📭 No events found")
                
                time.sleep(0.3)  # API rate limiting
                
            except Exception as e:
                logger.warning(f"Error fetching batch {current_batch}: {e}")
                continue
            
            current_start = current_end
        
        if not all_meetings:
            print("❌ No calendar data retrieved")
            return False
        
        # Store in database (clear existing data for historical fetch)
        return store_meetings_data(all_meetings, clear_existing=True, operation="historical")
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        return False

def fetch_incremental_data(days_back=1):
    """Fetch recent data incrementally (for daily cron jobs)"""
    try:
        service = GoogleCalendarService()
        
        if not service.authenticate():
            logger.error("Failed to authenticate with Google Calendar")
            return False
        
        # Calculate recent date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        print(f"🔄 INCREMENTAL FETCH: {start_date.date()} to {end_date.date()}")
        print(f"📅 Fetching last {days_back} day(s) of data")
        
        # Fetch recent data
        meetings_data = service.fetch_calendar_data(start_date, end_date)
        
        if not meetings_data:
            print("📭 No new calendar data found")
            return True  # Not an error, just no new data
        
        print(f"✅ Found {len(meetings_data)} recent events")
        
        # Store in database (don't clear existing data for incremental)
        return store_meetings_data(meetings_data, clear_existing=False, operation="incremental")
        
    except Exception as e:
        logger.error(f"Error fetching incremental data: {e}")
        return False

def store_meetings_data(meetings_data, clear_existing=False, operation="fetch"):
    """Store meetings data in database with duplicate handling"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if clear_existing:
                cursor.execute("DELETE FROM meetings")
                print(f"🗑️  Cleared existing meetings data")
            
            inserted = 0
            updated = 0
            skipped = 0
            
            print(f"💾 Processing {len(meetings_data)} events...")
            
            for i, meeting in enumerate(meetings_data):
                try:
                    # Check if event already exists (for incremental updates)
                    if not clear_existing:
                        cursor.execute("SELECT id FROM meetings WHERE event_id = %s", (meeting['event_id'],))
                        existing = cursor.fetchone()
                        
                        if existing:
                            # Update existing event
                            cursor.execute("""
                                UPDATE meetings SET 
                                    summary = %s, start_time = %s, end_time = %s, 
                                    duration_minutes = %s, attendees_count = %s,
                                    attendees_accepted = %s, attendees_declined = %s,
                                    attendees_tentative = %s, attendees_needs_action = %s,
                                    meet_link = %s, html_link = %s
                                WHERE event_id = %s
                            """, (
                                meeting['summary'], meeting['start_time'], meeting['end_time'],
                                meeting['duration_minutes'], meeting['attendees_count'],
                                meeting['attendees_accepted'], meeting['attendees_declined'],
                                meeting['attendees_tentative'], meeting['attendees_needs_action'],
                                meeting['meet_link'], meeting['html_link'], meeting['event_id']
                            ))
                            updated += 1
                            continue
                    
                    # Insert new event
                    cursor.execute("""
                        INSERT INTO meetings (
                            event_id, calendar_id, user_email, department, division, subdepartment,
                            is_manager, start_time, end_time, duration_minutes, attendees_count,
                            attendees_accepted, attendees_declined, attendees_tentative, 
                            attendees_needs_action, attendees_accepted_emails, summary, meet_link,
                            html_link, is_one_on_one, has_manager_attendee, unique_departments,
                            departments_list
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (event_id) DO NOTHING
                    """, (
                        meeting['event_id'], meeting['calendar_id'], meeting['user_email'],
                        meeting['department'], meeting['division'], meeting['subdepartment'],
                        meeting['is_manager'], meeting['start_time'], meeting['end_time'],
                        meeting['duration_minutes'], meeting['attendees_count'],
                        meeting['attendees_accepted'], meeting['attendees_declined'],
                        meeting['attendees_tentative'], meeting['attendees_needs_action'],
                        meeting['attendees_accepted_emails'], meeting['summary'],
                        meeting['meet_link'], meeting['html_link'], meeting['is_one_on_one'],
                        meeting['has_manager_attendee'], meeting['unique_departments'],
                        meeting['departments_list']
                    ))
                    
                    if cursor.rowcount > 0:
                        inserted += 1
                    else:
                        skipped += 1
                    
                    # Progress indicator for large datasets
                    if (i + 1) % 100 == 0:
                        print(f"   📝 Processed {i + 1}/{len(meetings_data)} events...")
                        
                except Exception as e:
                    skipped += 1
                    if skipped <= 5:
                        logger.error(f"Error processing meeting {meeting.get('event_id', 'unknown')}: {e}")
                    continue
            
            conn.commit()
            
            # Summary
            print(f"\n✅ {operation.upper()} COMPLETE:")
            print(f"   📝 Inserted: {inserted} new events")
            if updated > 0:
                print(f"   🔄 Updated: {updated} existing events")
            if skipped > 0:
                print(f"   ⏭️  Skipped: {skipped} events")
            
            # Database stats
            cursor.execute("SELECT COUNT(*) FROM meetings")
            total_count = cursor.fetchone()[0]
            print(f"📊 Total meetings in database: {total_count}")
            
            # Show year distribution
            cursor.execute("""
                SELECT EXTRACT(YEAR FROM start_time) as year, COUNT(*) as count
                FROM meetings 
                GROUP BY EXTRACT(YEAR FROM start_time)
                ORDER BY year DESC
                LIMIT 5
            """)
            year_stats = cursor.fetchall()
            if year_stats:
                print(f"\n📈 RECENT MEETINGS BY YEAR:")
                for year, count in year_stats:
                    print(f"  {int(year)}: {count} meetings")
        
        return True
        
    except Exception as e:
        logger.error(f"Error storing meetings data: {e}")
        return False

def main():
    """Main function with command line argument parsing"""
    print("🚀 Starting dynamic calendar data fetch...")
    
    # Validate environment variables are set
    required_env_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please ensure all database connection environment variables are set.")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='Fetch calendar data dynamically')
    parser.add_argument('--years', type=int, help='Number of years of historical data to fetch')
    parser.add_argument('--days', type=int, help='Number of days to fetch (from today backwards)')
    parser.add_argument('--daily', action='store_true', help='Fetch only today\'s data (daily update)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    try:
        fetcher = DynamicCalendarFetcher()
        
        if args.daily:
            print("📅 Performing daily update...")
            success = fetcher.fetch_daily_update()
        elif args.years:
            print(f"📚 Fetching {args.years} year(s) of historical data...")
            success = fetcher.fetch_historical_data(years=args.years)
        elif args.days:
            print(f"📅 Fetching last {args.days} days...")
            success = fetcher.fetch_recent_data(days=args.days)
        elif args.start_date and args.end_date:
            print(f"📅 Fetching data from {args.start_date} to {args.end_date}...")
            success = fetcher.fetch_date_range(args.start_date, args.end_date)
        else:
            print("❌ Please specify one of: --daily, --years, --days, or --start-date with --end-date")
            sys.exit(1)
        
        if success:
            print("✅ Data fetch completed successfully!")
        else:
            print("❌ Data fetch failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error during data fetch: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 