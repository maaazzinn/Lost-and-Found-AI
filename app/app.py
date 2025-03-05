from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import sqlite3
import datetime
import smtplib
from email.message import EmailMessage
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity
import cv2
from sentence_transformers import SentenceTransformer

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "lost_and_found_secret_key"

# Use absolute path for uploads
UPLOAD_BASE_PATH = r'C:\Users\mazin\Downloads\ansalna\app\static\uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_BASE_PATH
app.config['LOST_FOLDER'] = os.path.join(UPLOAD_BASE_PATH, 'lost')
app.config['FOUND_FOLDER'] = os.path.join(UPLOAD_BASE_PATH, 'found')

# Create upload directories if they don't exist
os.makedirs(app.config['LOST_FOLDER'], exist_ok=True)
os.makedirs(app.config['FOUND_FOLDER'], exist_ok=True)

# Database setup
def get_db_connection():
    conn = sqlite3.connect('instance/database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create lost_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lost_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT NOT NULL,
        contact_info TEXT NOT NULL,
        image_path TEXT NOT NULL,
        date_reported TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create found_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS found_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT NOT NULL,
        contact_info TEXT NOT NULL,
        image_path TEXT NOT NULL,
        date_reported TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create matches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lost_id INTEGER NOT NULL,
        found_id INTEGER NOT NULL,
        confidence REAL NOT NULL,
        is_verified BOOLEAN DEFAULT 0,
        date_matched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lost_id) REFERENCES lost_items (id),
        FOREIGN KEY (found_id) REFERENCES found_items (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# AI Model setup
# Image Processing Model
image_model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

# Text Processing Model
text_model = SentenceTransformer('all-MiniLM-L6-v2')

# Image processing functions
def preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    return img_array

def extract_image_features(img_path):
    try:
        img_array = preprocess_image(img_path)
        features = image_model.predict(img_array)
        return features[0]
    except Exception as e:
        print(f"Error extracting image features: {e}")
        return None

def get_text_embedding(text):
    try:
        embedding = text_model.encode([text])[0]
        return embedding
    except Exception as e:
        print(f"Error extracting text embedding: {e}")
        return None

def compute_match_score(lost_item, found_item):
    # Extract image features
    lost_img_features = extract_image_features(os.path.join(app.root_path, lost_item['image_path']))
    found_img_features = extract_image_features(os.path.join(app.root_path, found_item['image_path']))
    
    # Calculate image similarity
    if lost_img_features is not None and found_img_features is not None:
        image_similarity = cosine_similarity([lost_img_features], [found_img_features])[0][0]
    else:
        image_similarity = 0
    
    # Combine item descriptions for text matching
    lost_text = f"{lost_item['name']} {lost_item['description']} {lost_item['category']}"
    found_text = f"{found_item['name']} {found_item['description']} {found_item['category']}"
    
    # Extract text embeddings
    lost_text_embedding = get_text_embedding(lost_text)
    found_text_embedding = get_text_embedding(found_text)
    
    # Calculate text similarity
    if lost_text_embedding is not None and found_text_embedding is not None:
        text_similarity = cosine_similarity([lost_text_embedding], [found_text_embedding])[0][0]
    else:
        text_similarity = 0
    
    # Weighted combination of similarities (60% image, 40% text)
    overall_score = (image_similarity * 0.6) + (text_similarity * 0.4)
    
    return overall_score

def find_matches():
    conn = get_db_connection()
    lost_items = conn.execute('SELECT * FROM lost_items').fetchall()
    found_items = conn.execute('SELECT * FROM found_items').fetchall()
    
    matches = []
    
    for lost_item in lost_items:
        for found_item in found_items:
            # Check if this pair is already in the matches table
            existing_match = conn.execute('''
                SELECT * FROM matches 
                WHERE lost_id = ? AND found_id = ?
            ''', (lost_item['id'], found_item['id'])).fetchone()
            
            if existing_match:
                continue
            
            # Compute match score
            match_score = compute_match_score(lost_item, found_item)
            
            # If match score is above threshold (0.7), add to matches
            if match_score > 0.7:
                conn.execute('''
                    INSERT INTO matches (lost_id, found_id, confidence)
                    VALUES (?, ?, ?)
                ''', (lost_item['id'], found_item['id'], match_score))
                
                matches.append({
                    'lost_item': dict(lost_item),
                    'found_item': dict(found_item),
                    'confidence': match_score
                })
    
    conn.commit()
    conn.close()
    
    return matches

# Notification function
def send_notification(email, subject, message):
    try:
        # This is a placeholder. In a real app, you would configure SMTP settings
        # or use a service like SendGrid, Mailgun, etc.
        print(f"Notification sent to {email}")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        return True
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return False

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lost', methods=['GET', 'POST'])
def lost_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        location = request.form['location']
        contact_info = request.form['contact_info']
        
        # Handle image upload
        if 'image' not in request.files:
            flash('No image uploaded')
            return redirect(request.url)
        
        file = request.files['image']
        if file.filename == '':
            flash('No image selected')
            return redirect(request.url)
        
        filename = f"lost_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        file_path = os.path.join(app.config['LOST_FOLDER'], filename)
        file.save(file_path)
        
        # Save to database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO lost_items (name, description, category, location, contact_info, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, category, location, contact_info, os.path.join('static', 'uploads', 'lost', filename)))
        conn.commit()
        conn.close()
        
        # Find potential matches
        matches = find_matches()
        
        # If matches found, notify user
        if matches:
            flash('Potential matches found! Check the results page.')
            return redirect(url_for('results'))
        else:
            flash('Your lost item has been registered. We will notify you if a match is found.')
            return redirect(url_for('index'))
    
    return render_template('lost_form.html')

@app.route('/found', methods=['GET', 'POST'])
def found_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        location = request.form['location']
        contact_info = request.form['contact_info']
        
        # Handle image upload
        if 'image' not in request.files:
            flash('No image uploaded')
            return redirect(request.url)
        
        file = request.files['image']
        if file.filename == '':
            flash('No image selected')
            return redirect(request.url)
        
        filename = f"found_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        file_path = os.path.join(app.config['FOUND_FOLDER'], filename)
        file.save(file_path)
        
        # Save to database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO found_items (name, description, category, location, contact_info, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, category, location, contact_info, os.path.join('static', 'uploads', 'found', filename)))
        conn.commit()
        conn.close()
        
        # Find potential matches
        matches = find_matches()
        
        # If matches found, notify user
        if matches:
            flash('Potential matches found! Check the results page.')
            return redirect(url_for('results'))
        else:
            flash('Your found item has been registered. We will notify owners of potential matches.')
            return redirect(url_for('index'))
    
    return render_template('found_form.html')

@app.route('/results')
def results():
    conn = get_db_connection()
    matches = conn.execute('''
        SELECT m.id, m.confidence, m.is_verified,
               l.id as lost_id, l.name as lost_name, l.description as lost_description, 
               l.category as lost_category, l.location as lost_location, 
               l.contact_info as lost_contact, l.image_path as lost_image,
               f.id as found_id, f.name as found_name, f.description as found_description, 
               f.category as found_category, f.location as found_location, 
               f.contact_info as found_contact, f.image_path as found_image
        FROM matches m
        JOIN lost_items l ON m.lost_id = l.id
        JOIN found_items f ON m.found_id = f.id
        ORDER BY m.confidence DESC
    ''').fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    matches_data = []
    for match in matches:
        matches_data.append({
            'id': match['id'],
            'confidence': match['confidence'],
            'is_verified': match['is_verified'],
            'lost_item': {
                'id': match['lost_id'],
                'name': match['lost_name'],
                'description': match['lost_description'],
                'category': match['lost_category'],
                'location': match['lost_location'],
                'contact_info': match['lost_contact'],
                'image_path': match['lost_image']
            },
            'found_item': {
                'id': match['found_id'],
                'name': match['found_name'],
                'description': match['found_description'],
                'category': match['found_category'],
                'location': match['found_location'],
                'contact_info': match['found_contact'],
                'image_path': match['found_image']
            }
        })
    
    return render_template('results.html', matches=matches_data)

@app.route('/verify_match/<int:match_id>', methods=['POST'])
def verify_match(match_id):
    conn = get_db_connection()
    
    # Get match details
    match = conn.execute('SELECT * FROM matches WHERE id = ?', (match_id,)).fetchone()
    if not match:
        conn.close()
        flash('Match not found')
        return redirect(url_for('results'))
    
    # Get lost and found item details
    lost_item = conn.execute('SELECT * FROM lost_items WHERE id = ?', (match['lost_id'],)).fetchone()
    found_item = conn.execute('SELECT * FROM found_items WHERE id = ?', (match['found_id'],)).fetchone()
    
    # Update match status
    conn.execute('UPDATE matches SET is_verified = 1 WHERE id = ?', (match_id,))
    conn.commit()
    conn.close()
    
    # Send notifications
    lost_email = lost_item['contact_info']
    found_email = found_item['contact_info']
    
    lost_subject = "Good news! Your lost item has been found"
    lost_message = f"Your {lost_item['name']} has been matched with a found item. Contact details: {found_item['contact_info']}"
    
    found_subject = "Match verified for item you found"
    found_message = f"The {found_item['name']} you found has been matched with its owner. Contact details: {lost_item['contact_info']}"
    
    send_notification(lost_email, lost_subject, lost_message)
    send_notification(found_email, found_subject, found_message)
    
    flash('Match verified! Notifications sent to both parties.')
    return redirect(url_for('results'))

if __name__ == '__main__':
    app.run(debug=True)