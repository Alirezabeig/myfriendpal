from flask import Flask, request, jsonify, render_template
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import openai


app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'

twilio_account = TWILIO_ACCOUNT_SID
twilio_auth = TWILIO_AUTH_TOKEN
client = Client(twilio_account, twilio_auth)

gpt4_api_key = os.environ.get('GPT4_API_KEY')

openai.api_key = gpt4_api_key

def generate_greeting():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Replace with the actual GPT-4 model ID
            messages=[
                {"role": "system", "content": "You are a friendly greeter."},
                {"role": "user", "content": "Generate a greeting for me."}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Failed to generate message with GPT-4: {e}")
        return "Hey there, nice to meet you!"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.json
        phone_number = data.get('phone_number')
        
        greeting_message = generate_greeting()
        
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


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))  # Fetch the port from environment variables or set to 5000
    app.run(host="0.0.0.0", port=port)  # Run the app

