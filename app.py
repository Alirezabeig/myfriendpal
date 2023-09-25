from flask import Flask, request, jsonify
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TWILIO_ACCOUNT_SID = 'AC4f83e220b05a9e196c601e69705b44ab'
TWILIO_AUTH_TOKEN = 'fae80af5822f21e3e00544462caabe3d'
TWILIO_PHONE_NUMBER = '+18666421882'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    phone_number = data.get('phone_number')
    message = client.messages.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        body="hey, very nice meeting you!"
    )
    return jsonify({'message': 'Message sent!'})

if __name__ == '__main__':
    app.run(debug=True)
