from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build
from flask import Flask, request, jsonify, render_template
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import openai

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CALENDAR_CREDENTIALS_FILE = 'calendar-credentials.json'  # Create this file
CALENDAR_API_SERVICE_NAME = 'calendar'
CALENDAR_API_VERSION = 'v3'

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
    return render_template('index.html')


@app.route('/send_message', methods=['POST'])
def send_message():
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

    if os.path.exists(CALENDAR_CREDENTIALS_FILE):
        creds = service_account.Credentials.from_service_account_file(
            CALENDAR_CREDENTIALS_FILE, scopes=SCOPES)
    
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": "1084838804894-s7bra6uila2ffshf1712qnb9lf2hk781.apps.googleusercontent.com",
                    "client_secret": "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",
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
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)

    # Check if the user's response contains the keyword for connecting Google Calendar
    if "calendar" in user_input.lower():
        # Redirect the user to Google OAuth consent screen
        return redirect(url_for('authorize_google_calendar'))
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
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": "1084838804894-s7bra6uila2ffshf1712qnb9lf2hk781.apps.googleusercontent.com",
                "client_secret": "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",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        },
        SCOPES
    )
    creds = flow.run_local_server(port=0)
    with open(CALENDAR_CREDENTIALS_FILE, 'w') as token:
        token.write(creds.to_json())
    
    return "Google Calendar integration successful! You can now go back to your chat."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # 5000 is just a common default for local testing

  # Fetch the port from environment variables or set to 5000
    app.run(host="0.0.0.0", port=port)  # Run the app

