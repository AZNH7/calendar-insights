#!/usr/bin/env python3
"""
Using OAuth2 flow instead of service account credentials.
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
            logger.info("Authenticating with Google Calendar API...")
            
            # Load existing token if available
            if os.path.exists(TOKEN_FILE):
                logger.info("Loading existing OAuth2 token...")
                self.credentials = Credentials.from_authorized_user_file(TOKEN_FILE, CALENDAR_SCOPES)
            
            # If no valid credentials available, run OAuth flow
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing expired token...")
                    try:
                        self.credentials.refresh(Request())
                        logger.info("Token refreshed successfully")
                    except Exception as e:
                        logger.warning(f"Failed to refresh token: {e}")
                        self.credentials = None
                
                if not self.credentials:
                    logger.info("Starting OAuth2 flow for new credentials...")
                    
                    if not os.path.exists(CREDENTIALS_FILE):
                        logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
                        return False
                    
                    # Check if it's OAuth2 client credentials
                    with open(CREDENTIALS_FILE, 'r') as f:
                        cred_info = json.load(f)
                        if 'installed' not in cred_info:
                            logger.error("Credentials file is not OAuth2 client credentials")
                            return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_FILE, CALENDAR_SCOPES)
                    
                    # Run OAuth flow
                    self.credentials = flow.run_local_server(port=8080)
                    
                    # Save credentials for next run
                    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(self.credentials.to_json())
                    logger.info("OAuth2 credentials saved")
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self._authenticated = True
            logger.info("Google Calendar service authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
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
            if not attendees:
                continue

            start_info = event.get('start', {})
            end_info = event.get('end', {})
            start_time_str = start_info.get('dateTime', start_info.get('date'))
            end_time_str = end_info.get('dateTime', end_info.get('date'))

            if not start_time_str or not end_time_str:
                continue

            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Could not parse time for event {event.get('id')}")
                continue

            is_one_on_one = len(attendees) == 2
            organizer = event.get('organizer', {})

            meeting = {
                'user_email': organizer.get('email', 'unknown'),
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': (end_time - start_time).total_seconds() / 60,
                'attendees_count': len(attendees),
                'attendees_accepted': len([a for a in attendees if a.get('responseStatus') == 'accepted']),
                'attendees_declined': len([a for a in attendees if a.get('responseStatus') == 'declined']),
                'attendees_tentative': len([a for a in attendees if a.get('responseStatus') == 'tentative']),
                'attendees_needs_action': len([a for a in attendees if a.get('responseStatus') == 'needsAction']),
                'summary': event.get('summary', 'No Title'),
                'meet_link': event.get('hangoutLink'),
                'html_link': event.get('htmlLink'),
                'is_one_on_one': is_one_on_one
            }
            meeting_data.append(meeting)
        
        logger.info(f"Processed {len(meeting_data)} meetings from {len(events)} total events")
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
        logger.info(f"    Organizer: {meeting.get('organizer_email')}")
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
