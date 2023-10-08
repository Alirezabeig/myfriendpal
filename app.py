
import requests
from flask import Flask, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
#from google_auth_oauthlib.flow import InstalledAppFlow
#from google.oauth2 import service_account
#from googleapiclient.discovery import build
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import json
from db import create_connection, fetch_tokens_from_db, get_credentials_for_user

from config import load_configurations
from twilio_utils import sms_reply
from google.oauth2.credentials import Credentials
from calendar_utils import fetch_google_calendar_info, fetch_google_gmail_info
from shared_utils import get_new_access_token



import openai
import psycopg2
from psycopg2 import OperationalError
import traceback
from psycopg2 import Error
from calendar_utils import get_google_calendar_authorization_url
from calendar_utils import fetch_google_calendar_info

app, conn = load_configurations()
conn = create_connection()

   

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key
conversations = {}

logging.basicConfig(level=logging.ERROR)

def check_for_calendar_keyword(user_input, phone_number):
    print("Checking for calendar keyword...")  # Debug line
    if "calendar" in user_input.lower():
        print("Calendar keyword found. Generating authorization URL...")  # Debug line
        authorization_url = get_google_calendar_authorization_url(phone_number)
        
        print(f"Sending authorization URL: {authorization_url}")  # Debug line

        # Use your existing Twilio setup to send the authorization URL
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=f"Please authorize Google Calendar access by clicking: {authorization_url}"
        )
        print(f"Authorization URL sent. Message SID: {message.sid}")  # Debug line
        return True  # Return True to indicate "calendar" was found
    else:
        print("Calendar keyword not found.")  # Debug line
        return False

@app.route('/oauth2callback', methods=['GET'])
def oauth2callback():
    print("OAUTH2CALLBACK &*&*## -- ##")
    auth_code = request.args.get('code')
    phone_number = request.args.get('state')  # Assuming you passed phone_number as 'state' during OAuth2 initiation

    token_data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': 'https://www.myfriendpal.com/oauth2callback',
        'code': auth_code,
        'grant_type': 'authorization_code'
    }
    try:
        response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        token_info = response.json()
    except Exception as e:
        logging.error(f"Error occurred: {e}")

    # Save the access token and refresh token somewhere secure for future use
    access_token = token_info.get('access_token')
    refresh_token = token_info.get('refresh_token')

    # Fetch and store Gmail ID and next Google Calendar event
    google_calendar_email, next_events = fetch_google_calendar_info(access_token, refresh_token)
    
    if next_events:
        current_conversation.append({"role": "system", "content": f"User's next 5 events are {next_events}."})

    # Check if connection is closed
    if conn.closed:
        print("Connection closed, re-opening...")
        # Re-open your connection here
        # conn = psycopg2.connect( ... )
    
    # Update the database
    with conn.cursor() as cursor:  # Using 'with' ensures the cursor will be closed after use
        update_query = '''UPDATE conversations SET oauth_token = %s, google_calendar_email = %s, next_event = %s, refresh_token = %s WHERE phone_number = %s;'''
        try:
            cursor.execute(update_query, (json.dumps(token_info), google_calendar_email, next_event, refresh_token, phone_number))
            conn.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
            conn.rollback()

    return render_template('authorization_complete.html')


def generate_response(user_input, phone_number, credentials= None):
    print("inside_generate response")
    
    connection = create_connection()  # Assuming this function returns a valid DB connection
    cursor = connection.cursor()

    # Check if tokens exist for the specific phone_number
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE phone_number = %s", (phone_number,))
    count = cursor.fetchone()[0]

    if count > 0:
        cursor.execute("SELECT refresh_token, oauth_token FROM conversations WHERE phone_number = %s", (phone_number,))
        tokens = cursor.fetchone()
        refresh_token, oauth_token = tokens  # Adjust as per your actual field names
        google_calendar_email, next_events = fetch_google_calendar_info(refresh_token, oauth_token)
    elif credentials:
        google_calendar_email, next_events = fetch_google_calendar_info(credentials)
    else:
        google_calendar_email, next_events = None, None

    if not connection:
        app.logger.info("**** *** Generate response - database not connected.")
        return "Database not connected, can't proceed."
    
    app.logger.info('generate response page accessed')
    
    try:

        update_query = ''
        fetch_query = "SELECT conversation_data, google_calendar_email, next_google_calendar_event FROM conversations WHERE phone_number = %s"

        cursor.execute(fetch_query, (phone_number,))
        result = cursor.fetchone()
        
        if result:
            conversation_data, google_calendar_email, next_google_calendar_event = result

        # Deserialize the conversation_data if it's a string
            if isinstance(conversation_data, str):
                current_conversation = json.loads(conversation_data)
            else:
                current_conversation = conversation_data
        else:
        # If no result is returned, set the variables to None or empty list
            google_calendar_email, next_google_calendar_event, current_conversation = None, None, []
        
        current_conversation.append({
            "role": "system",
            "content": "Do this role play always. Your name is Pal and you were made by one engineer, love, and passion. You should always respond like a friend, and be concise, up to 30 words."
        })
        # Add the user's message to the conversation
        current_conversation.append({"role": "user", "content": user_input})
        
        # Add Gmail and next_event to the conversation context
        if google_calendar_email and next_google_calendar_event:
            current_conversation.append({"role": "system", "content": f"User's email is {google_calendar_email}. Next event is {next_google_calendar_event}."})

        
        # Generate GPT-4 response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=current_conversation
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
        
        # Append the generated response to the conversation
        current_conversation.append({"role": "assistant", "content": gpt4_reply})
        
        # Update the database with the latest conversation
        updated_data = json.dumps(current_conversation)
        
        if result:
            update_query = "UPDATE conversations SET conversation_data = %s WHERE phone_number = %s;"
            cursor.execute(update_query, (updated_data, phone_number))

        else:
            insert_query = "INSERT INTO conversations (phone_number, conversation_data) VALUES (%s, %s);"
            cursor.execute(insert_query, (phone_number, updated_data))
        
        connection.commit()
        
        return gpt4_reply

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        logging.error(traceback.format_exc())
        return "Sorry, I couldn't understand that."
 
@app.route("/sms", methods=['POST'])
def handle_sms():
    return sms_reply()

    
@app.route('/')
def index():
    connection = create_connection()
    if not connection:
        app.logger.info("Could not connect to the database.")
    app.logger.info('Index page accessed')
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    app.logger.info('Inside send_message')
    print("inside_send_message")
    try:
        data = request.json
        phone_number = data.get('phone_number')
  
        greeting_message = f"👋🏼 Hi there, I am so excited to connect with you. What should I call you? Also read more about me here: https://www.myfriendpal.com/pal . I am getting insanely good!"

        # Send the first message
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=greeting_message
        )
        logging.info(f"Message sent with ID: {message.sid}")
        return jsonify({'message': 'Message sent!'})
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return jsonify({'message': 'Failed to send message', 'error': str(e)})
    
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
        
@app.route('/pal', methods=['GET'])
def pal_page():
    return render_template('pal.html')

if __name__ == '__main__':
    print("Script is starting")
    app.debug = True
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
