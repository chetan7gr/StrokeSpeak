
from pathlib import Path
import os

import mysql.connector
from dotenv import load_dotenv

# Load the .env file from the backend folder
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path, override=True)

print("Environment file found:", env_path.is_file())
print("Database:", os.getenv("DB_NAME"))
print("Username:", os.getenv("DB_USER"))
print("Password loaded:", bool(os.getenv("DB_PASSWORD")))

try:
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "strokespeak"),
    )

    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE()")
    print("Connected database:", cursor.fetchone()[0])
    print("StrokeSpeak database connection successful!")

    cursor.close()
    connection.close()

except mysql.connector.Error as error:
    print("Database connection failed:", error)
