# db.py
import os
import psycopg2
from psycopg2 import OperationalError, Error

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
           conversation_data JSONB NOT NULL,
           google_oauth_token TEXT,
           google_calendar_email TEXT,
           next_event TEXT,
           refresh_token TEXT); '''

        cursor.execute(create_table_query)
        print("Table creation query executed.")
        
        connection.commit()
        print("Transaction committed.")

    except Exception as e:
        connection.rollback()
        logging.error(f"An error occurred: {e}")

