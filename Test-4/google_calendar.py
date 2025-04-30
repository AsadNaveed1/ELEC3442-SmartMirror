import os
import datetime
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from flask import jsonify

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    """Get a Google Calendar service object"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def get_upcoming_events(days=7, max_results=10):
    """Get upcoming events from Google Calendar"""
    try:
        service = get_calendar_service()
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        
        end_time = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=end_time,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return {"events": [], "events_by_date": {}}
            
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            if 'T' in start:
                start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                all_day = False
            else:
                start_dt = datetime.datetime.fromisoformat(f"{start}T00:00:00")
                end_dt = datetime.datetime.fromisoformat(f"{end}T23:59:59") - datetime.timedelta(days=1)
                all_day = True
            
            if all_day:
                time_str = "All day"
            else:
                time_str = start_dt.strftime("%I:%M %p") + " - " + end_dt.strftime("%I:%M %p")
            
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'all_day': all_day,
                'time_str': time_str,
                'date_str': start_dt.strftime("%b %d, %Y"),
                'colorId': event.get('colorId', '0'),
                'calendar_name': 'Primary Calendar'
            })
            
        events_by_date = {}
        for event in formatted_events:
            date_key = event['date_str']
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append(event)
            
        return {
            'events': formatted_events,
            'events_by_date': events_by_date
        }
        
    except Exception as e:
        print(f"Error getting calendar events: {e}")
        return {'events': [], 'events_by_date': {}}

def get_events_endpoint():
    """Flask endpoint to get calendar events"""
    days = 7
    max_results = 20
    
    events_data = get_upcoming_events(days, max_results)
    return jsonify(events_data)

def register_calendar_routes(app):
    """Register the calendar routes with your Flask app"""
    app.route('/calendar', methods=['GET'])(get_events_endpoint)