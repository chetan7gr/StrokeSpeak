
import getpass
import mysql.connector

try:
    password = getpass.getpass("Enter your MySQL root password: ")

    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password=password
    )

    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")

    version = cursor.fetchone()
    print("MySQL connection successful!")
    print("MySQL version:", version[0])

    cursor.close()
    connection.close()

except mysql.connector.Error as error:
    print("MySQL connection failed:", error)
