
from flask import Flask, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
#from google_auth_oauthlib.flow import InstalledAppFlow
#from google.oauth2 import service_account
#from googleapiclient.discovery import build
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import json
import openai
import psycopg2
from psycopg2 import OperationalError
import traceback

logging.basicConfig(level=logging.DEBUG)

load_dotenv()
print("DB_HOST is:", os.environ.get("DB_HOST"))
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
app.logger.setLevel(logging.INFO)

conn = psycopg2.connect(
    host = os.environ.get("DB_HOST"),
    port = os.environ.get("DB_PORT"),
    user = os.environ.get("DB_USER"),
    password = os.environ.get("DB_PASSWORD"),
    database = os.environ.get("DB_NAME"),
)
print("Successfully connected", conn)

#SCOPES = ['https://www.googleapis.com/auth/calendar.events.readonly']
#CALENDAR_CREDENTIALS_FILE = "client_secret.json"
#
#CALENDAR_API_SERVICE_NAME = os.environ.get('CALENDAR_API_SERVICE_NAME')
#CALENDAR_API_VERSION = os.environ.get('CALENDAR_API_VERSION')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = '+18666421882'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key

##conversations = {}

def create_connection():
    print("Into the create_connection function and it is kicking")
    try:
        db_host = os.environ.get("DB_HOST")
        db_port = os.environ.get("DB_PORT")
        db_user = os.environ.get("DB_USER")
        db_password = os.environ.get("DB_PASSWORD")
        db_name = os.environ.get("DB_NAME")
        print("Attempting to connect to: host={db_host} port={db_port} user={db_user} dbname={db_name}")
        
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        create_table(connection)
        return connection
    except OperationalError as e:
        print(f"Operational error occurred: {e}")
        logging.error(f"The full error is: {e}")
        return None

    except DatabaseError as e:
        print(f"Database error occurred: {e}")
        logging.error(f"The full error is: {e}")
        return None

    except Error as e:
        print(f"An explicit error occurred: {e}")
        logging.error(f"The full error is: {e}")
        return None
        
def create_table(connection):
    try:
        cursor = connection.cursor()
        # Change this SQL query based on your requirements
        create_table_query = '''CREATE TABLE IF NOT EXISTS conversations
              (id SERIAL PRIMARY KEY,
               phone_number TEXT NOT NULL,
               conversation_data JSONB NOT NULL); '''
        cursor.execute(create_table_query)
        connection.commit()
    except OperationalError as e:
        print(f"Operational error occurred: {e}")
        logging.error(f"The full error is: {e}")

    except DatabaseError as e:
        print(f"Database error occurred: {e}")
        logging.error(f"The full error is: {e}")

    except Error as e:
        print(f"An explicit error occurred: {e}")
        logging.error(f"The full error is: {e}")

def generate_response(user_input, phone_number, connection):
    cursor = connection.cursor()
    # Check if the conversation exists in the database
    cursor.execute("SELECT conversation_data FROM conversations WHERE phone_number = %s", (phone_number,))
    row = cursor.fetchone()
    if row is None:
        initial_conversation = [
            {"role": "system", "content": "hi there, nice meeting you."}
        ]
        cursor.execute("INSERT INTO conversations (phone_number, conversation_data) VALUES (%s, %s)", (phone_number, json.dumps(initial_conversation)))
        connection.commit()
        conversation_history = initial_conversation
    else:
        conversation_history = json.loads(row[0])
        
    # Append the new user message
    conversation_history.append({"role": "user", "content": user_input})
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation_history
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
        
        # Append GPT-4 reply to the conversation history
        conversation_history.append({"role": "assistant", "content": gpt4_reply})
        
        # Update the database record
        cursor.execute("UPDATE conversations SET conversation_data = %s WHERE phone_number = %s", (json.dumps(conversation_history), phone_number))
        connection.commit()
        
        return gpt4_reply
    except Exception as e:
        logging.error(f"Failed to generate message with GPT-4: {e}")
        return "Sorry, I couldn't understand that."



@app.route('/')
def index():
    print("The website is up and running")
    app.logger.info('Index page accessed')
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    app.logger.info('Inside send_message')
    print("inside_send_message")
    try:
        data = request.json
        phone_number = data.get('phone_number')
  
        greeting_message = f"Hi there, I am so excited to connect with you. What is your name?"

        # Send the first message
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

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route("/sms", methods=['POST'])
def sms_reply():
    app.logger.info('SMS reply triggered')
   
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)

    # Use the database connection
    connection = create_connection()
    if connection is None:
        return jsonify({'message': 'Database connection failed'})
    # Generate a regular GPT-4 response
    response_text = generate_response(user_input, phone_number, connection)
        
    # Send the response back to the user
    message = client.messages.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        body=response_text
    )
    connection.close()
    return jsonify({'message': 'Reply sent!'})

if __name__ == '__main__':
    print("Script is starting")
    app.debug = True
    port = int(os.environ.get("PORT", 5002))  # Fall back to 5002 for local development
    app.run(host="0.0.0.0", port=port)  # Run the app

