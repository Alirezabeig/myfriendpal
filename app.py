#app.py
import requests
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
from event_utils import fetch_for_prompt_next_calendar


import openai
from psycopg2 import OperationalError, Error
import traceback

from calendar_utils import get_google_calendar_authorization_url
from calendar_utils import fetch_google_calendar_info


load_dotenv(dotenv_path='./.env')
app, conn = load_configurations()
conn = create_connection()

is_loaded = load_dotenv()
print(f"Is .env loaded: {is_loaded}")


GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'

print("Debug in twilio_utils.py: Twilio credentials", os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
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

def fetch_next_calendar_event(refresh_token):
    new_access_token = get_new_access_token(refresh_token)
    return fetch_google_calendar_info(new_access_token, refresh_token)

def fetch_conversation_data(cursor, phone_number):
    fetch_query = "SELECT conversation_data, google_calendar_email, next_google_calendar_event, refresh_token FROM conversations WHERE phone_number = %s"
    cursor.execute(fetch_query, (phone_number,))
    result = cursor.fetchone()
    return result

def update_conversation_data(cursor, connection, phone_number, updated_data):
    update_query = "UPDATE conversations SET conversation_data = %s WHERE phone_number = %s;"
    cursor.execute(update_query, (updated_data, phone_number))
    connection.commit()

def deserialize_conversation(conversation_data):
    try:
        return json.loads(conversation_data)
    except json.JSONDecodeError:
        return []

def truncate_conversation(conversation, max_words):
    # Implement your truncate logic here
    return conversation[:max_words]

def append_to_conversation(conversation, role, content):
    new_conversation_item = {
        "role": role,
        "content": content
    }
    conversation.append(new_conversation_item)

def generate_gpt4_response(model, conversation):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{'role': msg['role'], 'content': msg['content']} for msg in conversation]
    )
    gpt4_reply = response['choices'][0]['message']['content'].strip()
    return gpt4_reply

def generate_response(user_input, phone_number):
    try:
        # Establish database connection
        connection = create_connection()
        if not connection:
            logging.info("Database not connected.")
            return "Database error"

        cursor = connection.cursor()
        logging.info('Generate response page accessed')

        result = fetch_conversation_data(cursor, phone_number)

        # Extract relevant data from the database result
        conversation_data, google_calendar_email, next_google_calendar_event, refresh_token = result

        current_conversation = deserialize_conversation(conversation_data)
        current_conversation = truncate_conversation(current_conversation, 500)

        # ... (other parts of your code)

        # Generate a response from GPT-4
        gpt4_reply = generate_gpt4_response("gpt-4", current_conversation)

        # ... (other parts of your code)

        # Update conversation data in the database
        update_conversation_data(cursor, connection, phone_number, updated_data)

        # ... (other parts of your code)

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
        
@app.route('/oauth2callback', methods=['GET'])
def handle_oauth2callback():
    print("Entered handle_oauth2callback in app.py")
    return oauth2callback()

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/pal', methods=['GET'])
def pal_page():
    return render_template('pal.html')


if __name__ == '__main__':
    print("Script is starting")
    app.debug = True
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)

