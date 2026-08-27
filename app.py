from flask import Flask, request, session, redirect
import json, os, datetime, time, random

app = Flask(__name__)
app.secret_key = "pro_ai_secret_key_2026"
DATA_FILE = "chat_data.json"
SECURITY_FILE = "security.json"
PROFILE_FILE = "profile.json"
USERS_FILE = "users.json"

def load_data(): return json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else {"chat_history": [], "pinned": False}
def save_data(d): json.dump(d, open(DATA_FILE, "w"))
def load_security(): return json.load(open(SECURITY_FILE)) if os.path.exists(SECURITY_FILE) else {"enabled": False, "type": "none", "code": "", "biometric": False}
def save_security(s): json.dump(s, open(SECURITY_FILE, "w"))
def load_profile(): return json.load(open(PROFILE_FILE)) if os.path.exists(PROFILE_FILE) else {"name": "", "username": "", "photo": "", "logged_in": False}
def save_profile(p): json.dump(p, open(PROFILE_FILE, "w"))
def load_users(): return json.load(open(USERS_FILE)) if os.path.exists(USERS_FILE) else {}
def save_users(u): json.dump(u, open(USERS_FILE, "w"))

def get_time(): return datetime.datetime.now().strftime("%I:%M %p")
def get_greeting():
    h = datetime.datetime.now().hour
    return "Good Morning" if h < 12 else "Good Afternoon" if h < 18 else "Good Evening"

data = load_data()
security = load_security()
profile = load_profile()
users = load_users()

@app.route("/")
def index():
    if profile["logged_in"]:
        return redirect("/greetings")
    return render_splash()

@app.route("/welcome")
def welcome():
    return render_welcome()

@app.route("/auth/<method>")
def auth(method):
    code = "pro-" + "".join([str(random.randint(0,9)) for _ in range(6)])
    session["auth_code"] = code
    session["auth_method"] = method
    print(f"SEND CODE {code} via {method}") # In real app: send SMS/Email/WhatsApp
    return render_code_page()

@app.route("/verify", methods=["POST"])
def verify():
    entered = "".join([request.form.get(f"d{i}", "") for i in range(6)])
    if entered == session.get("auth_code", "")[4:]:
        return redirect("/username")
    return render_code_page(error=True)

@app.route("/username", methods=["GET", "POST"])
def username():
    if request.method == "POST":
        name = request.form.get("username")
        if len(name.split()) < 3:
            return render_username(error="incomplete!")
        if name in users:
            return render_username(error="this name has already been used, try another")
        profile["name"] = name
        profile["username"] = "@" + name.replace(" ", "_").lower()
        users[name] = profile
        save_users(users)
        save_profile(profile)
        return redirect("/profile_pic")
    return render_username()

@app.route("/profile_pic", methods=["GET", "POST"])
def profile_pic():
    if request.method == "POST":
        if request.files.get("photo"):
            request.files["photo"].save("static/user.jpg")
            profile["photo"] = "/static/user.jpg"
        profile["logged_in"] = True
        save_profile(profile)
        return redirect("/greetings")
    return render_profile_pic()

@app.route("/greetings")
def greetings():
    return render_greetings()

@app.route("/chat", methods=["GET", "POST"])
def chat():
    # Full chat logic here - same as before with wake word
    return "Chat page"

def render_splash():
    return """
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{margin:0;background:#000;display:flex;align-items:center;justify-content:center;height:100vh}
   .logo{width:200px;height:200px;border-radius:50%;border:4px solid #FFD700}</style>
    </head><body><img src="/static/logo.png" class="logo">
    <script>setTimeout(()=>{window.location="/welcome"},3000)</script></body></html>
    """

def render_welcome():
    return """
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{background:white;margin:0;font-family:Arial}
   .header{background:#808080;padding:16px;text-align:center;color:white}
    h1{text-align:center;margin-top:40px}
   .btns{display:flex;justify-content:space-between;padding:20px;position:absolute;bottom:40px;width:90%}
   .btn{background:#7B2FFF;color:white;border:none;padding:14px 28px;border-radius:8px}</style>
    </head><body>
    <div class="header">Pro AI</div>
    <h1>Welcome 🤗!</h1>
    <div class="btns">
        <button class="btn" onclick="location.href='/auth/login'">Log-in</button>
        <button class="btn" onclick="location.href='/auth/signup'">Sign-in</button>
    </div></body></html>
    """

