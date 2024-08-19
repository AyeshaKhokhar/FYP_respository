from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from recommender2 import recommend_hotels
import nltk
from nltk.tokenize import word_tokenize
from textblob import TextBlob
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

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


def fetch_all_review(hotel_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT review, reviewerName, reviewTime FROM hotel_review_data1 WHERE hotelName=%s", (hotel_name,))
    reviews = cursor.fetchall()
    conn.close()
    return reviews

def truncate_review(review_text, num_words=20):
    words = review_text.split()
    return ' '.join(words[:num_words]) + ('...' if len(words) > num_words else '')


def fetch_reviews(hotel_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT review FROM hotel_review_data1 WHERE hotelName=%s", (hotel_name,))
    reviews = cursor.fetchall()
    conn.close()
    return [review['review'] for review in reviews]

# Function to extract aspects from review
aspects = ["room", "facilities", "comfort", "staff",  "cleanliness"]

def extract_aspects(review):
    words = word_tokenize(review.lower())
    return [aspect for aspect in aspects if aspect in words]

# Function to perform sentiment analysis
def analyze_sentiment(review):
    blob = TextBlob(review)
    return blob.sentiment.polarity

# Function to convert sentiment to score
def sentiment_to_score(polarity):
    return (polarity + 1) * 5

# Function to calculate aspect scores
def calculate_aspect_scores(reviews):
    aspect_scores = {aspect: [] for aspect in aspects}
    
    for review in reviews:
        review_aspects = extract_aspects(review)
        sentiment = analyze_sentiment(review)
        score = sentiment_to_score(sentiment)
        
        for aspect in review_aspects:
            aspect_scores[aspect].append(score)
    
    average_scores = {aspect: (sum(scores) / len(scores) if scores else None) 
                      for aspect, scores in aspect_scores.items()}
    
    return average_scores

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if both passwords match
        if password != confirm_password:
            return render_template('registeration.html', error_message='Passwords do not match. Please try again.')

         # Hash the password using Flask-Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if the email already exists
        cursor.execute('SELECT * FROM visitor WHERE email = %s', (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return render_template('registeration.html', error_message='Username already exists. Please choose a different username.')

        # Insert new user into the database
        cursor.execute('INSERT INTO visitor (username, email, password) VALUES (%s, %s, %s)', 
                       (username, email, hashed_password))
        conn.commit()
        session.pop('user_id', None)
        cursor.close()
        conn.close()

        return redirect(url_for('login'))

    return render_template('registeration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        source = request.form['source']
        print('source is:', source)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Use dictionary cursor to access columns by name

        # Check if the email matches the admin email and password
        admin_username = 'adminusername'
        admin_email = 'admin@gmail.com'  # Replace with your admin email
        admin_password = 'adminpassword'  # Replace with your hashed admin password

        if email == admin_email and password == admin_password:
            session['user_id'] = 'admin'  # Use a special identifier for admin
            session['role'] = 'admin'
            print(session['role'])
            if source == 'dashboard':
                print('indashb')
                # Redirect to user panel page if coming from dashboard
                return redirect(url_for('admin'))
            cursor.close()
            conn.close()
            return redirect(url_for('admin'))

        # Check if the email exists in the visitor table
        cursor.execute('SELECT * FROM visitor WHERE email = %s', (email,))
        user = cursor.fetchone()
        

        if user:
            if bcrypt.check_password_hash(user['password'], password):
                newid = user['id']
                # Check if the user is in the listed_user table
                cursor.execute('SELECT * FROM hotel_info WHERE user_id = %s', (newid,))
                listed_user = cursor.fetchone()
   
                print('session: ', session.get('user_id', None))
                if listed_user:
                    # storing current id
                    if source == 'dashboard':
                        if 'user_id' in session:
                            session['previous_session_id'] = session.get('user_id', None)
                            print('pre is: ', session['previous_session_id'] )
                    # User is in the listed_user table

                    session['user_id'] = listed_user['user_id']
                    session['role'] = 'listed'
                    print(session['role'])
                    print('curr: ', session['user_id'] )
                    if source == 'dashboard':
                        print('indashb')
                # Redirect to user panel page if coming from dashboard
                        return redirect(url_for('partner_panel'))
                    else:
                        # Redirect to home if not coming from dashboard
                        return redirect(url_for('home'))
                else:
                    if source != 'dashboard':
                    # User is a visitor
                        session['user_id'] = user['id']
                        session['role'] = 'visitor'
                        print(session['role'])

                    if source == 'dashboard':
                # Redirect to user panel page if coming from dashboard
                        return redirect(url_for('home', message='You are not listed as a property user.'))
                
                cursor.close()
                conn.close()
                return redirect(url_for('home'))  # Redirect to user dashboard or home

            else:
                cursor.close()
                conn.close()
                if source == 'dashboard':
                    return redirect(url_for('home', message='Invalid email or password.'))
                return render_template('login.html', error_message='Invalid email or password.')
               

        else:
            cursor.close()
            conn.close()
            return render_template('login.html', error_message='Email not found.')

    return render_template('login.html')

@app.route('/admin', methods=['POST', 'GET'])
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()        
    cursor.execute("SELECT COUNT(*) AS total_hotels FROM hotel_info")
    total_hotels = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) AS total_registrations FROM visitor")
    total_registrations = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) AS total_properties FROM property")
    count_pending_properties = cursor.fetchone()[0]

    cursor.execute("SELECT id, username, email FROM visitor")
    user_info = cursor.fetchall()
  
#   for delete button whether user data is deleted or hotel data is deleted
    action = request.args.get('action')
    user_id = request.args.get('user_id')
    hotel_id = request.args.get('hotel_id')
    property_id = request.args.get('property_id')
 
    print('action: ', action, 'user_id: ', user_id, 'hotel_id: ', hotel_id)
    
    if action == 'delete' and user_id:
        cursor.execute("DELETE FROM visitor WHERE id = %s", (user_id,))
        conn.commit()
        response = {'status': 'success', 'message': 'User deleted successfully'}
        return jsonify(response)
    
    if action == 'delete' and hotel_id:
        cursor.execute("DELETE FROM hotel_info WHERE hotel_id = %s", (hotel_id,))
        conn.commit()
        response = {'status': 'success', 'message': 'Hotel deleted successfully'}
        return jsonify(response)
    
    cursor.execute("SELECT * FROM property")
    all_pending_property = cursor.fetchall()
    
    if action == 'approve' and property_id:
        print('inside approve')
        # Fetch pending property data
        cursor.execute("SELECT * FROM property WHERE id = %s", (property_id,))
        pending_property = cursor.fetchone()
        
        # cursor.execute("SELECT MAX(hotel_id) AS last_id FROM hotel_info")
        # result = cursor.fetchone()
        hotel_id_do = get_next_hotel_id()

        if pending_property:
            print("inside property")
            # Store approved property in hotel_info table
            cursor.execute("SELECT * FROM visitor WHERE id = %s", (pending_property[1],))
            user = cursor.fetchone()

             # Check if the user already has an entry in the listed table
            cursor.execute("SELECT COUNT(*) FROM listed_user WHERE listeduser_id = %s", (pending_property[1],))
            is_listed = cursor.fetchone()[0] > 0

            if is_listed:
                    # Update the approved count for the user in the listed table
                cursor.execute("UPDATE listed_user SET approved_list = approved_list + 1 WHERE listeduser_id = %s", (pending_property[1],))
            else:
                    # Insert a new entry if not already listed
                cursor.execute("""
                        INSERT INTO listed_user (listeduser_id, username, email, password, hotel_id, approved_list, denied_list)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (pending_property[1], user[1], user[2], user[3], hotel_id_do, 1, 0))
                conn.commit()

            cursor.execute("""
                INSERT INTO hotel_info (hotel_id, hotel_link, hotel_name, review_score, hotel_city, facilities, hotel_pic, room_pic, hotel_loc, hotel_map, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (hotel_id_do, pending_property[11], pending_property[7], pending_property[10], pending_property[8], pending_property[13], pending_property[19], pending_property[18], pending_property[9], pending_property[12], pending_property[1]))
            conn.commit()

            # Insert room details into room_details table
            cursor.execute("""
                INSERT INTO room_details (hotel_id, room_name, room_desc, bed_quantity, room_fac)
                VALUES (%s, %s, %s, %s, %s)
            """, (hotel_id_do, pending_property[14], pending_property[15], pending_property[16], pending_property[17]))


            # Delete the approved property from pending_properties
            cursor.execute("DELETE FROM property WHERE id = %s", (property_id,))
            conn.commit()

            response = {'status': 'success', 'message': 'Listing approved successfully'}
            return jsonify(response)

            # Notify user about approval
         
        else:
            response = {'status': 'success', 'message': 'Listing not approved successfully'}
            return jsonify(response)   # Implement email notification here

    elif action == 'decline' and property_id:
        # Delete the pending property
        print('priperty is: ', property_id)
        cursor.execute("SELECT user_id FROM property WHERE id = %s", (property_id,))
        denied_user_id = cursor.fetchone()[0]
        print('denied is:', denied_user_id)

        cursor.execute("DELETE FROM property WHERE id = %s", (property_id,))
        conn.commit()

        if denied_user_id:
            cursor.execute("SELECT listeduser_id FROM listed_user WHERE listeduser_id = %s", (denied_user_id,))
            islisted = cursor.fetchone()
            print(islisted)
            if islisted:
                # Update the denied count for the user
                cursor.execute("UPDATE listed_user SET denied_list = denied_list + 1 WHERE listeduser_id = %s", (denied_user_id,))
                conn.commit()
        
        response = {'status': 'success', 'message': 'Listing deny successfully'}
        return jsonify(response)
        # Notify user about rejection
        # Implement email notification here

    elif request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = request.get_json()
                hotel_id = data.get('hotel-id')
                hotel_name = data.get('hotel-name')
                hotel_description = data.get('hotel-description')
                hotel_location = data.get('hotel-location')
                hotel_images = data.get('hotel-images')  # Base64 encoded image data

                update_fields = []
                params = []

                if hotel_name:
                    update_fields.append("hotel_name = %s")
                    params.append(hotel_name)

                if hotel_description:
                    hotel_description_html = convert_to_html(hotel_description)
                    update_fields.append("hotel_desc = %s")
                    params.append(hotel_description_html)
                
                if hotel_location:
                    update_fields.append("hotel_city = %s")
                    params.append(hotel_location)

      

                # Handle image if provided
                if hotel_images:
                    filename = 'image_' + hotel_id + '.png'  # Dynamic filename based on hotel ID
                    filename = secure_filename(filename)  # Ensure filename is safe
                    save_image(hotel_images, filename)
                    update_fields.append("hotel_pic = %s")
                    params.append(filename)

                if not hotel_id:
                    return jsonify({'status': 'error', 'message': 'Hotel ID is required'}), 400
                params.append(hotel_id)
                # Create the update query string
                update_query = "UPDATE hotel_info SET " + ", ".join(update_fields) + " WHERE hotel_id = %s"

                # Debugging prints
                print(f"Update Query: {update_query}")
                print(f"Parameters: {params}")

                # Execute the query
                cursor.execute(update_query, params)
                conn.commit()

                return jsonify({'status': 'success', 'message': 'Hotel information updated successfully!'}) 

        except Exception as e:
            print(f"Exception: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    cursor.execute("SELECT hotel_id, hotel_name, hotel_type, hotel_city, hotel_price, review_score  FROM hotel_info ORDER BY review_score DESC")
    hotel_data = cursor.fetchall()
    # print(hotel_data)

    # Fetch all users for GET request without action
    cursor.execute("SELECT id, username, email FROM visitor")
    users = cursor.fetchall()
    response = {'status': 'success', 'users': users}

    conn.close()

    return render_template('adminpanel.html',
                           total_hotels=total_hotels,
                           total_registrations=total_registrations,
                           user_info=user_info,
                           hotel_data=hotel_data,
                           all_pending_property=all_pending_property,
                           count_pending_properties=count_pending_properties)
