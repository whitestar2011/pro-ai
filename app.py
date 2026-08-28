import os
import random
import sqlite3
import bcrypt
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey_pro_ai_2026")

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'wav', 'mp3', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

DB = 'users_v2.db'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_greeting():
    lagos_time = datetime.now(ZoneInfo("Africa/Lagos"))
    hour = lagos_time.hour
    if 5 <= hour < 12: return "Good Morning"
    elif 12 <= hour < 18: return "Good Afternoon"
    else: return "Good Evening"

# ========== DATABASE ==========
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                 email TEXT UNIQUE,
                 username TEXT UNIQUE,
                 otp TEXT,
                 password_hash TEXT,
                 is_verified INTEGER,
                 profile_pic TEXT DEFAULT '/static/logo.png',
                 incognito INTEGER DEFAULT 0)''') # 0 = off, 1 = on

    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY,
                 user_id INTEGER,
                 role TEXT,
                 type TEXT DEFAULT 'text',
                 content TEXT,
                 file_url TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 is_pinned INTEGER DEFAULT 0,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()
    delete_old_messages()

def delete_old_messages():
    cutoff = datetime.now() - timedelta(days=90)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE created_at <? AND is_pinned = 0", (cutoff,))
    conn.commit()
    conn.close()

init_db()

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def get_messages(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    user = get_user_by_id(user_id)
    if user and user[7] == 1: # incognito ON = don't load history
        messages = []
    else:
        c.execute("SELECT * FROM messages WHERE user_id=? ORDER BY created_at ASC", (user_id,))
        messages = c.fetchall()
    conn.close()
    return messages

# ========== EMAIL ==========
def send_email(to_email, subject, code, type="login"):
    sender_email = os.environ['GMAIL_EMAIL']
    sender_password = os.environ['GMAIL_PASSWORD']
    msg = MIMEMultipart("alternative")
    msg['From'] = f"Pro AI Security <{sender_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    body = f"<h2>Pro AI Code</h2><p><b style='font-size:24px;'>{code}</b></p>"
    html = f"<html><body>{body}</body></html>"
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())

def detect_login_type(identifier):
    return "email" if re.match(r"[^@]+@[^@]+\.[^@]+", identifier) else "username"

def get_user_by_identifier(identifier, login_type):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE {login_type}=?", (identifier,))
    user = c.fetchone()
    conn.close()
    return user

# ========== AUTH ROUTES ==========
@app.route('/')
def home():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/send_login', methods=['POST'])
def send_login():
    identifier = request.form['identifier']
    login_type = detect_login_type(identifier)
    session['identifier'] = identifier
    session['login_type'] = login_type
    user = get_user_by_identifier(identifier, login_type)
    if login_type == "username":
        if not user or user[4] is None:
            flash("Username not found. Use email first to create account.")
            return redirect(url_for('home'))
        return redirect(url_for('login_password'))
    else:
        code = str(random.randint(100000, 999))
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        if not user:
            c.execute("INSERT INTO users (email, otp, is_verified) VALUES (?,?, 0)", (identifier, code))
        else:
            c.execute("UPDATE users SET otp=? WHERE email=?", (code, identifier))
        conn.commit()
        conn.close()
        send_email(identifier, "Your Pro AI Login Code", code, "login")
        return redirect(url_for('verify_otp'))

@app.route('/login_password', methods=['GET', 'POST'])
def login_password():
    if request.method == 'POST':
        password = request.form['password']
        identifier = session.get('identifier')
        user = get_user_by_identifier(identifier, 'username')
        if user and user[4] and bcrypt.checkpw(password.encode('utf-8'), user[4]):
            session['user_id'] = user[0]
            session['user'] = user[2]
            return redirect(url_for('dashboard'))
        else:
            flash("Wrong password")
    return render_template('login_password.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        code = request.form['otp']
        identifier = session.get('identifier')
        user = get_user_by_identifier(identifier, 'email')
        if user and code == user[3]:
            session['otp_verified'] = True
            session['user_id'] = user[0]
            if user[4] is None:
                return redirect(url_for('set_password'))
            else:
                session['user'] = user[2]
                return redirect(url_for('dashboard'))
        else:
            flash("Wrong code")
    return render_template('verify_otp.html')

@app.route('/set_password', methods=['GET', 'POST'])
def set_password():
    if not session.get('otp_verified'): return redirect(url_for('home'))
    if request.method == 'POST':
        password = request.form['password']
        username = request.form['username']
        user_id = session.get('user_id')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET password_hash=?, username=?, is_verified=1 WHERE id=?", (hashed, username, user_id))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already taken")
            return redirect(url_for('set_password'))
        conn.close()
        session['user'] = username
        return redirect(url_for('dashboard'))
    return render_template('set_password.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        code = str(random.randint(100000, 999))
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("UPDATE users SET otp=? WHERE email=?", (code, email))
        conn.commit()
        conn.close()
        send_email(email, "Pro AI Password Reset", code, "reset")
        session['reset_email'] = email
        return redirect(url_for('reset_password'))
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        code = request.form['otp']
        password = request.form['password']
        email = session.get('reset_email')
        user = get_user_by_identifier(email, 'email')
        if user and code == user[3]:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("UPDATE users SET password_hash=? WHERE email=?", (hashed, email))
            conn.commit()
            conn.close()
            flash("Password reset successful")
            return redirect(url_for('home'))
        else:
            flash("Invalid code")
    return render_template('reset_password.html')

# ========== DASHBOARD + CHAT ==========
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session: return redirect(url_for('home'))
    user = get_user_by_id(session['user_id'])
    messages = get_messages(session['user_id'])
    greeting = get_greeting()
    return render_template('dashboard.html', user=user, messages=messages, greeting=greeting)

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'user_id' not in session: return jsonify({"error": "not logged in"}), 401
    user_id = session['user_id']
    user = get_user_by_id(user_id)

    msg_type = request.form.get('type', 'text')
    content = request.form.get('content', '')
    file_url = None

    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{user_id}_{uuid.uuid4()}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            file_url = f"/static/uploads/{filename}"

    ai_reply = "Got it!"
    if msg_type == 'image': ai_reply = "Got your image! What should I do with it?"
    elif msg_type == 'voice': ai_reply = "I heard your voice note."
    else: ai_reply = f"You said: {content}. I'm Pro-ai and I'm here to help!"

    if user[7] == 0: # Only save if incognito is OFF
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO messages (user_id, role, type, content, file_url) VALUES (?,?,?,?,?)",
                  (user_id, 'user', msg_type, content, file_url))
        c.execute("INSERT INTO messages (user_id, role, type, content) VALUES (?,?,?,?)",
                  (user_id, 'ai', 'text', ai_reply))
        conn.commit()
        conn.close()

    return jsonify({"success": True, "reply": ai_reply})

@app.route('/pin/<int:msg_id>')
def pin_message(msg_id):
    if 'user_id' not in session: return redirect(url_for('home'))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE messages SET is_pinned = 1 WHERE id=? AND user_id=?", (msg_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# ========== SETTINGS ==========
@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session: return redirect(url_for('home'))
    user = get_user_by_id(session['user_id'])
    if request.method == 'POST':
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"user_{user[0]}.png")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("UPDATE users SET profile_pic=? WHERE id=?", (f"/static/uploads/{filename}", user[0]))
                conn.commit()
                conn.close()
                flash("Profile picture updated!")
        return redirect(url_for('dashboard'))
    return render_template('edit_profile.html', user=user)

@app.route('/security-settings')
def security_settings():
    if 'user_id' not in session: return redirect(url_for('home'))
    user = get_user_by_id(session['user_id'])
    return render_template('security.html', user=user)

@app.route('/toggle-incognito')
def toggle_incognito():
    if 'user_id' not in session: return redirect(url_for('home'))
    user = get_user_by_id(session['user_id'])
    new_state = 0 if user[7] == 1 else 1
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET incognito=? WHERE id=?", (new_state, session['user_id']))
    conn.commit()
    conn.close()
    flash("Incognito Mode: " + ("ON - Chats won't be saved" if new_state else "OFF"))
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
