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