#!/usr/bin/env python3
"""
Production-ready Google Calendar service using OAuth2 authentication.
This version uses OAuth2 flow instead of service account credentials.
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Scopes required for accessing Google Calendar
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# File paths
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials/service-account.json')
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials/token.json')

class GoogleCalendarService:
    """Production Google Calendar service using OAuth2"""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        self._authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API using OAuth2"""
        try:
            logger.info("Authenticating with Google Calendar API using OAuth2...")
            
            # Load existing token if available
            if os.path.exists(TOKEN_FILE):
                logger.info("Loading existing OAuth2 token...")
                self.credentials = Credentials.from_authorized_user_file(TOKEN_FILE, CALENDAR_SCOPES)
            
            # If no valid credentials available, check if we can refresh
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing expired token...")
                    try:
                        self.credentials.refresh(Request())
                        logger.info("Token refreshed successfully")
                        
                        # Save refreshed token
                        with open(TOKEN_FILE, 'w') as token:
                            token.write(self.credentials.to_json())
                        
                    except Exception as e:
                        logger.warning(f"Failed to refresh token: {e}")
                        self.credentials = None
                
                if not self.credentials:
                    logger.error("No valid OAuth2 credentials available")
                    logger.info("Please run OAuth2 flow to get new credentials")
                    return False
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self._authenticated = True
            logger.info("Google Calendar service authenticated successfully with OAuth2")
            return True
            
        except Exception as e:
            logger.error(f"OAuth2 authentication failed: {e}")
            return False
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all accessible calendars"""
        if not self._authenticated:
            if not self.authenticate():
                return []
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            logger.info(f"Found {len(calendars)} calendars")
            return calendars
        except HttpError as e:
            logger.error(f"Error listing calendars: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing calendars: {e}")
            return []
    
    def get_events(self, 
                   calendar_id: str = 'primary',
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   max_results: int = 100) -> List[Dict[str, Any]]:
        """Get calendar events for specified date range"""
        if not self._authenticated:
            if not self.authenticate():
                return []
        
        try:
            # Default to last 30 days if no dates provided
            if not end_date:
                end_date = datetime.now(timezone.utc)
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            logger.info(f"Fetching events from {calendar_id} between {start_date} and {end_date}")
            
            # Ensure dates are properly formatted for the API
            time_min = start_date.isoformat() if hasattr(start_date, 'isoformat') else start_date
            time_max = end_date.isoformat() if hasattr(end_date, 'isoformat') else end_date
            
            # Add 'Z' suffix if timezone info is missing
            if not time_min.endswith('Z') and '+' not in time_min and time_min.count(':') == 2:
                time_min += 'Z'
            if not time_max.endswith('Z') and '+' not in time_max and time_max.count(':') == 2:
                time_max += 'Z'
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Found {len(events)} events")
            
            # Process events to extract useful information
            processed_events = []
            for event in events:
                processed_event = {
                    'id': event.get('id'),
                    'summary': event.get('summary', 'No Title'),
                    'description': event.get('description', ''),
                    'start': event.get('start', {}),
                    'end': event.get('end', {}),
                    'organizer': event.get('organizer', {}),
                    'attendees': event.get('attendees', []),
                    'hangout_link': event.get('hangoutLink'),
                    'html_link': event.get('htmlLink'),
                    'location': event.get('location', ''),
                    'created': event.get('created'),
                    'updated': event.get('updated'),
                    'status': event.get('status'),
                    'conference_data': event.get('conferenceData', {})
                }
                processed_events.append(processed_event)
            
            return processed_events
            
        except HttpError as e:
            logger.error(f"Error fetching events: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching events: {e}")
            return []
    
    def get_meeting_data(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Get meeting data with enhanced processing for analytics"""
        events = self.get_events(
            start_date=datetime.now(timezone.utc) - timedelta(days=days_back),
            end_date=datetime.now(timezone.utc)
        )
        
        meeting_data = []
        for event in events:
            attendees = event.get('attendees', [])
            if len(attendees) > 1: 
                # Start and end times
                start_info = event.get('start', {})
                end_info = event.get('end', {})
                
                start_time = start_info.get('dateTime', start_info.get('date'))
                end_time = end_info.get('dateTime', end_info.get('date'))
                
                duration_minutes = None
                if start_time and end_time:
                    try:
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        duration_minutes = (end_dt - start_dt).total_seconds() / 60
                    except Exception as e:
                        logger.warning(f"Could not calculate duration for event {event.get('id')}: {e}")
                
                # Attendee info
                attendee_emails = []
                attendee_count = len(attendees)
                for attendee in attendees:
                    email = attendee.get('email')
                    if email:
                        attendee_emails.append(email)
                
                meeting_info = {
                    'event_id': event.get('id'),
                    'title': event.get('summary', 'No Title'),
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_minutes': duration_minutes,
                    'organizer_email': event.get('organizer', {}).get('email'),
                    'attendee_count': attendee_count,
                    'attendee_emails': attendee_emails,
                    'hangout_link': event.get('hangout_link'),
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'created': event.get('created'),
                    'updated': event.get('updated'),
                    'status': event.get('status'),
                    'conference_data': event.get('conference_data')
                }
                meeting_data.append(meeting_info)
        
        logger.info(f"Processed {len(meeting_data)} meetings from {len(events)} total events")
        return meeting_data
    
    def fetch_calendar_data(self, start_date, end_date):
        """Fetch calendar data for historical data fetching - compatible with database format"""
        events = self.get_events(
            start_date=start_date,
            end_date=end_date,
            max_results=2500  # Higher limit for historical fetching
        )
        
        meeting_data = []
        for event in events:
            # Process all events, not just meetings with multiple attendees
            attendees = event.get('attendees', [])
            
            # Extract start and end times
            start_info = event.get('start', {})
            end_info = event.get('end', {})
            
            start_time = start_info.get('dateTime', start_info.get('date'))
            end_time = end_info.get('dateTime', end_info.get('date'))
            
            if not start_time or not end_time:
                continue  # Skip events without proper time information
            
            # Calculate duration
            duration_minutes = None
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            except Exception as e:
                logger.warning(f"Could not calculate duration for event {event.get('id')}: {e}")
                continue
            
            # Extract organizer info
            organizer = event.get('organizer', {})
            organizer_email = organizer.get('email', 'unknown@domain.com')
            
            # Count attendees by status
            attendees_accepted = 0
            attendees_declined = 0
            attendees_tentative = 0
            attendees_needs_action = 0
            attendees_accepted_emails = []
            
            for attendee in attendees:
                response_status = attendee.get('responseStatus', 'needsAction')
                if response_status == 'accepted':
                    attendees_accepted += 1
                    attendees_accepted_emails.append(attendee.get('email', ''))
                elif response_status == 'declined':
                    attendees_declined += 1
                elif response_status == 'tentative':
                    attendees_tentative += 1
                elif response_status == 'needsAction':
                    attendees_needs_action += 1
            
            # Determine meeting characteristics
            attendees_count = len(attendees)
            is_one_on_one = attendees_count == 2
            meet_link = event.get('hangoutLink', '')
            if not meet_link and event.get('conferenceData'):
                # Try to extract meet link from conference data
                entry_points = event.get('conferenceData', {}).get('entryPoints', [])
                for entry in entry_points:
                    if entry.get('entryPointType') == 'video':
                        meet_link = entry.get('uri', '')
                        break
            
            # Database-compatible format
            meeting_record = {
                'event_id': event.get('id'),
                'calendar_id': 'primary',  # Default calendar
                'organizer_email': organizer_email,
                'user_email': organizer_email,  # Use organizer as user for now
                'summary': event.get('summary', 'No Title'),
                'start_time': start_dt,
                'end_time': end_dt,
                'duration_minutes': duration_minutes,
                'attendees_count': attendees_count,
                'attendees_accepted': attendees_accepted,
                'attendees_declined': attendees_declined,
                'attendees_tentative': attendees_tentative,
                'attendees_needs_action': attendees_needs_action,
                'attendees_accepted_emails': ','.join(attendees_accepted_emails),
                'meet_link': meet_link,
                'html_link': event.get('htmlLink', ''),
                'is_one_on_one': is_one_on_one,
                'has_manager_attendee': False,  # Would need additional logic to determine
                'unique_departments': 1,  # Default
                'departments_list': 'Unknown',  # Would need user mapping
                'department': 'Unknown',
                'division': 'Unknown',
                'subdepartment': 'Unknown',
                'is_manager': False
            }
            meeting_data.append(meeting_record)
        
        logger.info(f"Fetched {len(meeting_data)} meetings for database storage")
        return meeting_data

