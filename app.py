from flask import Flask, request, jsonify, render_template
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging

app = Flask(__name__)

TWILIO_ACCOUNT_SID = 'AC4f83e220b05a9e196c601e69705b44ab'
TWILIO_AUTH_TOKEN = 'fae80af5822f21e3e00544462caabe3d'
TWILIO_PHONE_NUMBER = '+18666421882'
GPT4_API_KEY = 'your_openai_api_key_here'  # Step 3


client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai.api_key = GPT4_API_KEY  # Step 3


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.json
        phone_number = data.get('phone_number')
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body="hey, very nice meeting you!"
        )
        logging.info(f"Message sent with ID: {message.sid}")
        return jsonify({'message': 'Message sent!'})
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return jsonify({'message': 'Failed to send message', 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))  # Fetch the port from environment variables or set to 5000
    app.run(host="0.0.0.0", port=port)  # Run the app

