from flask import Flask, request, jsonify, render_template
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging

app = Flask(__name__)

TWILIO_ACCOUNT_SID = 'AC4f83e220b05a9e196c601e69705b44ab'
TWILIO_AUTH_TOKEN = 'fae80af5822f21e3e00544462caabe3d'
TWILIO_PHONE_NUMBER = '+18666421882'


client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
GPT4_API_KEY = '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'

openai.api_key = GPT4_API_KEY

def generate_greeting():
    try:
        response = openai.Completion.create(
          engine="text-davinci-002",
          prompt="Create a friendly greeting message.",
          max_tokens=50
        )
        return response.choices[0].text.strip()
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

