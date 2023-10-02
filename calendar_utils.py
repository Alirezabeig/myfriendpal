
# calendar_utils.py
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import logging

logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    # Load the saved credentials
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token_file:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If we have valid credentials, proceed to call Google Calendar APIs
    if creds and not creds.expired:
        return build('calendar', 'v3', credentials=creds)
    else:
        return None
        
def initialize_google_calendar():
    """Initialize the Google Calendar API and return Auth URL."""
    logging.info("Initializing Google Calendar")
    try:
        ##SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        auth_url, _ = flow.authorization_url()
        
        logging.info(f"Auth URL generated: {auth_url}")
        return auth_url
    except Exception as e:
        logging.error(f"Failed to initialize Google Calendar: {e}")
        return None
