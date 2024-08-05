import pandas as pd
import mysql.connector
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

def fetch_data_from_mysql():
    # Connect to MySQL database
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="aishamysql2023",
        database="hotel_handling"
    )
    
    # SQL query
    query = "SELECT * FROM hotel_info"

    # Read data into DataFrame
    df = pd.read_sql(query, connection)

    # Close the connection
    connection.close()
    
    return df


def preprocess_facilities(facilities):
    lemm = WordNetLemmatizer()
    facilities_tokens = [lemm.lemmatize(w.lower()) for w in facilities]
    return set(facilities_tokens)


def recommend_hotels(city=None, price=None, facilities=None):
    df = fetch_data_from_mysql()
    
    # if df is not None and not df.empty:
    #     print("DataFrame columns:", df.columns)
    # else:
    #     print("DataFrame is None or empty")

    # Debugging: Check the data types and column names
    # print("DataFrame columns:", df.columns)
    # print("DataFrame dtypes:", df.dtypes)
    
    # Preprocess the data
    df['hotel_city'] = df['hotel_city'].str.lower()
    df['facilities'] = df['facilities'].str.lower()
    
    # Debugging: Check preprocessing
    # print("Data after preprocessing:", df.head())

    if city:
        df = df[df['hotel_city'] == city.lower()]
    
    if price is not None and price!='':
        try:
            price = float(price)
            df = df[df['hotel_price'] <= price]
        except ValueError:
            print("Invalid price value.")
    
    if facilities:
        # Handle list input for facilities
        if isinstance(facilities, list):
            f_set = set(preprocess_facilities(facilities))
        else:
            facilities = preprocess_facilities(word_tokenize(facilities.lower()))
            f_set = set(facilities)
        
        # Debugging: Check the processed facilities set
        print("Facilities set:", f_set)
        
        # Calculate similarity based on facilities
        cos = []
        for i in range(df.shape[0]):
            hotel_facilities_tokens = word_tokenize(df['facilities'].iloc[i])
            hotel_facilities_set = set(hotel_facilities_tokens)
            
            # Check if all required facilities are present in hotel facilities
            if f_set.issubset(hotel_facilities_set):
                cos.append(len(f_set))  # Use the count of required facilities as similarity score
            else:
                cos.append(0)
        
        df['similarity'] = cos
        
        # Debugging: Check similarity calculation
        # print("DataFrame with similarity scores:", df.head())
        
        df = df[df['similarity'] > 0]  # Filter out hotels with no matching facilities
        df = df.sort_values(by='similarity', ascending=False).drop_duplicates(subset=['hotel_name'])
    
    df = df.sort_values(by='review_score', ascending=False)
    df = df.reset_index(drop=True)
    
    # Debugging: Final DataFrame
    # print("Final recommended hotels DataFrame:", df.head())
    # print("Query parameters: ", (city, price, facilities))

    return df[['hotel_name', 'hotel_link', 'hotel_type', 'review_score', 'hotel_price', 'hotel_city', 'facilities']].head(50)

