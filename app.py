import requests
from flask import Flask, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import json
import openai
import psycopg2
from psycopg2 import OperationalError
import traceback
from psycopg2 import Error
from calendar_utils import get_google_calendar_authorization_url

load_dotenv()
print("DB_HOST is:", os.environ.get("DB_HOST"))
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
app.logger.setLevel(logging.INFO)

conn = psycopg2.connect(
    host = os.environ.get("DB_HOST"),
    port = os.environ.get("DB_PORT"),
    user = os.environ.get("DB_USER"),
    password = os.environ.get("DB_PASSWORD"),
    database = os.environ.get("DB_NAME"),
)
print("Successfully connected", conn)

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

def fetch_next_google_calendar_event(credentials):
    service = build('calendar', 'v3', credentials=credentials)
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=1, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    if not events:
        return "No upcoming events found."
    else:
        return events[0]['summary']

def check_for_calendar_keyword(user_input, phone_number):
    print("Checking for calendar keyword...")  # Debug line
    if "calendar" in user_input.lower():
        print("Calendar keyword found. Generating authorization URL...")  # Debug line
        authorization_url = get_google_calendar_authorization_url() + f"&state={phone_number}"

        
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

    token_data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': 'https://www.myfriendpal.com/oauth2callback',
        'code': auth_code,
        'grant_type': 'authorization_code'
    }

    response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
    token_info = response.json()

    print("Token Info:", token_info)  # Debugging line

    # Create Google Credentials from the token information
    credentials = Credentials.from_client_info(client_id=GOOGLE_CLIENT_ID, client_secret=GOOGLE_CLIENT_SECRET, **token_info)


    # Create Google Credentials from the token information
    ##credentials = Credentials.from_authorized_user_info(token_info)

    # Fetch the Google Calendar email using the Google API
    service = build('calendar', 'v3', credentials=credentials)
    profile_info = service.calendarList().get(calendarId='primary').execute()
    google_calendar_email = profile_info['id']

    # Fetch next Google Calendar event
    next_event = fetch_next_google_calendar_event(credentials)

    # You would replace this with the phone number that was used during the OAuth2 flow
    phone_number = "the_actual_phone_number"

    # Update the database to include the google_calendar_email and next_google_calendar_event
    try:
        connection = create_connection()
        cursor = connection.cursor()
        update_query = '''UPDATE conversations SET google_calendar_email = %s, next_google_calendar_event = %s WHERE phone_number = %s;'''
        cursor.execute(update_query, (google_calendar_email, next_event, phone_number))
        connection.commit()
    except Exception as e:
        logging.error(f"An error occurred while updating the database: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

    return "Authorization complete"


def create_connection():
    print("Inside create_connection function and it is kicking")
    try:
        db_host = os.environ.get("DB_HOST")
        db_port = os.environ.get("DB_PORT")
        db_user = os.environ.get("DB_USER")
        db_password = os.environ.get("DB_PASSWORD")
        db_name = os.environ.get("DB_NAME")
        print("Attempting to connect to: host={db_host} port={db_port} user={db_user} dbname={db_name}")
        
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        create_table(connection)
        print("Connection created ***",connection)
        return connection
        
    except OperationalError as oe:
        print(f"An OperationalError occurred: {oe}")
        logging.error(f"The full error is: {oe}")
    except Error as e:
        print(f"An explicit error occurred: {e}")
        logging.error(f"The full error is: {e}")
        
def create_table(connection):
    print("Inside create_table()")
    try:
        cursor = connection.cursor()
        print("Cursor created.")
        
        create_table_query = '''CREATE TABLE IF NOT EXISTS conversations
              (id SERIAL PRIMARY KEY,
               phone_number TEXT NOT NULL,
               conversation_data JSONB NOT NULL); '''
        
        cursor.execute(create_table_query)
        print("Table creation query executed.")
        
        connection.commit()
        print("Transaction committed.")

    except Error as e:
        print(f"An explicit error occurred: {e}")

def generate_response(user_input, phone_number):
    
    print("inside_generate response")
    connection = create_connection()  # Assuming this function returns a valid DB connection
    cursor = connection.cursor()
    
    if not connection:
        app.logger.info("**** *** Genereate response - database not connected.")
        print("Generate_response not working")
    
    app.logger.info('generate response page accessed ')
    
    try:
        # Fetch existing conversation from the database based on the phone_number
        fetch_query = "SELECT conversation_data, google_calendar_email, next_google_calendar_event FROM conversations WHERE phone_number = %s;"
        cursor.execute(fetch_query, (phone_number,))
        result = cursor.fetchone()

        app.logger.info("Connected ** to Genereate response")
        print("Generate_response working")
        
        # Check type of result[0] and deserialize if needed
        if result:
            if isinstance(result[0], str):
                current_conversation = json.loads(result[0])
                conversation_data, google_calendar_email, next_google_calendar_event = result
                current_conversation.append({"role": "assistant", "content": f"The Google Calendar email associated is {google_calendar_email}. Your next event is: {next_google_calendar_event}. What would you like to do next?"})

            else:
                current_conversation = result[0]
            
        else:
            current_conversation = [{"role": "assistant", "content": "What is your name?"}]
            
        current_conversation.append({"role": "user", "content": user_input})
        
        # Generate GPT-4 response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=current_conversation
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
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

    finally:
        cursor.close()
        connection.close()

@app.route("/sms", methods=['POST'])
def sms_reply():
    print("SMS reply triggered")
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)
    
    print(f"User input: {user_input}, Phone number: {phone_number}")  # Debug line
    
    calendar_keyword_found = check_for_calendar_keyword(user_input, phone_number)
    
    if not calendar_keyword_found:
        response_text = generate_response(user_input, phone_number)
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=response_text
        )

    return jsonify({'message': 'Reply sent!'})
    
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
  
        greeting_message = f"Hi there, I am so excited to connect with you. What is your name?"

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

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')

if __name__ == '__main__':
    print("Script is starting")
    app.debug = True
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
