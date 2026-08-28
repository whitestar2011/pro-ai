import os
import sqlite3
import random
import bcrypt
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, session, send_from_directory
from gtts import gTTS
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "proai_secret_key_change_this")
DB = 'users_v2.db'

# ===== GEMINI SETUP - PUT YOUR KEY ON LINE 16 =====
GEMINI_API_KEY = "AIzaSyD2IDPgY3fF7yqfhMq2nXNwcXyq9-8I8NY"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
# ==================================================

# ===== DB INIT =====
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, username TEXT UNIQUE, 
                  otp TEXT, password_hash TEXT, is_verified INTEGER, profile_pic TEXT, incognito INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY, user_id INTEGER, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
init_db()

def send_otp_email(to_email, otp):
    # your email sending code
    pass

# ===== ROUTES =====
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/send_login', methods=['POST'])
def send_login():
    data = request.json
    email = data.get('email')
    otp = str(random.randint(100000, 999999))
    
    user = get_user_by_identifier(email, 'email')
    if user:
        # existing user
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("UPDATE users SET otp=? WHERE email=?", (otp, email))
        conn.commit(); conn.close()
    else:
        # new user
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("INSERT INTO users (email, otp, is_verified, incognito) VALUES (?, ?, 0, 0)", (email, otp))
        conn.commit(); conn.close()
    
    send_otp_email(email, otp)
    return jsonify({"status": "otp_sent"})

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    # your verify otp code
    session['session_id'] = request.json.get('email')
    return jsonify({"status": "logged_in"})

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'session_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_text = request.form.get('text', '')
    
    # 1. GET REAL GEMINI REPLY
    try:
        response = model.generate_content(user_text)
        ai_text = response.text
    except Exception as e:
        print("Gemini Error:", e)
        ai_text = "⚠️ Sorry bro, Gemini is down right now"
    
    # 2. CONVERT TO VOICE
    tts = gTTS(text=ai_text, lang='en')
    os.makedirs('static/uploads', exist_ok=True)
    audio_path = f"static/uploads/ai_{random.randint(1000,9999)}.mp3"
    tts.save(audio_path)
    
    return jsonify({
        "user_text": user_text,
        "ai_text": ai_text,
        "audio_url": "/" + audio_path,
        "status": "success"
    })

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({"status": "logged_out"})

def get_user_by_identifier(identifier, login_type):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE {login_type}=?", (identifier,))
    user = c.fetchone()
    conn.close()
    return user

if __name__ == '__main__':
    app.run(debug=True)
