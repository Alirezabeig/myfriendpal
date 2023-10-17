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

def generate_response(user_input, phone_number):
    try:
        # Establish database connection
        connection = create_connection()
        if not connection:
            logging.info("Database not connected.")
            return "Database error"

        cursor = connection.cursor()
        logging.info('Generate response page accessed')

        # Initialize variables
        current_conversation = []

        fetch_query = "SELECT conversation_data, google_calendar_email, next_google_calendar_event, refresh_token FROM conversations WHERE phone_number = %s"
        cursor.execute(fetch_query, (phone_number,))
        result = cursor.fetchone()

        if result is None:
            # Insert a new row if no conversation exists for this phone number
            insert_query = "INSERT INTO conversations (phone_number, conversation_data) VALUES (%s, %s);"
            cursor.execute(insert_query, (phone_number, json.dumps([])))
            connection.commit()
        else:
            conversation_data, google_calendar_email, next_google_calendar_event, refresh_token = result
            if next_google_calendar_event:
                next_google_calendar_event = json.loads(next_google_calendar_event)
            if isinstance(conversation_data, str):
                current_conversation = json.loads(conversation_data)

        if google_calendar_email:
            next_google_calendar_event = fetch_for_prompt_next_calendar(refresh_token)
            current_conversation.append({"role": "system", "content": "Fetched new calendar events"})
            serialized_next_google_calendar_event = json.dumps(next_google_calendar_event)
            cursor.execute("UPDATE conversations SET next_google_calendar_event = %s WHERE phone_number = %s;", (serialized_next_google_calendar_event, phone_number))
            connection.commit()

        new_conversation_system = {
            "role": "system",
            "content": "Do this role play always. Your name is Pal, your were made by one engineer with love and passion and tons of coding skills. You are concise up to 30 words max. Always friendly, no need to list calendar events unless you are asked, learn about them"
        }
        new_conversation_user = {
            "role": "user",
            "content": user_input
        }
        
        current_conversation.extend([new_conversation_system, new_conversation_user])

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                'role': msg['role'],
                'content': msg['content']} for msg in current_conversation]
        )

        gpt4_reply = response['choices'][0]['message']['content'].strip()
        gpt4_reply = ' '.join(gpt4_reply.split()[:30])

        new_conversation_assistant = {
            "role": "assistant",
            "content": gpt4_reply
        }
        current_conversation.append(new_conversation_assistant)

        updated_data = json.dumps(current_conversation)
        
        update_query = "UPDATE conversations SET conversation_data = %s WHERE phone_number = %s;"
        logging.info(f"Executing SQL Query: {update_query} with phone_number = {phone_number}")  # Log the SQL query
        print("Executing SQL query")
        cursor.execute(update_query, (updated_data, phone_number))
        connection.commit()
        print("Executing - commited")
        logging.info("Transaction committed.")  

        return gpt4_reply

    except Exception as e:
        logging.error(f"An error occurred: {e}")
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

