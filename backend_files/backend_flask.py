from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="aishamysql2023",
        database="hotel_handling"
    )

def fetch_all_data():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
        
    hotel_details = []
    cursor.execute('''
        SELECT hotel_name, hotel_city, review_score, hotel_price, hotel_pic
        FROM hotel_info
        ''')
    result = cursor.fetchall()
    if result:
        hotel_details.extend(result)
        
    cursor.close()
    connection.close()
         
    print("Sending response:", hotel_details)  # Debug response data
    return hotel_details