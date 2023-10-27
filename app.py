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
from constants import const_convo
from json import dumps
from threading import Thread
load_dotenv()

import openai

from calendar_utils import fetch_google_calendar_info , get_google_calendar_authorization_url , fetch_google_gmail_info
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

app = Flask(__name__, static_url_path='/static')

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
    print("Checking for calendar keyword.**..")  # Debug line
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

def fetch_g_emails_content(refresh_token):
    new_access_token = get_new_access_token(refresh_token)
    return fetch_google_gmail_info(new_access_token, refresh_token)

def execute_query(query, params, cursor):
    cursor.execute(query, params)
    return cursor.fetchone()

def fetch_google_info(refresh_token):
    google_calendar_email, next_google_calendar_event, local_now = fetch_next_calendar_event(refresh_token)
    google_calendar_email, last_five_emails = fetch_g_emails_content(refresh_token)
    return google_calendar_email, next_google_calendar_event, local_now, last_five_emails

def update_conversation_data(conversation, role, content):
    conversation.append({"role": role, "content": content})

def generate_response(user_input=None, phone_number=None):
    print("inside_generate response")
    
    connection = create_connection()  
    cursor = connection.cursor()

    if not connection:
        return "Error: Database not connected"

    fetch_query = "SELECT conversation_data, request_count, google_calendar_email, next_google_calendar_event, refresh_token FROM conversations WHERE phone_number = %s"
    result = execute_query(fetch_query, (phone_number,), cursor)

    google_calendar_email, next_google_calendar_event, local_now, last_five_emails = None, None, None, None
    current_conversation = []
    
    if result:
        conversation_data, request_count, google_calendar_email, next_google_calendar_event, refresh_token = result
        google_calendar_email, next_google_calendar_event, local_now, last_five_emails = fetch_google_info(refresh_token)

        if request_count >= 20:
            return "Your free trial has ended, please subscribe to PAL PRO."

        current_conversation = json.loads(conversation_data) if isinstance(conversation_data, str) else conversation_data

    update_conversation_data(current_conversation, "user", user_input)
    
    if google_calendar_email and refresh_token:
        update_conversation_data(current_conversation, "system", f"my local Current Time: {local_now}")

    if last_five_emails:
        update_conversation_data(current_conversation, "system", f"These are my Last 5 Emails: {dumps(last_five_emails)}")

    if google_calendar_email and next_google_calendar_event:
        update_conversation_data(current_conversation, "system", f"mys email is {google_calendar_email}. my Next events based on my calendar are: {next_google_calendar_event}.")

    update_conversation_data(current_conversation, "system", const_convo)
    truncated = truncate_to_last_n_words(current_conversation, max_words=1000)
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=truncated
    )
    
    gpt4_reply = response['choices'][0]['message']['content'].strip()
    gpt4_reply = gpt4_reply[:1600]
    
    update_conversation_data(current_conversation, "assistant", gpt4_reply)

    updated_data = json.dumps(current_conversation)

    if result:
        update_query = "UPDATE conversations SET conversation_data = %s, request_count = request_count + 1 WHERE phone_number = %s;"
        cursor.execute(update_query, (updated_data, phone_number))
    else:
        insert_query = "INSERT INTO conversations (phone_number, conversation_data, request_count) VALUES (%s, %s, 1) ON CONFLICT (phone_number) DO NOTHING;"
        cursor.execute(insert_query, (phone_number, updated_data))
    
    connection.commit()

    return gpt4_reply




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
        logging.info(f"Message delivered with ID: {message.sid}")
        return jsonify({'message': 'Message delivered!'})
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return jsonify({'message': 'Failed to send message', 'error': str(e)})
    
@app.route('/oauth2callback', methods=['GET'])
def handle_oauth2callback():
    print("Entered handle_oauth2callback in app.py")
    return oauth2callback()

def message_all_users():
    print("Inside message_all_users")

    connection = create_connection()
    cursor = connection.cursor()

    fetch_query = "SELECT phone_number FROM conversations"
    cursor.execute(fetch_query)
    all_phone_numbers = cursor.fetchall()

    daily_user_input ="if you know my calendar and gmail, based on them, reach out to support and help. If you don't, share daily insights and lessons that are not cliche but very important from most important business and startup books and leaders. No need to mention if you have access to my information or not"

    for phone_number_tuple in all_phone_numbers:
        phone_number = phone_number_tuple[0]
        print(f"Attemptinggs to send message to {phone_number}")
        try:
            generated_response = generate_response(user_input=daily_user_input, phone_number=phone_number)
            
            message = client.messages.create(
                to=phone_number,
                from_=TWILIO_PHONE_NUMBER,
                body=generated_response
            )
            print(f"Message sent to {phone_number} with ID: {message.sid}")
        except Exception as e:
            print(f"Failed to send message to {phone_number}: {e}")

def start_jobs():
    print("inside Startss jobs")
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=message_all_users,
        trigger=IntervalTrigger(minutes=3),
        id='trigger_responses_job',
        name='Trigger responses for all users every 24 hours',
        replace_existing=True,
        max_instances=1
        )
    
    atexit.register(lambda: scheduler.shutdown())

@app.route('/pal', methods=['GET'])
def pal_page():
    return render_template('pal.html')

@app.route('/policy', methods=['GET'])
def policy_page():
    return render_template('policy.html')

@app.route('/about', methods=['GET'])
def about_page():
    return render_template('about.html')


if __name__ == '__main__':
    print("Script is starting")
    start_jobs() 
    app.debug = True
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)