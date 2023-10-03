
from flask import Flask, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import openai
import psycopg2
from psycopg2 import OperationalError

logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])

load_dotenv()
print("os.environ")

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

app.logger.setLevel(logging.INFO)

SCOPES = ['https://www.googleapis.com/auth/calendar.events.readonly']

CALENDAR_CREDENTIALS_FILE = "client_secret.json"

CALENDAR_API_SERVICE_NAME = os.environ.get('CALENDAR_API_SERVICE_NAME')
CALENDAR_API_VERSION = os.environ.get('CALENDAR_API_VERSION')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key

def create_connection():
    print("Environment Variables:")
    print("DB_HOST:", os.environ.get("DB_HOST"))
    print("DB_PORT:", os.environ.get("DB_PORT"))
    print("DB_USER:", os.environ.get("DB_USER"))
    print("DB_PASSWORD:", os.environ.get("DB_PASSWORD"))
    print("DB_NAME:", os.environ.get("DB_NAME"))

    try:
        connection = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME")
        )
        create_table(connection)
        return connection
    except Exception as e:
        print(f"The error '{e}' occurred")
        return None

def generate_response(user_input, phone_number):
    connection = create_connection()
    app.logger.info(f'Generating response for {phone_number}')
    print(f'Generating response for {phone_number}')
    if not connection:
        return "Could not connect to the database."

    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            
            # Load existing conversation from database
            cursor.execute("SELECT conversation_data FROM conversations WHERE phone_number = %s", (phone_number,))
            db_result = cursor.fetchone()
            
            if db_result:
                conversations[phone_number] = db_result[0]
            else:
                conversations[phone_number] = [
                    {"role": "system", "content": "...(your existing message)"}
                ]
            
            # ... (your existing code to generate GPT-4 response)
            # Assuming you've stored the GPT-4 response in a variable named 'gpt4_reply'
            
            # Save updated conversation back to the database
            update_query = '''INSERT INTO conversations(phone_number, conversation_data) VALUES(%s, %s)
                              ON CONFLICT (phone_number) DO UPDATE SET conversation_data = EXCLUDED.conversation_data;'''
            cursor.execute(update_query, (phone_number, conversations[phone_number]))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()

    return gpt4_reply  # Make sure 'gpt4_reply' is defined

    
def create_table(connection):
    try:
        cursor = connection.cursor()
        create_table_query = '''CREATE TABLE IF NOT EXISTS conversations
              (phone_number TEXT PRIMARY KEY,
               conversation_data JSONB NOT NULL); '''
        cursor.execute(create_table_query)
        connection.commit()
    except OperationalError as e:
        print(f"The error '{e}' occurred")

def get_calendar_service():
    # Load the saved credentials
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token_file:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If we have valid credentials, proceed to call Google Calendar APIs
    if creds and not creds.expired:
        return build('calendar', 'v3', credentials=creds)
    else:
        return None
        
@app.route('/')
def index():
    app.logger.info('Index page accessed')
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    app.logger.info('Inside send_message')
    print("inside_send_message")
    try:
        data = request.json
        phone_number = data.get('phone_number')
        
        # Initialize Google Calendar and get Auth URL
        google_auth_url = initialize_google_calendar()

        if google_auth_url is None:
            raise ValueError("Failed to initialize Google Calendar")

        # Create first message
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

@app.route("/headers")
def headers():
    return dict(request.headers)

def initialize_google_calendar():
    """Initialize the Google Calendar API and return Auth URL."""
    logging.info("Initializing Google Calendar")
    try:
        client_id = "1084838804894-s7bra6uila2ffshf1712qnb9lf2hk781.apps.googleusercontent.com"
        state_string = "some_random_string"
        redirect_uri = "https://www.myfriendpal.com/oauth2callback"

        auth_url = f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={client_id}&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly&state={state_string}&access_type=offline&redirect_uri={redirect_uri}"

        logging.info(f"Auth URL generated: {auth_url}")
        return auth_url
    except Exception as e:
        logging.error(f"Failed to initialize Google Calendar: {e}")
        return None

@app.route("/sms", methods=['POST'])
def sms_reply():
    app.logger.info('SMS reply triggered')
   
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)

    # Check if the user's response contains the keyword for connecting Google Calendar
    if "calendar" in user_input.lower():
        logging.info("Detected calendar keyword.")
        
        # Here, instead of generating the auth URL with InstalledAppFlow,
        # you simply call your existing initialize_google_calendar() function
        auth_url = initialize_google_calendar()
        
        if auth_url:  # Check if auth_url is not None
            logging.info(f"Generated auth URL: {auth_url}")
            
            # Send the Auth URL via SMS
            message = client.messages.create(
                to=phone_number,
                from_=TWILIO_PHONE_NUMBER,
                body=f"Please authorize Google Calendar by visiting this link: {auth_url}"
            )
        else:
            logging.error("Failed to generate auth URL.")
    else:
        # Generate a regular GPT-4 response
        response_text = generate_response(user_input, phone_number)
        
        # Send the response back to the user
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=response_text
        )

    return jsonify({'message': 'Reply sent!'})
    
@app.route("/authorize_google_calendar")
def authorize_google_calendar():
    app.logger.info('Google Calendar authorization')
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open(CALENDAR_CREDENTIALS_FILE, 'w') as token:
        token.write(creds.to_json())
    
    return "Google Calendar integration successful! You can now go back to your chat."


@app.route('/oauth2callback')
def oauth2callback():
    
    app.logger.info('Inside oauth2callback')
    logging.info(f"Received request URL: {request.url}")
    # Create the OAuth2 flow and fetch the token
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    
    # Log the credentials after they are created
    app.logger.info(f'Credentials: {creds.to_json()}')
    print("the oauth call back")

    # Save the credentials for future use
    with open('token.json', 'w') as token_file:
        token_file.write(creds.to_json())
    
    return redirect('/')

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5002))  # Fall back to 5002 for local development
    app.run(host="0.0.0.0", port=port)  # Run the app

