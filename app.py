#app.py
from flask import Flask, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import json

from config import load_configurations
from db import create_connection
from twilio_utils import sms_reply
from google_calendar import oauth2callback
from truncate_conv import truncate_to_last_n_words
from shared_utils import get_new_access_token

import openai
import traceback

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
    
def fetch_next_calendar_event(refresh_token, timezone):
    new_access_token = get_new_access_token(refresh_token)
    email, events, local_time = fetch_google_calendar_info(new_access_token, refresh_token, timezone=timezone)
    return email, events, local_time

def generate_response(user_input, phone_number):
    print("inside_generate response")
    
    # Create a database connection
    connection = create_connection()  
    cursor = connection.cursor()
    
    # Check for valid database connection
    if not connection:
        app.logger.info("**** *** Generate response - database not connected.")
        print("Generate_response not working")
    
    app.logger.info('generate response page accessed')

    # Initialize variables
    current_conversation = []
    refresh_token = None
    timezone = None
    
    try:
        # Fetch existing data from the database
        fetch_query = "SELECT conversation_data, google_calendar_email, next_google_calendar_event, refresh_token, timezone FROM conversations WHERE phone_number = %s"
        cursor.execute(fetch_query, (phone_number,))
        result = cursor.fetchone()

        if result:
            conversation_data, google_calendar_email, next_google_calendar_event, refresh_token, timezone = result

            # Fetch next Google Calendar event using the refresh token and timezone from the database
            google_calendar_email, next_google_calendar_event, local_time = fetch_next_calendar_event(refresh_token, timezone)

            if isinstance(conversation_data, str):
                current_conversation = json.loads(conversation_data)
            else:
                current_conversation = conversation_data
        else:
            google_calendar_email, next_google_calendar_event = None, None
            
        # Add user's input to the conversation
        current_conversation.append({"role": "user", "content": user_input})
        
        # Add system content about Gmail and next_event if they exist
        if google_calendar_email and next_google_calendar_event:
            current_conversation.append({"role": "system", "content": f"User's email is {google_calendar_email}. Next event is {next_google_calendar_event}."})
        
        # Add constant conversation details
        const_convo = "Your name is Pal. You are friendly and concise, up to 50 words maximum unless necessary..."
        current_conversation.insert(0, {"role": "system", "content": const_convo})
        
        # Generate GPT-4 response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=current_conversation
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
        
        # Append GPT-4 reply to the conversation
        current_conversation.append({"role": "assistant", "content": gpt4_reply})
        
        # Update the database
        updated_data = json.dumps(current_conversation)
        
        if result:
            update_query = """UPDATE conversations 
                              SET conversation_data = %s, timezone = %s 
                              WHERE phone_number = %s;"""
            cursor.execute(update_query, (updated_data, local_time.isoformat(), phone_number))
        else:
            insert_query = """INSERT INTO conversations (phone_number, conversation_data, timezone) 
                              VALUES (%s, %s, %s);"""
            cursor.execute(insert_query, (phone_number, updated_data, local_time.isoformat()))
        
        # Commit changes and return GPT-4 reply
        connection.commit()
        
        return gpt4_reply
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred."

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
  
        greeting_message = f"👋🏼 Hi there, I am so excited to connect with you. What is your name? Also read more about me here: https://www.myfriendpal.com/pal . I am getting insanely good to help CEOs build the next big thing!"

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
    
@app.route('/oauth2callback', methods=['GET'])
def handle_oauth2callback():
    print("Entered handle_oauth2callback in app.py")
    return oauth2callback()


@app.route('/pal', methods=['GET'])
def pal_page():
    return render_template('pal.html')

if __name__ == '__main__':
    print("Script is starting")
    app.debug = True
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
