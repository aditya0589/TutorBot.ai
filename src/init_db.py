import os
import pymysql
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

def get_db_connection():
    ssl_config = {}
    if os.getenv('MYSQL_SSL_CA'):
        ssl_config['ca'] = os.getenv('MYSQL_SSL_CA')
    
    # If no specific CA but we are on TiDB, we might need to rely on system CAs or just try connecting.
    # For TiDB Cloud, usually SSL is required.
    
    kwargs = {
        'host': os.getenv('MYSQL_HOST'),
        'user': os.getenv('MYSQL_USER'),
        'password': os.getenv('MYSQL_PASSWORD'),
        'db': os.getenv('MYSQL_DB'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    # Only add ssl if we have a CA or if we want to enforce it (TiDB requires it)
    # If MYSQL_SSL_CA is empty, we can try passing an empty dict which enables SSL with default settings
    if os.getenv('MYSQL_HOST') and 'tidbcloud' in os.getenv('MYSQL_HOST'):
         if not ssl_config:
             # Enforce SSL for TiDB even if no CA provided (uses system CA)
             kwargs['ssl'] = {'check_hostname': False}
         else:
             kwargs['ssl'] = ssl_config

    return pymysql.connect(**kwargs)

def init_db():
    print("Connecting to database...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("Connected successfully!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Read the SQL file
    with open('database_setup.sql', 'r') as f:
        sql_content = f.read()

    # Clean up non-standard comments (-->)
    sql_content = re.sub(r'-->.*', '', sql_content)
    
    # Split into statements
    statements = sql_content.split(';')

    print("Executing schema statements...")
    for statement in statements:
        statement = statement.strip()
        if not statement:
            continue
            
        # Skip CREATE DATABASE and USE commands as we are already connected to the target DB
        if statement.upper().startswith('CREATE DATABASE') or statement.upper().startswith('USE'):
            print(f"Skipping: {statement[:50]}...")
            continue

        try:
            cursor.execute(statement)
            print(f"Executed: {statement[:50]}...")
        except Exception as e:
            # Ignore "table already exists" errors
            if "already exists" in str(e):
                print(f"Table already exists, skipping: {statement[:50]}...")
            else:
                print(f"Error executing statement: {e}")
                print(f"Statement: {statement}")

    conn.commit()
    conn.close()
    print("Database initialization completed!")

if __name__ == '__main__':
    init_db()
