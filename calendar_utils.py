
# calendar_utils.py
from googleapiclient.discovery import build
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/calendar.events.readonly']

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token_file:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if creds and not creds.expired:
        return build('calendar', 'v3', credentials=creds)
    else:
        return None

def initialize_google_calendar():
    client_id = "1084838804894-s7bra6uila2ffshf1712qnb9lf2hk781.apps.googleusercontent.com"
    state_string = "some_random_string"
    redirect_uri = "https://www.myfriendpal.com/oauth2callback"

    auth_url = f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={client_id}&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly&state={state_string}&access_type=offline&redirect_uri={redirect_uri}"

    return auth_url
    
def authorize_google_calendar():
    app.logger.info('Google Calendar authorization')
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open(CALENDAR_CREDENTIALS_FILE, 'w') as token:
        token.write(creds.to_json())
    
    return "Google Calendar integration successful! You can now go back to your chat."
