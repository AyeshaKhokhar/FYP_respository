from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from recommender2 import recommend_hotels
import nltk
from nltk.tokenize import word_tokenize
from textblob import TextBlob
from flask_bcrypt import Bcrypt
import os
from werkzeug.utils import secure_filename
import base64
from decimal import Decimal
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
import json
import pickle
import random
import smtplib
import time
from email.message import EmailMessage

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Load the model
model = load_model('sentiment_model.keras')

# Load the tokenizer
with open('tokenizer.pkl', 'rb') as handle:
    tokenizer = pickle.load(handle)
    
def predict_sentiment(score):
    sentiment = "Positive" if score > 0.5 else "Negative"
    return sentiment

def predict_sentiment_score(review):
    sequence = tokenizer.texts_to_sequences([review])
    padded_sequence = pad_sequences(sequence, maxlen = 200)
    prediction = model.predict(padded_sequence)
    return prediction[0][0].round(1)

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

def save_image(image_data, filename):
    # If image_data is a base64 string, decode it first
    if image_data.startswith('data:image'):
        header, image_data = image_data.split(';base64,')
        image_data = base64.b64decode(image_data)
    
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'wb') as f:
        f.write(image_data)

def convert_to_html(description):
    """
    Convert plain text description into HTML paragraphs.
    """
    # Split the description into paragraphs based on double newlines
    paragraphs = description.strip().split('\n\n')
    
    # Convert each paragraph into <p> tag
    html_paragraphs = ''.join(f'<p>{p.strip()}</p>\n' for p in paragraphs)
    
    return html_paragraphs

def get_next_hotel_id():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch the highest hotel_id from id_tracker
    cursor.execute("SELECT last_id FROM id_tracker WHERE id_type = 'hotel_id'")
    result = cursor.fetchone()
    last_id = result['last_id']
    
    # Calculate the new hotel_id
    new_hotel_id = last_id + 1
    
    # Update the last_id in the tracker
    cursor.execute("UPDATE id_tracker SET last_id = %s WHERE id_type = 'hotel_id'", (new_hotel_id,))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return new_hotel_id

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

@app.route('/list_property')
def property():
    if 'user_id' not in session:
        return render_template('login.html', error_message='First u need to get login.')
    if 'user_id' in session: 
        print('yes it is', session['user_id'])
    return render_template('list_form.html')

