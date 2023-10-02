from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import logging
import os

# Import the functions from the separated files
from calendar_utils import get_calendar_service, initialize_google_calendar
from gpt4_utils import generate_response
from twilio.rest import Client

logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/')
def index():
    print("hello world!")
    app.logger.info('Index page accessed')
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.json
        phone_number = data.get('phone_number')
        google_auth_url = initialize_google_calendar()
        
        if google_auth_url is None:
            raise ValueError("Failed to initialize Google Calendar")
        
        greeting_message = f"Hi there, follow this link to connect your Google Calendar {google_auth_url}"
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=greeting_message
        )
        return jsonify({'message': 'Message sent!'})
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return jsonify({'message': 'Failed to send message', 'error': str(e)})

@app.route("/sms", methods=['POST'])
def sms_reply():
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)
    
    if "calendar" in user_input.lower():
        auth_url = initialize_google_calendar()
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=f"Please authorize Google Calendar by visiting this link: {auth_url}"
        )
    else:
        response_text = generate_response(user_input, phone_number)
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=response_text
        )
    return jsonify({'message': 'Reply sent!'})

# Additional routes like '/authorize_google_calendar' and '/oauth2callback' can be kept as-is

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5002))  # Fall back to 5002 for local development
    app.run(host="0.0.0.0", port=port)  # Run the app
