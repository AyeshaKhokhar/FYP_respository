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
    

@app.route('/detail_page', methods=['POST'])
def detail_page():
    hotel_name = request.form.get('hotel_name')
    destination = request.form.get('destination')
    date = request.form.get('date')
    people = request.form.get('people')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch hotel details
    cursor.execute('''
        SELECT hotel_id, hotel_name, hotel_link, room_pic, facilities, hotel_desc, review_score, total_review, hotel_loc, hotel_map
        FROM hotel_info
        WHERE hotel_name = %s
    ''', (hotel_name,))
    hotel = cursor.fetchone()
    
    if hotel:
        hotel_id = hotel['hotel_id']
        room_pics = hotel['room_pic'].split(', ')
        facilities_str = hotel['facilities']
        
        # Split facilities string into a list
        facilities = facilities_str.split('  ')
        
        # Fetch all facility icons at once
        placeholders = ', '.join(['%s'] * len(facilities))
        cursor.execute(f'''
            SELECT icon_name, icon_pic
            FROM icon_detail
            WHERE icon_name IN ({placeholders})
        ''', tuple(facilities))
        icons = cursor.fetchall()
        
        # Create a dictionary for easy lookup
        facility_icons = {icon['icon_name']: icon['icon_pic'] for icon in icons}
        print(facility_icons)
        # Prepare the facility list for the template
        facility_icon_list = []
        for facility in facilities:
            if facility in facility_icons:
                facility_icon_list.append({
                    'name': facility,
                    'pic': facility_icons[facility]
                })
        
        # Step 3: Fetch room details using hotel_id
        cursor.execute('''
            SELECT room_id, room_name, room_price, room_desc, bed_quantity, room_fac
            FROM room_details
            WHERE hotel_id = %s
        ''', (hotel_id,))
        rooms = cursor.fetchall()
        
        print(rooms)
        
        
        # for finding aspect base review analysis
        reviews = fetch_reviews(hotel_name)
        aspect_scores = calculate_aspect_scores(reviews)
        print(aspect_scores)
        
        # for all reviews data
        reviews = fetch_all_review(hotel_name)
       
        truncated_reviews = []
        for review in reviews:
            truncated_review = truncate_review(review['review'])
            truncated_reviews.append({
                'review': truncated_review,
                'reviewerName': review['reviewerName'],
                'reviewTime': review['reviewTime']
            })

        
        # Create a list to store room facilities with icons
        room_list = []
        for room in rooms:
            room_facilities_str = room['room_fac']
            if room_facilities_str:
                room_facilities = [facility.strip() for facility in room_facilities_str.split(',')]
                
                # Fetch icons for room facilities
                placeholders = ', '.join(['%s'] * len(room_facilities))
                cursor.execute(f'''
                    SELECT icon_name, icon_pic
                    FROM icon_detail
                    WHERE icon_name IN ({placeholders})
                ''', tuple(room_facilities))
                room_icons = cursor.fetchall()
                
                # Create a dictionary for room facility icons
                room_facility_icons = {icon['icon_name'].strip(): icon['icon_pic'] for icon in room_icons}
                
                # Prepare the facility list with icons for the room
                room_facility_icon_list = []
                for facility in room_facilities:
                    if facility in room_facility_icons:
                        room_facility_icon_list.append({
                            'name': facility,
                            'pic': room_facility_icons[facility]
                        })
                
                # Append room details with facilities
                room_list.append({
                    'name': room['room_name'],
                    'price': room['room_price'],
                    'description': room['room_desc'],
                    'bed_quantity': room['bed_quantity'],
                    'facilities': room_facility_icon_list
                })
        
        print(f"Room list prepared: {room_list}")
        
        cursor.close()
        conn.close()
        # Pass data to template
        return render_template('detail-product1.html', 
                               hotel=hotel,
                               room_pics=room_pics,
                               facility_icons=facility_icon_list,
                               destination=destination,
                               date=date,
                               people=people,
                               aspect_scores=aspect_scores,
                               reviews=truncated_reviews, 
                               rooms=room_list
                               )
    else:
        return "Hotel not found", 404
