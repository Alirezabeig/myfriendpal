
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
from psycopg2 import Error


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

##SCOPES = ['https://www.googleapis.com/auth/calendar.events.readonly']
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
conversations = {}

logging.basicConfig(level=logging.ERROR)

def create_connection():
    print("Inside create_connection function and it is kicking")
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
        print("Connection created ***",connection)
        return connection
        
    except OperationalError as oe:
        print(f"An OperationalError occurred: {oe}")
        logging.error(f"The full error is: {oe}")
    except Error as e:
        print(f"An explicit error occurred: {e}")
        logging.error(f"The full error is: {e}")
        
def create_table(connection):
    print("Inside create_table()")
    try:
        cursor = connection.cursor()
        print("Cursor created.")
        
        create_table_query = '''CREATE TABLE IF NOT EXISTS conversations
              (id SERIAL PRIMARY KEY,
               phone_number TEXT NOT NULL,
               conversation_data JSONB NOT NULL); '''
        
        cursor.execute(create_table_query)
        print("Table creation query executed.")
        
        connection.commit()
        print("Transaction committed.")

    except Error as e:
        print(f"An explicit error occurred: {e}")

def generate_response(user_input, phone_number):
    
    print("inside_generate response")
    connection = create_connection()  # Assuming this function returns a valid DB connection
    cursor = connection.cursor()
    
    if not connection:
        app.logger.info("**** *** Genereate response - database not connected.")
        print("Generate_response not working")
    
    app.logger.info('generate response page accessed ')
    
    try:
        # Fetch existing conversation from the database based on the phone_number
        fetch_query = "SELECT conversation_data FROM conversations WHERE phone_number = %s;"
        cursor.execute(fetch_query, (phone_number,))
        result = cursor.fetchone()
        
        app.logger.info("Connected ** to Genereate response")
        print("Generate_response working")
        
        # Check type of result[0] and deserialize if needed
        if result:
            if isinstance(result[0], str):
                current_conversation = json.loads(result[0])
            else:
                current_conversation = result[0]
            print("Current_conversation_loads", current_conversation)
        else:
            current_conversation.append({"role": "user", "content": user_input})
            print("Current_conversation", current_conversation)

        current_conversation.append({"role": "user", "content": user_input})
        
        gpt4_instruction = "1. You are like a friend. Your name is Pal . 2. You have no other name. Your language is like a friend. 3. You are built by love and perspiration. 4. if someone asks you how you are built, always respond with a funny and spiritual answer."
        current_conversation.append({"role": "system", "content": gpt4_instruction})

        # Generate GPT-4 response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=current_conversation
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
        current_conversation.append({"role": "assistant", "content": gpt4_reply})
        
        # Update the database with the latest conversation
        updated_data = json.dumps(current_conversation)
        
        if result:
            update_query = "UPDATE conversations SET conversation_data = %s WHERE phone_number = %s;"
            cursor.execute(update_query, (updated_data, phone_number))
        else:
            insert_query = "INSERT INTO conversations (phone_number, conversation_data) VALUES (%s, %s);"
            cursor.execute(insert_query, (phone_number, updated_data))

        connection.commit()
        return gpt4_reply

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        logging.error(traceback.format_exc())
        return "Sorry, I couldn't understand that."

    finally:
        cursor.close()
        connection.close()

@app.route("/sms", methods=['POST'])
def sms_reply():
    print("SMS reply triggered")
    user_input = request.values.get('Body', None)
    phone_number = request.values.get('From', None)
        # Generate a regular GPT-4 response
    response_text = generate_response(user_input, phone_number)
        
        # Send the response back to the user
    message = client.messages.create(
    to=phone_number,
    from_=TWILIO_PHONE_NUMBER,
    body=response_text
        )

    return jsonify({'message': 'Reply sent!'})
    
@app.route('/')
def index():
    connection = create_connection()
    if not connection:
        app.logger.info("Could not connect to the database.")
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

if __name__ == '__main__':
    print("Script is starting")
    app.debug = True
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
