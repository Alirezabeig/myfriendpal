
#twilio_utils.py
from flask import request, jsonify
from twilio.rest import Client
import os
import openai
from dotenv import load_dotenv
import json
from truncate_conv import truncate_to_last_n_words

load_dotenv()

gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'
print("Debug in twilio_utils.py: Twilio credentials", os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def sms_reply(user_input=None, phone_number=None):
    from app import client, TWILIO_PHONE_NUMBER, check_for_calendar_keyword, generate_response

    print("SMS reply triggered")
    if user_input is None and phone_number is None:
        user_input = request.values.get('Body', None)
        phone_number = request.values.get('From', None)
        
    # Use values from request if parameters aren't provided
    if not user_input:
        user_input = request.values.get('Body', None)
    if not phone_number:
        phone_number = request.values.get('From', None)
    
    print(f"User input: {user_input}, Phone number: {phone_number}")  # Debug line
    
    calendar_keyword_found = check_for_calendar_keyword(user_input, phone_number)
    
    if not calendar_keyword_found:
        response_text = generate_response(user_input, phone_number)
        try:
            message = client.messages.create(
                to=phone_number,
                from_=TWILIO_PHONE_NUMBER,
                body=response_text
            )
            return {'status': 'success', 'message': 'Reply sent!'}
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return {'status': 'error', 'message': 'Failed to send reply!'}
    
    return {'status': 'info', 'message': 'Calendar keyword detected, no reply sent!'}
