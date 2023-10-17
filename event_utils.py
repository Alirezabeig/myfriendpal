# event_utils.py


import openai  # Assuming OpenAI Python package is installed
from googleapiclient.discovery import build  # Google Calendar API
from google.oauth2.credentials import Credentials
from datetime import datetime
import os
from shared_utils import get_new_access_token  # Assuming you have a get_new_access_token function in shared_utils.py
gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

def fetch_for_prompt_next_calendar(refresh_token):
    try:
        # Get a new access_token using the refresh_token
        access_token = get_new_access_token(refresh_token)
        
        # Create credentials
        creds = Credentials.from_authorized_user_info({
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'refresh_token': refresh_token,
            'access_token': access_token
        })

        # Build the Google Calendar service
        service = build('calendar', 'v3', credentials=creds)

        # Fetch events
        now = datetime.utcnow().isoformat() + 'Z'
        events = service.events().list(
            calendarId='primary',
            timeMin=now,
            orderBy='startTime',
            singleEvents=True,
            maxResults=5
        ).execute()

        next_google_calendar_event = [{'summary': event['summary'], 'start': event['start'].get('dateTime', event['start'].get('date')), 'end': event['end'].get('dateTime', event['end'].get('date'))} for event in events.get('items', [])]


        return next_google_calendar_event

    except RefreshError:
        # Handle token expiry and retry fetching the calendar
        new_access_token = get_new_access_token(refresh_token)
        return fetch_for_prompt_next_calendar(new_access_token, refresh_token)  # Retry the function using the new_access_token


