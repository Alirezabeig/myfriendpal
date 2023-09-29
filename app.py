
import MySQLdb
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


should_initialize_db = os.environ.get('INITIALIZE_DB', 'False')
print(f"Environment variable INITIALIZE_DB is set to: {os.environ.get('INITIALIZE_DB', 'Not Set')}")
print(f"should_initialize_db is set to: {should_initialize_db}")
if should_initialize_db.lower() == 'true':
    print("Before calling the initialize_db")
    initialize_db()
    print("After calling initialize_db")


app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key

conversations = {}  # This will hold the conversation history

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
            {"role": "system", "content":
            "1. You are like a friend. Your name is Pal. You have no other name. 2. Your language is like a friend. You are built by love and prespration. 3. if someone asks you how you are built , always respond a funny and spirtual answer. 4.Also always make sure you know the name of the person you are chatting with and make sure to alway listen to their daily success and challenges and respond accordingly. 5. Also learn from users what acitivities they like or they like to improve any personlaity traits or habits. 6. always offer kind warm friendly (unlike machines) to them, like life-coach friend. 7. don't get annoying by using jagon. 8. keep it concise, your responses should be maximum 30 words"},
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
    logging.info("sms_reply called")
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
        connection = get_connection()
        cursor = connection.cursor()

        serialized_conversation = json.dumps(conversation)

        cursor.execute("INSERT INTO conversations (phone_number, conversation) VALUES (%s, %s) ON DUPLICATE KEY UPDATE conversation = %s", (phone_number, serialized_conversation, serialized_conversation))

        connection.commit()
        connection.close()

        logging.info(f"Successfully saved conversation for {phone_number}: {serialized_conversation}")
    except Exception as e:
        logging.error(f"Could not save conversation: {e}")


def load_conversation(phone_number):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT conversation FROM conversations WHERE phone_number = %s", (phone_number,))
    row = cursor.fetchone()

    connection.close()

    if row:
        return json.loads(row[0])
    else:
        return None
        
@app.route('/get_conversations', methods=['GET'])
def get_all_conversations():
    connection = get_connection()
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
