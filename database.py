import sqlite3

def initialize_db():
    connection = sqlite3.connect('conversations.db')
    cursor = connection.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS conversations
                      (phone_number TEXT PRIMARY KEY,
                       conversation BLOB)''')
    
    connection.commit()
    connection.close()

