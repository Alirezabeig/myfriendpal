
#twilio_utils.py
from flask import request, jsonify
from google.oauth2.credentials import Credentials
import logging
from db import create_connection, fetch_tokens_from_db, get_credentials_for_user

def sms_reply():
    from app import client, TWILIO_PHONE_NUMBER, check_for_calendar_keyword, generate_response

    print("SMS reply triggered")
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)
    
    print(f"User input: {user_input}, Phone number: {phone_number}")  # Debug line
    
    credentials = get_credentials_for_user(phone_number)
    calendar_keyword_found = check_for_calendar_keyword(user_input, phone_number)
    
    if not calendar_keyword_found:
        # Check if credentials exist, if not, handle as a simple SMS conversation
        if credentials:
            response_text = generate_response(user_input, phone_number, credentials)
        else:
            response_text = generate_response(user_input, phone_number)
        
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=response_text
        )

    return jsonify({'message': 'Reply sent!'})
