import sqlite3
import os

def get_connection():
    return sqlite3.connect("conversations.db")

def initialize_db():
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS conversations
                      (phone_number TEXT PRIMARY KEY,
                       conversation TEXT)''')
    
    connection.commit()
    connection.close()