def test_oauth2_calendar_service():
    """Test the OAuth2 calendar service"""
    logger.info("=== Testing OAuth2 Calendar Service ===")
    
    # Initialize service
    calendar_service = GoogleCalendarService()
    
    # Test authentication
    if not calendar_service.authenticate():
        logger.error("❌ Authentication failed")
        return False
    
    # Test calendar list
    calendars = calendar_service.list_calendars()
    if not calendars:
        logger.error("❌ No calendars found")
        return False
    
    logger.info(f"✅ Found {len(calendars)} calendars")
    for calendar in calendars[:3]:
        logger.info(f"  - {calendar.get('summary')} ({calendar.get('accessRole')})")
    
    # Test events fetching
    start_date = datetime.now(timezone.utc) - timedelta(days=7)
    end_date = datetime.now(timezone.utc)
    events = calendar_service.get_events(start_date=start_date, end_date=end_date)
    logger.info(f"✅ Found {len(events)} events in last 7 days")
    
    # Test meeting data processing
    meetings = calendar_service.get_meeting_data(days_back=7)
    logger.info(f"✅ Processed {len(meetings)} meetings from events")
    
    for meeting in meetings[:3]:
        logger.info(f"  Meeting: {meeting.get('title')}")
        logger.info(f"    Attendees: {meeting.get('attendee_count')}")
        logger.info(f"    Duration: {meeting.get('duration_minutes')} minutes")
    
    return True

if __name__ == '__main__':
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 Testing OAuth2 Google Calendar Service")
    success = test_oauth2_calendar_service()
    
    if success:
        logger.info("🎉 All tests passed! OAuth2 calendar service is working.")
    else:
        logger.error("❌ Tests failed.")