@app.route('/submit_property', methods=['POST'])
def submit_property():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    submission_type = request.form.get('submission_type', '')
    if 'user_id' not in session and submission_type == 'list_property':
        return jsonify({'status': 'error', 'message': 'You must be logged in to submit a property.'}), 403

    try:
        
        if submission_type == 'list_property':
            username = request.form.get('username', '')
            email = request.form.get('email', '')
            password = request.form.get('password', '')
            confirmPassword = request.form.get('confirmPassword', '')
            address = request.form.get('address', '')
            phone = request.form.get('phone', '')
            hotel_name = request.form.get('hotelName', '')
            hotel_link = request.form.get('googleMapLink', '')
            hotel_location = request.form.get('hotelLocation', '')
            hotel_city = request.form.get('city', '')
            hotel_score = request.form.get('ratingScore', '')
            hotel_embeddedCode = request.form.get('embeddedCode', '')
            hotel_facilities = request.form.getlist('facilities')
            room_name = request.form.get('totalRooms', '')
            room_details = request.form.get('roomDetails', '')
            room_bed = request.form.get('bedSize', '')
            room_facilities = request.form.getlist('room_facilities')
            # Handle file uploads (only store filenames)
            hotel_images = request.files.getlist('hotelImages')
            hotel_main_image = request.files.get('hotelMainImage')

        # Check if email exists in the database
            print('not eneterd')
            cursor.execute('SELECT * FROM visitor WHERE email = %s', (email,))
            print(email)
            user = cursor.fetchone()

            if user:
                # If user exists, check if session user_id matches the email ID
                existing_user_id = user['id']
                print('useris')
                print(user['id'])
                if session['user_id'] != existing_user_id:
                    print('usrenot')
                    print(session['user_id'])
                    # Update session user_id to match the email ID
                    session['user_id'] = existing_user_id
                    print(session['user_id'])
            else:
                
                if password != confirmPassword:
                    return render_template('list_form.html', error_message='Passwords do not match. Please try again.')

            # Hash the password using Flask-Bcrypt
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                
                print('about')
                cursor.execute('INSERT INTO visitor (username, email, password) VALUES (%s, %s, %s)', (username, email, hashed_password))
                
                conn.commit()
                new_user_id = cursor.lastrowid
                print('go')
                session['user_id'] = new_user_id

            # Extract filenames from file objects
            hotel_images_filenames = [image.filename for image in hotel_images if image.filename]
            main_image_filename = hotel_main_image.filename if hotel_main_image and hotel_main_image.filename else None

            # Convert lists to strings for database insertion
            hotel_facilities_str = '  '.join(hotel_facilities)
            room_facilities_str = ', '.join(room_facilities)
            hotel_images_str = ', '.join(hotel_images_filenames)
            print('done')
          
            print('to enter')
            cursor.execute("""
                INSERT INTO property (
                    user_id, username, email, password, address, phone, hotel_name, hotel_city, hotel_location, 
                    hotel_score, hotel_link, hotel_mapcode, hotel_facilities, room_name, room_des, 
                    room_bed, room_facilities, hotel_images, hotel_main_image, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            """, (
                session['user_id'], username, email, password, address, phone, hotel_name, hotel_city, hotel_location,
                hotel_score, hotel_link, hotel_embeddedCode, hotel_facilities_str, room_name, room_details,
                room_bed, room_facilities_str, hotel_images_str, main_image_filename
            ))
            conn.commit()
            print('notere')
            return jsonify({'status': 'success', 'message': 'Property submitted for review!'})
        
        elif submission_type == 'partner_panel':
            # Handle property submission for 'partner_panel' without user credentials
            hotel_name = request.form.get('hotel-name', '')
            city = request.form.get('city', '')
            hotel_location = request.form.get('hotel-location', '')
            hotel_rating = request.form.get('hotel-rating', '')
            google_map_link = request.form.get('googleMapLink', '')
            embedded_code = request.form.get('embeddedCode', '')
            facilities = request.form.getlist('facilities')
            hotel_description = request.form.get('hotel-description', '')
            room_name = request.form.get('totalRooms', '')
            bed_size = request.form.get('bedSize', '')
            room_facilities = request.form.getlist('roomFacilities')
            room_details = request.form.get('roomDetails', '')
            hotel_images = request.files.getlist('hotelImages')
            hotel_main_image = request.files.get('hotelMainImage')

            # Extract filenames from file objects
            hotel_images_filenames = [image.filename for image in hotel_images if image.filename]
            main_image_filename = hotel_main_image.filename if hotel_main_image and hotel_main_image.filename else None
            
            # Convert lists to strings for database insertion
            facilities_str = ', '.join(facilities)
            room_facilities_str = ', '.join(room_facilities)
            hotel_images_str = ', '.join(hotel_images_filenames)

            user_id =session.get('user_id')
            cursor.execute('SELECT username, email, password FROM visitor WHERE id = %s', (user_id,))
            user_details = cursor.fetchone()
            username = user_details['email']
            email = user_details['password']
            password = user_details['username']
            print(username, email, password)
            # Insert into property table
            cursor.execute("""
                INSERT INTO property (
                    user_id, username, email, password, address, phone, hotel_name, hotel_city, hotel_location, 
                    hotel_score, hotel_link, hotel_mapcode, hotel_facilities, room_name, room_des, 
                    room_bed, room_facilities, hotel_images, hotel_main_image, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            """, (
                session.get('user_id', None),  user_details['username'], user_details['email'] , user_details['password'],  None, None, hotel_name, city, hotel_location,
                hotel_rating, google_map_link, embedded_code, facilities_str, room_name, room_details,
                bed_size, room_facilities_str, hotel_images_str, main_image_filename
            ))

        conn.commit()
        return jsonify({'status': 'success', 'message': 'Property submitted for review!'})

    except Exception as e:
        print(f"Exception: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


    finally:
        conn.close()

@app.route('/update_hotel', methods=['POST'])
def update_hotel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    user_id = session.get('user_id')  
    hotel_id = request.form.get('hotel-id')

    # Check if hotel ID exists for the user
    cursor.execute('SELECT hotel_id FROM hotel_info WHERE hotel_id = %s AND user_id = %s', (hotel_id, user_id))
    result = cursor.fetchone()

    if not result:
        return jsonify({"status": "error", "message": "Hotel ID does not exist or is not associated with this user"})

    # Get form data
    hotel_id = request.form.get('hotel-id')
    hotel_name = request.form.get('update-hotel-name')
    hotel_location = request.form.get('update-hotel-location')
    hotel_rating = request.form.get('update-hotel-rating')
    hotel_description = request.form.get('update-hotel-description')
    
    # Handle file upload if present
    hotel_main_image = request.files.get('hotelMainImage')
    if hotel_main_image:
        # Save file and get its path
        image_path = f"static/images/{hotel_main_image.filename}"
        hotel_main_image.save(image_path)
    else:
        image_path = None  # No image uploaded

    try:
        # Construct SQL query based on provided data
        update_query = "UPDATE hotel_info SET "
        update_values = []

        if hotel_name:
            update_query += "hotel_name = %s, "
            update_values.append(hotel_name)
        if hotel_location:
            update_query += "hotel_loc = %s, "
            update_values.append(hotel_location)
        if hotel_rating:
            update_query += "review_score = %s, "
            update_values.append(hotel_rating)
        if hotel_description:
            update_query += "description = %s, "
            update_values.append(hotel_description)
        if image_path:
            update_query += "main_image = %s, "
            update_values.append(image_path)

        # Remove trailing comma and space
        update_query = update_query.rstrip(", ")
        update_query += " WHERE hotel_id = %s"
        update_values.append(hotel_id)

        # Execute the update query
        cursor.execute(update_query, tuple(update_values))
        conn.commit()

        return jsonify({"status": "success", "message": "Hotel information updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
@app.route('/update_account', methods=['POST'])
def update_account():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    user_id = session.get('user_id') 

    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    try:
        # Construct SQL query based on provided data
        update_query = "UPDATE visitor SET "
        update_values = []

        if name:
            update_query += "username = %s, "
            update_values.append(name)
        if email:
            update_query += "email = %s, "
            update_values.append(email)
        if password:
            # Encrypt the password before updating
            encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Replace this with your encryption method
            update_query += "password = %s, "
            update_values.append(encrypted_password)

        # Check if any fields were provided
        if not update_values:
            return jsonify({"status": "error", "message": "No updates provided"})

        # Remove trailing comma and space
        update_query = update_query.rstrip(", ")
        update_query += " WHERE id = %s"
        update_values.append(user_id)

        # Execute the update query for the visitor table
        cursor.execute(update_query, tuple(update_values))
        conn.commit()

        # Update the listed_user table similarly
        update_query_listed_user = "UPDATE listed_user SET "
        update_values_listed_user = []

        if name:
            update_query_listed_user += "username = %s, "
            update_values_listed_user.append(name)
        if email:
            update_query_listed_user += "email = %s, "
            update_values_listed_user.append(email)
        if password:
            # Encrypt the password before updating
            encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Replace this with your encryption method
            update_query_listed_user += "password = %s, "
            update_values_listed_user.append(encrypted_password)
      
        # Remove trailing comma and space
        if update_values_listed_user:  # Ensure there is something to update
            update_query_listed_user = update_query_listed_user.rstrip(", ")
            update_query_listed_user += " WHERE listeduser_id = %s"
            update_values_listed_user.append(user_id)

            cursor.execute(update_query_listed_user, tuple(update_values_listed_user))
            conn.commit()

        return jsonify({"status": "success", "message": "Account information updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/partner_panel')
def partner_panel():

    print(session['user_id'])
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        action = request.args.get('action')
        hotel_id = request.args.get('hotel_id')

        if action == 'delete' and hotel_id:
            print('enetered in del')
            # Get user_id from hotel_info
            cursor.execute('SELECT user_id FROM hotel_info WHERE hotel_id = %s', (hotel_id,))
            hotel_info = cursor.fetchone()

            if hotel_info:
                owner_id = hotel_info['user_id']
                print('owneris: ', owner_id)
                # Delete hotel record
                cursor.execute('DELETE FROM hotel_info WHERE hotel_id = %s', (hotel_id,))
                conn.commit()
                print('succes del')
                # Notify admin
                # Implement your email notification logic here
                print(f'Notify admin: Hotel with ID {hotel_id} deleted.')

                # Check if there are other hotels listed by this user
                cursor.execute('SELECT COUNT(*) AS hotel_count FROM hotel_info WHERE user_id = %s', (owner_id,))
                hotel_count = cursor.fetchone()['hotel_count']
                print("countis:", hotel_count)
                if hotel_count == 0:      

                    # Notify admin about user account deletion
                    cursor.execute('SELECT username FROM listed_user WHERE listeduser_id = %s', (owner_id,))
                    user_info = cursor.fetchone()
                    print('finduser')
                    if user_info:
                        print(f'Notify admin: User with ID {owner_id} ({user_info["username"]}) deleted all hotels.')
                        
                    # No more hotels listed by this user
                    cursor.execute('DELETE FROM listed_user WHERE listeduser_id = %s', (owner_id,))
                    conn.commit()
                    print('dellist')
                    message = 'All listed hotels deleted. You are no longer a partner.'
                    # Redirect to home page with alert
                    return jsonify({'status': 'success', 'message': message, 'redirect': '/'})
                else:
                    message = 'Hotel deleted successfully.'
                    return jsonify({'status': 'success', 'message': message})

            return jsonify({'status': 'error', 'message': 'Hotel not found.'})
        
    except Exception as e:
        print(f"Exception: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

    cursor.execute('SELECT COUNT(*) AS total_hotels FROM hotel_info WHERE user_id = %s', (user_id,))
    total_listed_hotels = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(*) AS pending_total_hotels FROM property WHERE user_id = %s', (user_id,))
    pending_listed_hotels = cursor.fetchone()

    cursor.execute('SELECT denied_list FROM listed_user WHERE listeduser_id = %s', (user_id,))
    denied_listed_hotels = cursor.fetchone()
    print('deny is: ', denied_listed_hotels['denied_list'])

    cursor.execute('SELECT approved_list FROM listed_user WHERE listeduser_id = %s', (user_id,))
    approved_listed_hotels = cursor.fetchone()
    print('apprve is: ', approved_listed_hotels['approved_list'])

    cursor.execute('SELECT * FROM hotel_info WHERE user_id = %s', (user_id,))
    listed_hotels_details = cursor.fetchall()

    for hotel in listed_hotels_details:
        print(hotel['hotel_name'])
        print(hotel['hotel_loc'])
        print(hotel['review_score'])

    hotel_names = [hotel['hotel_name'] for hotel in listed_hotels_details]
    review_scores = [hotel['review_score'] for hotel in listed_hotels_details]

    return render_template('partner_panel.html',
                           total_listed_hotels=total_listed_hotels,
                           listed_hotels_details=listed_hotels_details,
                           pending_listed_hotels=pending_listed_hotels,
                           denied_listed_hotels=denied_listed_hotels,
                           approved_listed_hotels=approved_listed_hotels,
                           hotel_names=hotel_names,
                           review_scores=review_scores
                           )

def calculate_sentiment_score(review_text):
    review = review_text
    score = predict_sentiment_score(review)
    return round(score * 3, 1) 

@app.route('/submit_review', methods=['POST'])
def submit_review():
    hotel_id = request.form.get('hotel_id')
    review_text = request.form.get('review-text')
   
    print('hotel is: ',hotel_id)
    if 'user_id' not in session:
        print('not in session redirecting it')
        error_message = "First you need to login"
        return jsonify({'status': 'redirect', 'url': url_for('login', error_message=error_message, comes='review', hotel=hotel_id), 'error_message': error_message})
        
    user_id = session['user_id']
    print('user: ', user_id)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
        # Fetch reviewer's name from visitors table
    cursor.execute('SELECT username FROM visitor WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if not user:
        return 'User not found', 404

    reviewer_name = user['username']

    sentiment_score = calculate_sentiment_score(review_text)
    score = predict_sentiment_score(review_text)
    sentiment = predict_sentiment(score)
        
    print('score: ', sentiment_score)
    print('sentiment',sentiment)

        # Fetch hotel details from hotel_info
    cursor.execute('SELECT review_score, hotel_name FROM hotel_info WHERE hotel_id = %s', (hotel_id,))
    hotel = cursor.fetchone()
    if not hotel:
        cursor.close()
        conn.close()
        return 'Hotel not found', 404

    hotel_name = hotel['hotel_name']

        # Insert the new review into hotel_reviews
    cursor.execute("""
        INSERT INTO hotel_review_data1 (reviewerName, reviewTime, review, hotelName, sentiment)
        VALUES (%s, %s, %s, %s, %s)
    """, (reviewer_name, 'now', review_text, hotel_name, sentiment))
        
    cursor.execute('SELECT COUNT(review) AS total_reviews FROM hotel_review_data1 WHERE hotelName = %s', (hotel_name,))
    total_hotel_reviews = cursor.fetchone()

    existing_review_count = total_hotel_reviews['total_reviews']
    print('total: ', existing_review_count)
    existing_avg_score = hotel['review_score']
    print('review: ', existing_avg_score)

        # Convert Decimal to float if necessary
    if isinstance(existing_avg_score, Decimal):
        existing_avg_score = float(existing_avg_score)

        # formula for new average score of hotel
    new_avg_score = ((existing_avg_score * existing_review_count) + sentiment_score) / (existing_review_count + 1)

    new_review_count = existing_review_count + 1
    
    cursor.execute(
        "UPDATE hotel_info SET review_score = %s, total_review = %s WHERE hotel_name = %s",
        (new_avg_score, new_review_count, hotel_name)
    )
    conn.commit()
        
    cursor.close()
    conn.close()
        
    return jsonify({'status': 'success', 'message': 'Review submitted successfully!'})

# Global variables
current_otp = None
otp_email = None
otp_sent_time = None

@app.route('/send_otp', methods=['POST'])
def send_otp():
    global current_otp, otp_email, otp_sent_time

    # Extract form data
    data = request.form
    email = data.get('email')

    if email:
        # Check if OTP is still valid
        if current_otp and otp_sent_time and time.time() - otp_sent_time < 60:
            return jsonify({'success': False, 'error': 'OTP has already been sent. Please wait before requesting a new one.'})

        # Generate OTP
        current_otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        otp_email = email
        otp_sent_time = time.time()

        # Send OTP via email
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            from_mail = 'ayesharasheed6949@gmail.com'
            server.login(from_mail, 'bfpu ethh rall amui')
            msg = EmailMessage()
            msg['Subject'] = "OTP Verification"
            msg['From'] = from_mail
            msg['To'] = email
            msg.set_content("Your OTP is: " + current_otp)
            server.send_message(msg)
            server.quit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Email is required'})

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    global current_otp, otp_sent_time

    data = request.get_json()
    otp = data.get('otp')

    if otp == current_otp:
        if time.time() - otp_sent_time <= 60:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'OTP expired. Please request a new one.'})
    else:
        return jsonify({'success': False, 'error': 'Invalid OTP. Please try again.'})