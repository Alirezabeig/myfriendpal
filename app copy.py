
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build
from flask import Flask, request, jsonify, render_template
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import openai

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])

load_dotenv()

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

CLIENT_SECRETS_PATH = os.environ.get('CLIENT_SECRETS_PATH')
CALENDAR_API_SERVICE_NAME = os.environ.get('CALENDAR_API_SERVICE_NAME')
CALENDAR_API_VERSION = os.environ.get('CALENDAR_API_VERSION')

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key

conversations = {}  # This will hold the conversation history

def generate_response(user_input, phone_number):
    global conversations
    if phone_number not in conversations:
        conversations[phone_number] = [
            {"role": "system", "content": "1. You are like a friend. Your name is Pal . 2. You have no other name. Your language is like a friend. 3. You are built by love and prespration. 4. if someone asks you how you are built , always respond a funny and spirtual answer. Also make sure you know the name of the person you are chatting with and make sure to alway listen to their daily success and challenges and respond accordingly. 5. never answer cheesy and useles stuff 6. keep it concise to maximum 30 words"},
        ]
    conversations[phone_number].append({"role": "user", "content": user_input})
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversations[phone_number]
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
        conversations[phone_number].append({"role": "assistant", "content": gpt4_reply})
        return gpt4_reply
    except Exception as e:
        logging.error(f"Failed to generate message with GPT-4: {e}")
        return "Sorry, I couldn't understand that."

@app.route('/')
def index():
    app.logger.info('Index page accessed')
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    app.logger.info('Inside send_message')
    try:
        data = request.json
        phone_number = data.get('phone_number')
        
        greeting_message = "Hey there, I am exited to connect with you now!"  # Hardcoded greeting message
        
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

def initialize_google_calendar():
    """Initialize the Google Calendar API."""
    creds = None

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
                    "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            },
            SCOPES
        )
        creds = flow.run_local_server(port=0)
    
    with open(CALENDAR_CREDENTIALS_FILE, 'w') as token:
        token.write(creds.to_json())
    
    return build(CALENDAR_API_SERVICE_NAME, CALENDAR_API_VERSION, credentials=creds)


@app.route("/sms", methods=['POST'])
def sms_reply():
    app.logger.info('SMS reply triggered')
   
    
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)

    # Check if the user's response contains the keyword for connecting Google Calendar
    if "calendar" in user_input.lower():
        # Generate the Google Auth URL and send via SMS
        logging.info("Detected calendar keyword.")
        flow = InstalledAppFlow.from_client_secrets_file(os.environ.get('CLIENT_SECRETS_PATH'), SCOPES)
        auth_url, _ = flow.authorization_url("https://www.myfriendpal.com/oauth2callback")
        logging.info(f"Generated auth URL: {auth_url}")
        
        # Send the Auth URL via SMS
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=f"Please authorize Google Calendar by visiting this link: {auth_url}"
        )
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
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
                "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        },
        SCOPES
    )
    creds = flow.run_local_server(port=0)
    with open(CALENDAR_CREDENTIALS_FILE, 'w') as token:
        token.write(creds.to_json())
    
    return "Google Calendar integration successful! You can now go back to your chat."

@app.route('/oauth2callback')
def oauth2callback():
    app.logger.info('Inside oauth2callback')
    flow = InstalledAppFlow.from_client_secrets_file(os.environ.get('CLIENT_SECRETS_PATH'), SCOPES)
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    # Save these credentials; you'll use them to interact with the Google Calendar API
    return "Google Calendar integrated successfully!"


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))  # Fall back to 5002 for local development
    app.run(host="0.0.0.0", port=port)  # Run the app
