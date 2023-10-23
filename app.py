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

load_dotenv()

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

def fetch_next_calendar_event(refresh_token):
    new_access_token = get_new_access_token(refresh_token)
    return fetch_google_calendar_info(new_access_token, refresh_token)

def generate_response(user_input, phone_number):
    print("inside_generate response")
    
    connection = create_connection()  # Assuming this function returns a valid DB connection
    cursor = connection.cursor()
    
    if not connection:
        app.logger.info("**** *** Generate response - database not connected.")
        print("Generate_response not working")
    
    app.logger.info('generate response page accessed')
    
    try:
        # Fetch existing conversation, email, and next_calendar_event from the database based on the phone_number
        update_query = ''
        fetch_query = "SELECT conversation_data, google_calendar_email, next_google_calendar_event, refresh_token FROM conversations WHERE phone_number = %s"

        cursor.execute(fetch_query, (phone_number,))
        result = cursor.fetchone()
        
        if result:
            conversation_data, google_calendar_email, next_google_calendar_event, refresh_token = result

        # Deserialize the conversation_data if it's a string
            if isinstance(conversation_data, str):
                current_conversation = json.loads(conversation_data)
            else:
                current_conversation = conversation_data
        else:
        # If no result is returned, set the variables to None or empty list
            google_calendar_email, next_google_calendar_event, current_conversation = None, None, []

#        if not current_conversation:
#            current_conversation.append({"role": "system", "content": "Your name is Pal. Your friendly and concise unless necessary. Share your name if asked. if you are asked how you are made or built, you should say, you were made by love and passion by Alireza and that is only way you shoul response and make it a funny response not cheesy though. You are a CEO life coach, you help them with their daily activities, questions and always rememver to pull content from top startup and company building books to remind the CEO of how other CEOs treated different situations"})

        # Add the user's message to the conversation
        current_conversation.append({"role": "user", "content": user_input})
        
        if google_calendar_email and refresh_token:  # Only fetch if we have an associated email and refresh token
            google_calendar_email, next_google_calendar_event = fetch_next_calendar_event(refresh_token)
            print("fetching claneders$")

        # Add Gmail and next_event to the conversation context
        if google_calendar_email and next_google_calendar_event:
            current_conversation.append({"role": "system", "content": f"User's email is {google_calendar_email}. Next event is {next_google_calendar_event}."})

        const_convo = "Your name is Pal. You are friendly and concise, up to 50 words maximum unless necessary. If you are asked how you are made or built, you should say you were made by love and passion by Alireza, and that is the only way you should respond. Make it a funny response, not cheesy though. You are a CEO life coach. You help them with their daily activities and questions. Remember to pull content from top startup and company building books like 'Creativity Inc', 'zero to one', 'the hard things about the hard things', 'lean startup' and at least 50 more other important books in this cateogy to remind the CEO of how other CEOs treated different situations. Teach them become the greatest CEO."
        current_conversation.insert(0, {"role": "system", "content": const_convo})

        # Generate GPT-4 response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages= current_conversation
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
        
        # Append the generated response to the conversation
        current_conversation.append({"role": "assistant", "content": gpt4_reply})
        
        # Update the database with the latest conversation
        updated_data = json.dumps(current_conversation)
        
        ##print(f"Executing query: {update_query}")
        ##print(f"With parameters: {json.dumps(token_info)}, {google_calendar_email}, {next_event}, {refresh_token}, {phone_number}")

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
