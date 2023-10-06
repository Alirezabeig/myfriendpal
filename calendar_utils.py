#calendar_utils.py
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from oauth2client import client
from oauth2client.client import OAuth2WebServerFlow
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError

# Set up API credentials
CALENDAR_CREDENTIALS_FILE = "client_secret.json"
CALENDAR_API_SERVICE_NAME = os.environ.get('CALENDAR_API_SERVICE_NAME')
CALENDAR_API_VERSION = os.environ.get('CALENDAR_API_VERSION')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = "https://www.myfriendpal.com/oauth2callback"

# Existing scopes for Google Calendar, add Gmail scope to it
CALENDAR_SCOPE = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/gmail.readonly']


def get_google_calendar_authorization_url(phone_number):
    print("Generating Google Calendar authorization URL...")  # Debug line
    flow = OAuth2WebServerFlow(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scope=CALENDAR_SCOPE,
        redirect_uri=REDIRECT_URI,
        access_type='offline',
        approval_prompt='force'
    )
    
    print("Type of flow:", type(flow))  # Debug line
    print("Flow object:", flow)  # Debug line
    
    # Depending on your library version, this may vary.
    # For example, you may only need to pass one argument.
    try:
        print("right before authorization")
        authorization_url = flow.step1_get_authorize_url(state=phone_number)

    except Exception as e:
        print("Error while generating URL:", e)
        return None
    
    print(f"Generated authorization URL: {authorization_url}")  # Debug line
    
    return authorization_url


def fetch_google_calendar_info(access_token, refresh_token):
    print(f"Client ID: {GOOGLE_CLIENT_ID}")
    print(f"Client Secret: {GOOGLE_CLIENT_SECRET}")
    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")

    try:
        creds = Credentials.from_authorized_user_info({
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'refresh_token': refresh_token,
            'access_token': access_token
        })
        service = build('calendar', 'v3', credentials=creds)
        
        # Fetch the email
        profile = service.calendarList().get(calendarId='primary').execute()
        google_calendar_email = profile['id']
        
        # Fetch the next event
        events = service.events().list(calendarId='primary', orderBy='startTime', singleEvents=True, maxResults=1).execute()
        next_event = events.get('items', [])[0]['summary'] if events.get('items', []) else None
        
        return google_calendar_email, next_event
    except RefreshError:
        new_access_token = get_new_access_token(refresh_token)
        return fetch_google_calendar_info(new_access_token, refresh_token)

    
def fetch_google_gmail_info(access_token):
    
    
    try:
        creds = Credentials.from_authorized_user_info({'access_token': access_token})
        service = build('gmail', 'v1', credentials=creds)

        # Fetch the user's email profile to get the email address
        profile_info = service.users().getProfile(userId='me').execute()
        google_calendar_email = profile_info['emailAddress']

        # Fetch the most recent email subject (just as an example)
        results = service.users().messages().list(userId='me', maxResults=1).execute()
        message_id = results['messages'][0]['id']
        message = service.users().messages().get(userId='me', id=message_id).execute()

        # Decode the Base64 encoded Email subject
        subject = next(header['value'] for header in message['payload']['headers'] if header['name'] == 'Subject')

        return google_calendar_email, subject
    
    except RefreshError:
        new_access_token = get_new_access_token(refresh_token)
        return fetch_google_gmail_info(new_access_token, refresh_token)

