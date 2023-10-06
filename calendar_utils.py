from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os

# Set up API credentials
CALENDAR_CREDENTIALS_FILE = "client_secret.json"
CALENDAR_API_SERVICE_NAME = os.environ.get('CALENDAR_API_SERVICE_NAME', "calendar")  # Provide default value
CALENDAR_API_VERSION = os.environ.get('CALENDAR_API_VERSION', "v3")  # Provide default value
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = "https://www.myfriendpal.com/oauth2callback"
CALENDAR_SCOPE = ['https://www.googleapis.com/auth/calendar']

def get_google_calendar_authorization_url():
    print("Generating Google Calendar authorization URL...")  # Debug line
    flow = Flow.from_client_info(
        client_info={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI]
        },
        scopes=CALENDAR_SCOPE
    )
    authorization_url, state = flow.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type='offline',
        include_granted_scopes='true'
    )
    
    print(f"Generated authorization URL: {authorization_url}")  # Debug line
    
    return authorization_url, state, flow  # return state and flow for later use

def fetch_calendar_events(token_info):
    credentials = Credentials.from_authorized_user_info(token_info, CALENDAR_SCOPE)
    service = build("calendar", "v3", credentials=credentials)
    events_result = service.events().list(calendarId='primary').execute()
    events = events_result.get('items', [])
    
    return events
