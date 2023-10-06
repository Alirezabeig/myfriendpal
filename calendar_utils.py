#calendar_utils
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from oauth2client import client
from oauth2client.client import OAuth2WebServerFlow

# Set up API credentials


CALENDAR_CREDENTIALS_FILE = "client_secret.json"
CALENDAR_API_SERVICE_NAME = os.environ.get('CALENDAR_API_SERVICE_NAME')
CALENDAR_API_VERSION = os.environ.get('CALENDAR_API_VERSION')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
CALENDAR_SCOPE = ['https://www.googleapis.com/auth/calendar']

def get_google_calendar_authorization_url():
    print("Generating Google Calendar authorization URL...")  # Debug line
    flow = OAuth2WebServerFlow(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scope=CALENDAR_SCOPE,
        redirect_uri=REDIRECT_URI
    )
    
    print("Type of flow:", type(flow))  # Debug line
    print("Flow object:", flow)  # Debug line
    
    # Depending on your library version, this may vary.
    # For example, you may only need to pass one argument.
    try:
        print("right before authorization")
        authorization_url = flow.step1_get_authorize_url()

    except Exception as e:
        print("Error while generating URL:", e)
        return None
    
    print(f"Generated authorization URL: {authorization_url}")  # Debug line
    
    return authorization_url

def fetch_calendar_events(credentials):
    service = build("calendar", "v3", credentials=credentials)
    events_result = service.events().list(calendarId='primary').execute()
    events = events_result.get('items', [])
    return events
