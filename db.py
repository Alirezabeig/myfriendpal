# db.py
import os
import psycopg2
from psycopg2 import OperationalError, Error
import logging
import json
import asyncpg


from dotenv import load_dotenv
load_dotenv()

is_loaded = load_dotenv()
print(f"Is .env loaded: {is_loaded}")

async def create_connection():
    print("Inside create_connection function and it is kicking")
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")

    try:
        print(f"Attempting to connect to: host={db_host} port={db_port} user={db_user} dbname={db_name}")
        connection = await asyncpg.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        await create_table(connection)
        print("Connection created ***",connection)
        return connection
        
    except OperationalError as oe:
        print(f"An OperationalError occurred: {oe}")
        logging.error(f"The full error is: {oe}")
    except Error as e:
        print(f"An explicit error occurred: {e}")
        logging.error(f"The full error is: {e}")

async def create_table(connection):

    create_table_query = '''CREATE TABLE IF NOT EXISTS conversations
    (id SERIAL PRIMARY KEY,
    phone_number TEXT NOT NULL,
    conversation_data JSONB NOT NULL,
    oauth_token JSONB,
    google_calendar_email TEXT,
    next_google_calendar_event TEXT,
    refresh_token TEXT,
    request_count INT DEFAULT 0); '''

    try:
        await connection.execute(create_table_query)
        print("table creation query executed.")
        
    except Exception as e:
        connection.rollback()
        logging.error(f"An error occurred: {e}")

async def fetch_tokens_from_db(connection, phone_number):
    try:
        
        # SQL query to fetch the access and refresh tokens based on phone number
        query = "SELECT oauth_token, refresh_token FROM conversations WHERE phone_number = %s;"
        result = await connection.fetchrow(query, phone_number)
        
        if result is None:
            return None, None
        
        return result['oauth_token'], result['refresh_token']
    except Exception as e:
        logging.error(f"An error occurred while fetching tokens: {e}")
        return None, None

async def get_credentials_for_user(phone_number):
    try:
        connection = await create_connection()
        oauth_token, refresh_token = await fetch_tokens_from_db(connection, phone_number)
        await connection.close()
        if oauth_token is None or refresh_token is None:
            print(f"No tokens found for phone number {phone_number}")
            return None, None
        return oauth_token, refresh_token
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None, None

