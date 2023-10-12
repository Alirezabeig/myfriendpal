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

def fetch_for_prompt_next_calendar(access_token, refresh_token):
    try:
        creds = Credentials.from_authorized_user_info({
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'refresh_token': refresh_token,
            'access_token': access_token
        })
        service = build('calendar', 'v3', credentials=creds)
        
        now = datetime.utcnow().isoformat() + 'Z'
        events = service.events().list(calendarId='primary', timeMin=now, orderBy='startTime', singleEvents=True, maxResults=5).execute()
        next_google_calendar_event = [(event['summary'], event['start'].get('dateTime', event['start'].get('date')), event['end'].get('dateTime', event['end'].get('date'))) for event in events.get('items', [])]

        return next_google_calendar_event
        
    except RefreshError:
        new_access_token = get_new_access_token(refresh_token)
        return fetch_for_prompt_next_calendar(new_access_token, refresh_token)

def is_important_event(event):
    openai.api_key = gpt4_api_key
    prompt = f"Important events are interviews, team meetings, family time, birthdates or special occasions. Is the following event important or not? {event}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        prompt=prompt,
        max_tokens=20  # Reduced tokens as we're looking for a simple Yes or No.
    )
    importance_level = response['choices'][0]['text'].strip().lower()
    return "yes" in importance_level or "important" in importance_level
