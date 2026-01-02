import mysql.connector
from mysql.connector import Error


def create_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost", user="root", password="yourpassword", database="fsr_data"
        )
        return connection
    except Error as e:
        print("Error connecting to MySQL:", e)
        return None


def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS force_readings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                force_value FLOAT
            )
        """)
        connection.commit()
    except Error as e:
        print("Error creating table:", e)


def insert_force(connection, value):
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO force_readings (force_value) VALUES (%s)", (value,))
        connection.commit()
    except Error as e:
        print("Error inserting data:", e)
