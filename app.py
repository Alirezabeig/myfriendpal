
import sqlite3
import json
from database import initialize_db
from flask import Flask, request, jsonify, render_template,redirect
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import openai

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key

conversations = {}  # This will hold the conversation history

initialize_db()

@app.before_request
def enforce_https():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

    
def generate_response(user_input, phone_number):
    # Load existing conversation from database
    print("generate_response called")
    conversation = load_conversation(phone_number)
    
    if conversation is None:
        conversation = [
            {"role": "system", "content": "You are like a friend. Your name is Pal . you have no other name. Your language is like a friend. You are built by love and prespration. if someone asks you how you are built , always respond a funny and spirtual answer. Also always make sure you know the name of the person you are chatting with and make sure to alway listen to their daily success and challenges and respond accordingly. Also learn from users what acitivities or what they llike to improve and always offer kind warm friendly (unlike machines) to them, like life coach friend."},
        ]
        
    conversation.append({"role": "user", "content": user_input})
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
        conversation.append({"role": "assistant", "content": gpt4_reply})
        
        # Save updated conversation back to the database
        save_conversation(phone_number, conversation)
        
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
        
        greeting_message = "Hey there, I am exited to connect with you!"  # Hardcoded greeting message
        
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


@app.route("/sms", methods=['POST'])
def sms_reply():
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)

    # Generate response using GPT-4
    gpt4_response = generate_response(user_input, phone_number)
    
    message = client.messages.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        body=gpt4_response
    )

    return jsonify({'message': 'Reply sent!'})
    
def save_conversation(phone_number, conversation):
    try:
        connection = sqlite3.connect('conversations.db')
        cursor = connection.cursor()
        
        # Serialize the conversation list to a JSON string
        serialized_conversation = json.dumps(conversation)
        
        # Insert or replace the conversation using the phone number as the key
        cursor.execute("INSERT OR REPLACE INTO conversations (phone_number, conversation) VALUES (?, ?)", (phone_number, serialized_conversation))
        
        # Commit the changes and close the connection
        connection.commit()
        connection.close()
        
        logging.info(f"Successfully saved conversation for {phone_number}: {serialized_conversation}")
    except Exception as e:
        logging.error(f"Could not save conversation: {e}")

def load_conversation(phone_number):
    connection = sqlite3.connect('conversations.db')
    cursor = connection.cursor()

    cursor.execute("SELECT conversation FROM conversations WHERE phone_number = ?", (phone_number,))
    row = cursor.fetchone()

    connection.close()

    if row:
        return json.loads(row[0])
    else:
        return None
        
@app.route('/get_conversations', methods=['GET'])
def get_all_conversations():
    connection = sqlite3.connect('conversations.db')
    cursor = connection.cursor()
    
    cursor.execute("SELECT phone_number, conversation FROM conversations")
    rows = cursor.fetchall()
    
    connection.close()
    
    conversations_dict = {}
    for row in rows:
        phone_number, conversation = row
        conversations_dict[phone_number] = json.loads(conversation)
    
    return jsonify(conversations_dict)


if __name__ == '__main__':
    
    port = int(os.environ.get("PORT", 5001))  # Fetch the port from environment variables or set to 5000
    app.run(host="0.0.0.0", port=port)
