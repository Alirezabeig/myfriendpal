#calendar_utils
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

# Set up API credentials

CALENDAR_CREDENTIALS_FILE = "client_secret.json"
CALENDAR_API_SERVICE_NAME = 'calendar'
CALENDAR_API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_calendar_authorization_url():
    flow = InstalledAppFlow.from_client_secrets_file(
        CALENDAR_CREDENTIALS_FILE, SCOPES)
    authorization_url, _ = flow.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type='offline',
        include_granted_scopes='true')
    
    return authorization_url

def fetch_calendar_events(credentials):
    service = build("calendar", "v3", credentials=credentials)
    events_result = service.events().list(calendarId='primary').execute()
    events = events_result.get('items', [])
    return events
