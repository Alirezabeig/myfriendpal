#calendar_utils.py
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from googleapiclient.errors import HttpError
from datetime import datetime
import pytz

from oauth2client import client
from oauth2client.client import OAuth2WebServerFlow
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from shared_utils import get_new_access_token
from dotenv import load_dotenv

MAX_RETRIES = 3

load_dotenv()

# Set up API credentials
CALENDAR_CREDENTIALS_FILE = "client_secret.json"
CALENDAR_API_SERVICE_NAME = os.environ.get('CALENDAR_API_SERVICE_NAME')
CALENDAR_API_VERSION = os.environ.get('CALENDAR_API_VERSION')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = "https://www.myfriendpal.com/oauth2callback"

# Existing scopes for Google Calendar, add Gmail scope to it
CALENDAR_SCOPE = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/gmail.readonly']

def convert_utc_to_local(utc_time_str, local_timezone):
    """
    Convert a UTC time string to a local time string based on the given timezone.

    :param utc_time_str: UTC time in isoformat
    :param local_timezone: Timezone string (e.g., 'America/Los_Angeles')
    :return: Local time string in isoformat
    """
    utc_time = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
    local_time = utc_time.astimezone(pytz.timezone(local_timezone))
    return local_time.isoformat()

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


def fetch_google_calendar_info(access_token, refresh_token, api_name='calendar', api_version='v3'):
    print("Inside fetch_google_calendar_info")
    
    retry_count = 0  # Initialize retry counter
    
    while retry_count < MAX_RETRIES:
        try:
            creds = Credentials.from_authorized_user_info({
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'refresh_token': refresh_token,
                'access_token': access_token
            })
            
            service = build(api_name, api_version, credentials=creds)
            
            # Fetch the email
            profile = service.calendarList().get(calendarId='primary').execute()
            google_calendar_email = profile['id']
            google_calendar_timezone = profile['timeZone']

            # Fetch the next 5 events
            now = datetime.utcnow().isoformat() + 'Z'
            events = service.events().list(calendarId='primary', timeMin=now, 
                                           orderBy='startTime', singleEvents=True, 
                                           maxResults=5).execute()
                                           
            next_google_calendar_event = [(event['summary'], 
                                           convert_utc_to_local(event['start'].get('dateTime', event['start'].get('date')), google_calendar_timezone), 
                                           convert_utc_to_local(event['end'].get('dateTime', event['end'].get('date')), google_calendar_timezone)) 
                                          for event in events.get('items', [])]

            local_now = convert_utc_to_local(now, google_calendar_timezone)
            print(f"Local Current Time: {local_now}")
            print(f"Now: {now}")

            return google_calendar_email, next_google_calendar_event, local_now

        except RefreshError:
            print("RefreshError occurred. Retrying...")
            retry_count += 1  # Increment retry counter
            access_token = get_new_access_token(refresh_token)  # Update the access token
        
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            return None, None, None
            
        except ValueError as e:
            print(f"A value error occurred: {e}")
            return None, None, None
    
    print("Maximum retries reached. Exiting function.")
    return None, None, None

    
def fetch_google_gmail_info(new_access_token, refresh_token):
    email_list = []  # To store the last 5 emails' content and subject
    retry_count = 0  # Initialize retry counter
    
    while retry_count < MAX_RETRIES:
        try:
            # Generate new access token using refresh token
            new_access_token = get_new_access_token(refresh_token)
            
            creds = Credentials.from_authorized_user_info({
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'refresh_token': refresh_token,
                'access_token': new_access_token
            })
            
            service = build('gmail', 'v1', credentials=creds)

            # Fetch the user's email profile to get the email address
            profile_info = service.users().getProfile(userId='me').execute()
            google_calendar_email = profile_info['emailAddress']

            # Fetch the most recent 5 email IDs
            results = service.users().messages().list(userId='me', maxResults=5).execute()
            message_ids = results['messages']

            for message_data in message_ids:
                message_id = message_data['id']
                message = service.users().messages().get(userId='me', id=message_id).execute()

                # Decode the Base64 encoded Email subject and snippet (a preview of the email content)
                subject = next(header['value'] for header in message['payload']['headers'] if header['name'] == 'Subject')
                snippet = message['snippet']

                email_list.append({
                    'subject': subject,
                    'snippet': snippet
                })

            return google_calendar_email, email_list
        
        except RefreshError:
            print("RefreshError occurred. Retrying...")
            retry_count += 1  # Increment retry counter

    print("Maximum retries reached. Exiting function.")
    return None, None
