import os
import random
import sqlite3
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

DB = 'users.db'

# ========== DATABASE ==========
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # email for OTP, username for password login
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, 
                 email TEXT UNIQUE, 
                 username TEXT UNIQUE,
                 otp TEXT, 
                 password_hash TEXT, 
                 is_verified INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# ========== EMAIL FUNCTION ==========
def send_email(to_email, subject, code, type="login"):
    sender_email = os.environ['GMAIL_EMAIL']
    sender_password = os.environ['GMAIL_PASSWORD']
    
    msg = MIMEMultipart("alternative")
    msg['From'] = f"Pro AI Security <{sender_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    if type == "login":
        body = f"<h2>Pro AI Login Code</h2><p>Your code: <b style='font-size:24px; letter-spacing:5px;'>{code}</b></p><p>Expires in 10 minutes.</p>"
    elif type == "reset":
        body = f"<h2>Password Reset Request</h2><p>Someone requested to reset your Pro AI password.</p><p>Code: <b style='font-size:24px; letter-spacing:5px;'>{code}</b></p><p>If this wasn't you, ignore this email.</p>"
    elif type == "security":
        body = f"<h2>Security Alert</h2><p>Your Pro AI password was just changed.</p><p>If this wasn't you, please reset your password immediately.</p>"

    html = f"<html><body style='font-family: Arial; background:#f6f9fc;'><div style='max-width: 500px; margin: 20px auto; padding: 30px; border-radius: 12px; background:white;'>{body}</div></body></html>"
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())


def detect_login_type(identifier):
    if re.match(r"[^@]+@[^@]+\.[^@]+", identifier): return "email"
    else: return "username"

def get_user_by_identifier(identifier, login_type):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE {login_type}=?", (identifier,))
    user = c.fetchone()
    conn.close()
    return user

# ========== ROUTES ==========
@app.route('/')
def home():
    if 'user' in session:
        return render_template('dashboard.html')
    return render_template('login.html') # 1 page for email/username

@app.route('/send_login', methods=['POST'])
def send_login():
    identifier = request.form['identifier']
    login_type = detect_login_type(identifier)
    session['identifier'] = identifier
    session['login_type'] = login_type
    
    user = get_user_by_identifier(identifier, login_type)

    if login_type == "username":
        if not user or user[4] is None: # password_hash column
            flash("Username not found or no password set. Use email first to create account.")
            return redirect(url_for('home'))
        return redirect(url_for('login_password')) # Go to password page
    
    else: # email
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
            session['user'] = identifier
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
        
        if user and code == user[3]: # otp column
            session['otp_verified'] = True
            session['user_id'] = user[0]
            if user[4] is None: # no password yet
                return redirect(url_for('set_password'))
            else:
                session['user'] = identifier
                return redirect(url_for('dashboard'))
        else:
            flash("Wrong code")
    return render_template('verify_otp.html')

@app.route('/set_password', methods=['GET', 'POST'])
def set_password():
    if not session.get('otp_verified'):
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        password = request.form['password']
        username = request.form['username'] # Let them pick username here
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
        
        # SECURITY EMAIL
        c.execute("SELECT email FROM users WHERE id=?", (user_id,))
        email = c.fetchone()[0]
        send_email(email, "Pro AI Security Alert", "", "security")
            
        session['user'] = username
        return redirect(url_for('dashboard'))
    return render_template('set_password.html')

# ========== FORGOT PASSWORD ==========
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
            send_email(email, "Pro AI Security Alert", "", "security") # alert
            flash("Password reset successful")
            return redirect(url_for('home'))
        else:
            flash("Invalid code")
    return render_template('reset_password.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)
