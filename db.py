import psycopg2
from psycopg2 import OperationalError

def create_connection():
    try:
        # Update 'password' with your actual pgAdmin 4 master password
        connection = psycopg2.connect(
            database="KRATOS_aicte",
            user="postgres",
            password="#Qazwsx123edc?", 
            host="127.0.0.1",
            port="5432"
        )
        print("SUCCESS: Connected to KRATOS_aicte database!")
        return connection
    except OperationalError as e:
        print(f"FATAL: The error '{e}' occurred")
        return None

# Test the connection when you run this file
if __name__ == "__main__":
    conn = create_connection()
    if conn:
        conn.close()