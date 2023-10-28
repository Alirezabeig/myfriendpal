# google_calender.py
from flask import request
import requests
import os
from db import conn, create_connection
from calendar_utils import fetch_google_calendar_info
from flask import render_template
import json
from twilio_utils import send_sms_confirmation

from dotenv import load_dotenv
load_dotenv()

# Rest of your code

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'
conn = create_connection()

def oauth2callback():
    print("Entered oauth2callback")
    auth_code = request.args.get('code')
    phone_number = request.args.get('state')  # Assuming you passed phone_number as 'state' during OAuth2 initiation

    token_data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': 'https://www.myfriendpal.com/oauth2callback',
        'code': auth_code,
        'grant_type': 'authorization_code'
    }

    response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
    token_info = response.json()

    # Check if we have valid tokens
    access_token = token_info.get('access_token')
    refresh_token = token_info.get('refresh_token')

    if access_token and refresh_token:
        # Fetch and store Gmail ID and next Google Calendar event
        google_calendar_email, next_google_calendar_event , local_now = fetch_google_calendar_info(access_token, refresh_token)
        
        # Check if connection is closed
        if conn.closed:
            print("Connection closed, re-opening...")
            # Re-open your connection here
            # conn = psycopg2.connect( ... )
        
        # Update the database
        with conn.cursor() as cursor:  # Using 'with' ensures the cursor will be closed after use
            update_query = '''UPDATE conversations SET oauth_token = %s, google_calendar_email = %s, local_now = %s , next_google_calendar_event = %s, refresh_token = %s WHERE phone_number = %s;'''
            try:
                cursor.execute(update_query, (json.dumps(token_info), google_calendar_email, next_google_calendar_event, local_now, refresh_token, phone_number))
                conn.commit()
            except Exception as e:
                print(f"Error occurred: {e}")
                conn.rollback()
        send_sms_confirmation(phone_number, "Your Google Calendar and Gamil have been successfully authorized.")
        
    else:
        print("Failed to get access_token or refresh_token")
        send_sms_confirmation(phone_number, "Failed to authorize Google Calendar.")

    return render_template('authorization_complete.html')

    
def get_new_access_token(refresh_token):
    data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    try:
        response = requests.post('https://oauth2.googleapis.com/token', data=data)
        token_info = response.json()
        new_access_token = token_info.get('access_token')
        return new_access_token
    except Exception as e:
        logging.error(f"Failed to get new access token: {e}")
        return None

