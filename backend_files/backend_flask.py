from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from recommender2 import recommend_hotels

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

def fetch_recommend_data(df_recommendations):
    hotel_names = df_recommendations['hotel_name'].tolist()
    print("hoetls:", hotel_names)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
        
    hotel_details = []
    for hotel_name in hotel_names:
        cursor.execute('''
            SELECT hotel_name, hotel_city, review_score, hotel_price, hotel_pic
            FROM hotel_info
            WHERE hotel_name = %s
            ''', (hotel_name,))
        result = cursor.fetchone()
        if result:
            hotel_details.append(result)
        
    cursor.close()
    connection.close()
         
    print("Sending response:", hotel_details)  # Debug response data
    return hotel_details

@app.route('/main_pro2', methods=['GET', 'POST'])
def main_product():
    if request.method == 'POST':
        # Handle form submission from home page
        destination = request.form.get('destination')
        date = request.form.get('date')
        people = request.form.get('people')

        if destination:
            # Store form data in session
            session['destination'] = destination
            session['date'] = date
            session['people'] = people

            # Recommend hotels based on destination only
            df_recommendations = recommend_hotels(destination)

            # Fetch recommended data from database
            hotel_details = fetch_recommend_data(df_recommendations)

            # Render template with recommended data
            return render_template('main_pro2.html', hotel_details=hotel_details, destination=destination, date=date, people=people)
        


    elif request.method == 'GET' and request.args.get('ajax') == 'true':
        # Handle AJAX request for filtering
        facilities = request.args.getlist('facility')
        price = request.args.get('priceRange', type=int)
        destination = session.get('destination', '')

        print('Received AJAX request with:', facilities, price, destination)

        if destination or price or facilities:

            if destination and price and facilities:
                df_recommendations = recommend_hotels(destination, price, facilities)

            elif destination and price and not facilities:
                df_recommendations = recommend_hotels(destination, price)

            elif destination and not price and facilities:
                df_recommendations = recommend_hotels(destination, facilities=facilities)

            elif destination and not price and not facilities:
                df_recommendations = recommend_hotels(destination)

            elif not destination and price and facilities:
                df_recommendations = recommend_hotels(price=price, facilities=facilities)

            elif not destination and price and not facilities:
                df_recommendations = recommend_hotels(price=price)

            elif not destination and not price and facilities:
                df_recommendations = recommend_hotels(facilities=facilities)

            # Fetch recommended data from database
            hotel_details = fetch_recommend_data(df_recommendations)
        
        else:
            # No filters applied, check if destination is set
            if destination:
                df_recommendations = recommend_hotels(destination)
            else:
                # Fetch all hotel data if no filters and no destination
                df_recommendations = fetch_all_data()

            # Fetch data from database
            hotel_details = fetch_recommend_data(df_recommendations)

        # checking if no hotel is recommended
        if not hotel_details:
            message = "No recommended hotel found"
        else:
            message = ""

         # Return data in JSON format for dynamic updates
        return jsonify(hotel_details=hotel_details, message=message)
    

    else:
        # Clear session data when directly accessing the product page
        session.pop('destination', None)
        session.pop('date', None)
        session.pop('people', None)

        # Fetch all hotel data
        hotel_details = fetch_all_data()
        return render_template('main_pro2.html', hotel_details=hotel_details)