def render_code_page(error=False):
    method = session.get("auth_method", "phone")
    return f"""
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{{background:white;margin:0;font-family:Arial}}
   .header{{background:#808080;padding:16px;color:white}}
   .code-box{{display:flex;gap:10px;justify-content:center;margin-top:40px}}
   .digit{{width:50px;height:50px;border:2px solid gray;border-radius:8px;text-align:center;font-size:24px}}
   .error{{color:red;text-align:center}}
   .resend{{background:#7B2FFF;color:white;border:none;padding:10px;border-radius:8px;position:absolute;left:20px;bottom:40px}}</style>
    </head><body>
    <div class="header">Verify</div>
    <p style="text-align:center">Enter code sent to {method}</p>
    { '<p class="error">incorrect verification code</p>' if error else "" }
    <form method="POST" action="/verify">
    <div class="code-box">
        {"".join([f'<input name="d{i}" class="digit" maxlength="1" inputmode="numeric">' for i in range(6)])}
    </div>
    <button class="resend" type="button" onclick="location.href='/auth/{method}'">Resend</button>
    <button style="position:absolute;right:20px;bottom:40px;background:#7B2FFF;color:white;border:none;padding:10px;border-radius:8px">Verify</button>
    </form></body></html>
    """

def render_username(error=None):
    return f"""
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{{background:#111b21;color:white;margin:0;font-family:Arial}}
   .header{{background:#808080;padding:16px}}
    input{{width:80%;margin:20px 10%;padding:12px;background:#2a3942;border:2px solid {'red' if error else '#7B2FFF'};border-radius:8px;color:white}}
   .error{{color:red;text-align:center}}
   .next{{background:#7B2FFF;color:white;border:none;padding:12px 24px;border-radius:8px;position:absolute;right:20px;bottom:20px}}</style>
    </head><body>
    <div class="header">Enter a username</div>
    {f'<p class="error">{error}</p>' if error else ""}
    <form method="POST"><input name="username" placeholder="At least 3 words" autofocus>
    <button class="next">Next</button></form></body></html>
    """

def render_profile_pic():
    return f"""
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{{background:#111b21;color:white;margin:0;text-align:center}}
   .header{{background:#808080;padding:16px;display:flex;justify-content:space-between}}
   .circle{{width:150px;height:150px;border-radius:50%;background:#7B2FFF;border:3px solid #FFD700;margin:40px auto;display:flex;align-items:center;justify-content:center;font-size:60px}}
   .btn{{background:#7B2FFF;color:white;border:none;padding:12px 24px;border-radius:8px;margin:10px}}</style>
    </head><body>
    <div class="header"><span>←</span><span>{profile['username']}</span><span></span></div>
    <div class="circle">{profile['name'][:1].upper() if profile['name'] else 'P'}</div>
    <button class="btn" onclick="location.href='/profile_edit'">Edit</button>
    <form method="POST" enctype="multipart/form-data">
        <button class="btn" name="skip" value="1">Skip</button>
        <button class="btn" type="submit">Next</button>
    </form></body></html>
    """

def render_greetings():
    greeting = get_greeting()
    return f"""
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{{background:#111b21;color:white;margin:0;text-align:center;font-family:Arial}}
   .header{{background:#808080;padding:12px;display:flex;justify-content:space-between;align-items:center}}
   .logo-anim{{font-size:32px;margin-top:20px;animation:flip 2s infinite}}
    @keyframes flip {{0%,100%{{transform:rotateY(0)}}50%{{transform:rotateY(180deg)}}}}
   .greet{{font-size:28px;margin-top:40px}}
   .menu{{position:fixed;top:0;left:0;width:80%;height:100%;background:#2a3942;display:none;z-index:50}}</style>
    </head><body>
    <div class="header">
        <span onclick="openMenu()">⏱️</span>
        <span class="logo-anim">Pro-ai</span>
        <span onclick="openMenu()">☰</span>
    </div>
    <div class="greet">{greeting}, {profile['name'].split()[0] if profile['name'] else 'there'}!</div>

    <div class="menu" id="sideMenu">
        <div style="padding:20px">
            <button onclick="closeMenu()">New Conversation</button><br><br>
            <button>Pinned Chats</button><br><br>
            <button>Sessions</button>
        </div>
    </div>

    <script>
    function openMenu(){{document.getElementById('sideMenu').style.display='block'}}
    function closeMenu(){{document.getElementById('sideMenu').style.display='none'}}
    // Wake word listener
    let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.onresult = e => {{
        if(e.results[0][0].transcript.toLowerCase().includes('hey professor')) location.href='/chat';
        if(e.results[0][0].transcript.toLowerCase() === 'bye') window.close();
    }}
    recognition.start();
    </script></body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
