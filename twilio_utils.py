
from flask import request, jsonify
from app import client, TWILIO_PHONE_NUMBER, check_for_calendar_keyword, generate_response

def sms_reply():
    print("SMS reply triggered")
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)
    
    print(f"User input: {user_input}, Phone number: {phone_number}")  # Debug line
    
    calendar_keyword_found = check_for_calendar_keyword(user_input, phone_number)
    
    if not calendar_keyword_found:
        response_text = generate_response(user_input, phone_number)
        message = client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=response_text
        )

    return jsonify({'message': 'Reply sent!'})
