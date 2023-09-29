# database.py

import MySQLdb
import os

def get_connection():
    return MySQLdb.connect(
        host=os.environ.get('DB_HOST', "database-1.cteawawmvpgi.us-east-1.rds.amazonaws.com"),  # Fallback to hardcoded host
        user=os.environ.get('DB_USER', "admin"),  # Fallback to hardcoded user
        passwd=os.environ.get('DB_PASSWORD', "fhc85C75*Dfj#$jf5"),  # Fallback to hardcoded password
        db=os.environ.get('DB_NAME', "conversations")  # Fallback to hardcoded db name
    )

def initialize_db():
    connection = get_connection()
    cursor = connection.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS conversations
                      (phone_number VARCHAR(15) PRIMARY KEY,
                       conversation TEXT)''')
    
    # Commit the changes and close the connection
    connection.commit()
    connection.close()
