
import getpass
import mysql.connector

password = getpass.getpass("Enter your MySQL root password: ")

connection = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password=password
)

cursor = connection.cursor()
cursor.execute(
    "CREATE DATABASE IF NOT EXISTS strokespeak "
    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
)

print("StrokeSpeak database created successfully!")

cursor.close()
connection.close()
