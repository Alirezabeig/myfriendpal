from flask import Flask, request, jsonify, render_template
from twilio.rest import Client
import requests
import os  # For fetching environment variables
from dotenv import load_dotenv  # Required to load variables from .env file

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Fetching environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
GPT4_API_ENDPOINT = os.getenv('GPT4_API_ENDPOINT')
GPT4_API_KEY = os.getenv('GPT4_API_KEY')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/')
def index():
    return render_template('ui.html')

@app.route('/sendSMS', methods=['POST'])
def send_sms():
    phone_number = request.json.get('phoneNumber')
    try:
        message = client.messages.create(
            body="Please reply with your name.",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return jsonify({"message": "SMS sent!"})
    except Exception as e:
        return jsonify({"message": "Failed to send SMS.", "error": str(e)}), 500

@app.route('/receiveSMS', methods=['POST'])
def receive_sms():
    incoming_message = request.form.get('Body')
    
    headers = {
        "Authorization": f"Bearer {GPT4_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4",  # Specifying the model
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": incoming_message}
        ]
    }
    
    # Note: The `GPT4_API_ENDPOINT` should now be the base URL.
    try:
        response = requests.post(f"{GPT4_API_ENDPOINT}/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        gpt_response = response.json()["choices"][0]["message"]["content"].strip()

        message = client.messages.create(
            body=gpt_response,
            from_=TWILIO_PHONE_NUMBER,
            to=request.form.get('From')
        )
        return "OK", 200
    except Exception as e:
        return str(e), 500


if __name__ == '__main__':
    app.run(debug=True)
