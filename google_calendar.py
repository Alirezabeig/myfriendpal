# google_calendar.py
from aiohttp import web, ClientSession
import os
import json
from db import create_connection
from calendar_utils import fetch_google_calendar_info
from twilio_utils import send_sms_confirmation
import asyncio

from dotenv import load_dotenv
load_dotenv()


GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
TWILIO_PHONE_NUMBER = '+18666421882'

async def oauth2callback(request):
    print("Entered oauth2callback")
    auth_code = request.query.get('code')
    phone_number = request.query.get('state')  # Assuming you passed phone_number as 'state' during OAuth2 initiation

    token_data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': 'https://www.myfriendpal.com/oauth2callback',
        'code': auth_code,
        'grant_type': 'authorization_code'
    }

    async with ClientSession() as session:
        async with session.post('https://oauth2.googleapis.com/token', data=token_data) as response:
            token_info = await response.json()
            access_token = token_info.get('access_token')
            refresh_token = token_info.get('refresh_token')

            if access_token and refresh_token:
                google_calendar_email, next_google_calendar_event, local_now = await fetch_google_calendar_info(access_token, refresh_token)
                
                connection = await create_connection()

                update_query = '''UPDATE conversations SET oauth_token = $1, google_calendar_email = $2, local_now = $3, next_google_calendar_event = $4, refresh_token = $5 WHERE phone_number = $6;'''
                
                try:
                    await connection.execute(update_query, json.dumps(token_info), google_calendar_email, local_now, next_google_calendar_event, refresh_token, phone_number)
                except Exception as e:
                    print(f"Error occurred: {e}")
                    await connection.rollback()
                finally:
                    await connection.close()
                
                await send_sms_confirmation(phone_number, "Your accounts have been successfully authorized.")
            else:
                print("Failed to get access_token or refresh_token")
                await send_sms_confirmation(phone_number, "Failed to authorize Google Calendar.")

    return web.Response(text="Authorization complete", content_type="text/html")

async def get_new_access_token(refresh_token):
    data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    async with ClientSession() as session:
        async with session.post('https://oauth2.googleapis.com/token', data=data) as response:
            token_info = await response.json()
            new_access_token = token_info.get('access_token')
            return new_access_token

# Rest of your code
