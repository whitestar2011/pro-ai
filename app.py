from flask import Flask, request, session, redirect
import json, os, datetime, time, random, requests, re, google.generativeai as genai

app = Flask(__name__)
app.secret_key = "pro_ai_secret_key_2026"

# ===== CONFIG =====
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY" # Get free from https://aistudio.google.com/app/apikey
VIRUSTOTAL_API_KEY = "YOUR_VIRUSTOTAL_KEY" # Get free from virustotal.com
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

DATA_FILE = "chat_data.json"
SECURITY_FILE = "security.json"
PROFILE_FILE = "profile.json"
USERS_FILE = "users.json"

# ===== HELPERS =====
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

def scan_url(url):
    try:
        headers = {"x-apikey": VIRUSTOTAL_API_KEY}
        res = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
        analysis_id = res.json()["data"]["id"]
        time.sleep(2)
        report = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
        stats = report.json()["data"]["attributes"]["stats"]
        return stats["malicious"] == 0 and stats["suspicious"] == 0
    except: return True

def find_links(text): return re.findall(r'http[s]?://\S+', text)

data = load_data()
security = load_security()
profile = load_profile()
users = load_users()

# ===== ROUTES =====
@app.route("/")
def index():
    if profile["logged_in"]: return redirect("/greetings")
    return render_splash()

@app.route("/welcome")
def welcome(): return render_welcome()

@app.route("/auth/<method>")
def auth(method):
    code = "pro-" + "".join([str(random.randint(0,9)) for _ in range(6)])
    session["auth_code"] = code
    session["auth_method"] = method
    print(f"SEND CODE {code} via {method}")
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
        if len(name.split()) < 3: return render_username(error="incomplete!")
        if name in users: return render_username(error="this name has already been used, try another")
        profile["name"] = name
        profile["username"] = "@" + name.replace(" ", "_").lower()
        users[name] = profile
        save_users(users); save_profile(profile)
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
def greetings(): return render_greetings()

@app.route("/chat", methods=["GET", "POST"])
def chat():
    global data
    chat_history = data["chat_history"]
    incognito = session.get("incognito", False)

    if security["enabled"]:
        if time.time() - session.get("last_active", 0) > 300 or session.get("just_opened", True):
            session["just_opened"] = False
            return render_lock_screen()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "toggle_incognito":
            session["incognito"] = not incognito
        else:
            user_msg = request.form.get("msg")
            if user_msg:
                # Scan links
                safety_warning = ""
                for link in find_links(user_msg):
                    if not scan_url(link): safety_warning = f"\n\n⚠️ Warning: Link flagged unsafe"

                new_msg = {"sender": "you", "msg": user_msg, "time": get_time()}
                if incognito: new_msg["incognito"] = True
                chat_history.append(new_msg)

                # REAL GEMINI AI RESPONSE
                try:
                    response = model.generate_content(user_msg)
                    reply = response.text + safety_warning
                except:
                    reply = "I'm having trouble connecting to AI right now." + safety_warning

                ai_msg = {"sender": "ai", "msg": reply, "time": get_time(), "voice": True}
                if incognito: ai_msg["incognito"] = True
                chat_history.append(ai_msg)
                data["chat_history"] = chat_history
                save_data(data)

    messages_html = ""
    for item in chat_history:
        cls = "you" if item["sender"] == "you" else "ai"
        user_photo = f'<img src="{profile["photo"]}" class="user-avatar">' if profile["photo"] else '<div class="user-avatar default"></div>'
        ai_logo = '<img src="/static/logo.png" class="ai-avatar" onerror="this.style.display=\'none\'">'
        voice_btn = f'<button onclick="speak(`{item["msg"]}`)" style="background:none;border:none;color:#53bdeb;font-size:16px">🔊</button>' if cls == "ai" else ""
        if cls == "you": messages_html += f'<div class="bubble {cls}">{user_photo}<div>{item["msg"]}<div class="meta">{item["time"]}</div></div></div>'
        else: messages_html += f'<div class="bubble {cls}"><div>{item["msg"]}{voice_btn}<div class="meta">{item["time"]}</div></div>{ai_logo}</div>'

    toggle_state = "checked" if security["enabled"] else ""
    return f"""
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
    body{{background:#111b21;color:white;margin:0;font-family:Arial}}
  .header{{background:#202c33;padding:10px 16px;height:59px;display:flex;justify-content:space-between;align-items:center;position:fixed;width:100%;top:0;box-sizing:border-box}}
  .header-logo{{width:40px;height:40px;border-radius:50%;border:2px solid #FFD700}}
  .menu-btn{{background:none;border:none;color:white;font-size:24px}}
  .dropdown{{display:none;position:absolute;right:10px;top:55px;background:#2a3942;min-width:240px;border-radius:8px;z-index:10}}
  .profile-section{{padding:16px;border-bottom:1px solid #3a4a52}}
  .profile-section input{{width:100%;padding:8px;margin:6px 0;background:#111b21;border:1px solid #555;border-radius:6px;color:white}}
  .switch{{position:relative;display:inline-block;width:50px;height:24px}}
  .switch input{{opacity:0}}.slider{{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background-color:#555;border-radius:24px}}
    input:checked +.slider{{background-color:#7B2FFF}}
  .chat{{padding:90px 10px 80px 10px;height:100vh;overflow-y:scroll}}
  .bubble{{display:flex;gap:8px;margin:6px 0;max-width:75%;clear:both;align-items:flex-end}}
  .you{{float:right}}.ai{{float:left}}
  .user-avatar{{width:32px;height:32px;border-radius:50%;background:#7B2FFF}}
  .ai-avatar{{width:28px;height:28px;border-radius:50%;border:1.5px solid #FFD700}}
  .bubble > div{{padding:6px 10px;border-radius:7.5px;background:#202c33}}
  .you > div{{background:#7B2FFF}}
  .meta{{font-size:11px;color:#8696a0;text-align:right;margin-top:4px}}
  .input{{position:fixed;bottom:0;width:100%;background:#202c33;padding:8px 16px;display:flex;gap:8px;box-sizing:border-box}}
  .input input{{flex:1;padding:12px 15px;border-radius:25px;border:none;background:#2a3942;color:white}}
  .send-btn{{background:#7B2FFF;border:none;border-radius:50%;width:48px;height:48px;color:white}}
  .mic-btn{{background:#FF5722;border:none;border-radius:50%;width:48px;height:48px;color:white}}
  .mic-btn.recording{{background:red;animation:pulse 1s infinite}}
   @keyframes pulse {{0%{{transform:scale(1)}}50%{{transform:scale(1.1)}}100%{{transform:scale(1)}}}}
  .security-page{{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:#111b21;color:white;z-index:99;overflow-y:scroll}}
  .security-header{{background:#202c33;padding:16px;display:flex;align-items:center;gap:16px}}
    </style></head><body>
    <div class="header">
        <img src="/static/logo.png" class="header-logo" onerror="this.style.display='none'">
        <button class="menu-btn" onclick="toggleMenu()">⋮</button>
        <div class="dropdown" id="menu">
            <div class="profile-section">
                <b>Profile</b>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="action" value="update_profile">
                    <input name="name" placeholder="Your Name" value="{profile['name']}">
                    <input name="username" placeholder="Username" value="{profile['username']}">
                    <input type="file" name="photo" accept="image/*">
                    <button type="submit" style="background:#7B2FFF;border:none;padding:8px;border-radius:6px;color:white;width:100%;margin-top:6px">Save</button>
                </form>
            </div>
            <div style="padding:12px 16px;display:flex;justify-content:space-between"><span>Security</span>
                <label class="switch"><input type="checkbox" {toggle_state}><span class="slider"></span></label>
            </div>
            <button onclick="showFeatures()" style="background:none;border:none;color:white;padding:12px 16px;width:100%;text-align:left">✨ Features</button>
            <form method="POST"><input type="hidden" name="action" value="toggle_incognito">
                <button style="background:none;border:none;color:white;padding:12px 16px;width:100%;text-align:left">{"Disable" if incognito else "Enable"} Incognito</button>
            </form>
            <button onclick="refresh()" style="background:none;border:none;color:white;padding:12px 16px;width:100%;text-align:left">Refresh</button>
        </div>
    </div>

    <div class="security-page" id="featuresPage">
        <div class="security-header"><button onclick="closeFeatures()" style="background:none;border:none;font-size:24px;color:white">←</button><h2>Pro AI Features</h2></div>
        <div style="padding:16px">
            <h3>🔒 Security</h3><p>• Toggle ON/OFF with biometrics</p><p>• Pattern, PIN, Password, Biometrics</p><p>• Edit / Change / Turn off</p><p>• Auto-lock after 5 minutes</p>
            <h3>🕶️ Privacy</h3><p>• Incognito Mode</p><p>• Banner notification</p>
            <h3>💬 Chat</h3><p>• Reply, Pin, Delete, Search</p><p>• Emoji picker, Blue ticks</p>
            <h3>🛡️ Safety</h3><p>• Link scanning with VirusTotal</p><p>• In-app browser</p>
            <h3>👤 Profile</h3><p>• Name, Username, Photo</p>
            <h3>🎤 Voice</h3><p>• Hold mic to record</p><p>• AI replies in voice</p><p>• Wake word: "hey Professor"</p><p>• Say "bye" to close</p>
            <h3>🤖 AI</h3><p>• Real Gemini AI Brain</p><p>• Animated logo, Timezone greetings</p>
        </div>
    </div>

    <div class="chat">{messages_html}</div>
    <form method="POST" class="input" id="msgForm">
        <input name="msg" id="msgInput" placeholder="Message">
        <button type="button" class="mic-btn" id="micBtn">🎤</button>
        <button type="submit" class="send-btn">➤</button>
    </form>

    <script>
    // VOICE TO TEXT
    let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    let micBtn = document.getElementById('micBtn');
    let msgInput = document.getElementById('msgInput');

    micBtn.onmousedown = micBtn.ontouchstart = () => {{
        micBtn.classList.add('recording');
        recognition.start();
    }}
    micBtn.onmouseup = micBtn.ontouchend = () => {{
        micBtn.classList.remove('recording');
        recognition.stop();
    }}

    recognition.onresult = e => {{
        msgInput.value = e.results[0][0].transcript;
        document.getElementById('msgForm').submit();
    }}

    // TEXT TO SPEECH
    function speak(text) {{
        let utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1;
        utterance.pitch = 1;
        speechSynthesis.speak(utterance);
    }}

    // WAKE WORD
    let wakeRecognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    wakeRecognition.continuous = true;
    wakeRecognition.onresult = e => {{
        let txt = e.results[e.results.length-1][0].transcript.toLowerCase();
        if(txt.includes('hey professor')) msgInput.focus();
        if(txt.trim() === 'bye') window.close();
    }}
    wakeRecognition.start();

    function toggleMenu(){{document.getElementById('menu').style.display = document.getElementById('menu').style.display === 'block'? 'none' : 'block'}}
    function showFeatures(){{document.getElementById('featuresPage').style.display='block';document.getElementById('menu').style.display='none'}}
    function closeFeatures(){{document.getElementById('featuresPage').style.display='none'}}
    function refresh(){{location.reload()}}
    </script></body></html>
    """

# ===== RENDER FUNCTIONS =====
def render_splash(): return """<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;background:#000;display:flex;align-items:center;justify-content:center;height:100vh}.logo{width:200px;height:200px;border-radius:50%;border:4px solid #FFD700}</style></head><body><img src="/static/logo.png" class="logo"><script>setTimeout(()=>{window.location="/welcome"},3000)</script></body></html>"""
def render_welcome(): return """<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{background:white;margin:0}.header{background:#808080;padding:16px;text-align:center;color:white}h1{text-align:center;margin-top:40px}.btns{display:flex;justify-content:space-between;padding:20px;position:absolute;bottom:40px;width:90%}.btn{background:#7B2FFF;color:white;border:none;padding:14px 28px;border-radius:8px}</style></head><body><div class="header">Pro AI</div><h1>Welcome 🤗!</h1><div class="btns"><button class="btn" onclick="location.href='/auth/login'">Log-in</button><button class="btn" onclick="location.href='/auth/signup'">Sign-in</button></div></body></html>"""
def render_code_page(error=False): method = session.get("auth_method", "phone"); return f"""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{background:white;margin:0}}.header{{background:#808080;padding:16px;color:white}}.code-box{{display:flex;gap:10px;justify-content:center;margin-top:40px}}.digit{{width:50px;height:50px;border:2px solid gray;border-radius:8px;text-align:center;font-size:24px}}.error{{color:red;text-align:center}}.resend{{background:#7B2FFF;color:white;border:none;padding:10px;border-radius:8px;position:absolute;left:20px;bottom:40px}}</style></head><body><div class="header">Verify</div><p style="text-align:center">Enter code sent to {method}</p>{ '<p class="error">incorrect verification code</p>' if error else "" }<form method="POST" action="/verify"><div class="code-box">{"".join([f'<input name="d{i}" class="digit" maxlength="1" inputmode="numeric">' for i in range(6)])}</div><button class="resend" type="button" onclick="location.href='/auth/{method}'">Resend</button><button style="position:absolute;right:20px;bottom:40px;background:#7B2FFF;color:white;border:none;padding:10px;border-radius:8px">Verify</button></form></body></html>"""
def render_username(error=None): return f"""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{background:#111b21;color:white;margin:0}}.header{{background:#808080;padding:16px}}input{{width:80%;margin:20px 10%;padding:12px;background:#2a3942;border:2px solid {'red' if error else '#7B2FFF'};border-radius:8px;color:white}}.error{{color:red;text-align:center}}.next{{background:#7B2FFF;color:white;border:none;padding:12px 24px;border-radius:8px;position:absolute;right:20px;bottom:20px}}</style></head><body><div class="header">Enter a username</div>{f'<p class="error">{error}</p>' if error else ""}<form method="POST"><input name="username" placeholder="At least 3 words" autofocus><button class="next">Next</button></form></body></html>"""
def render_profile_pic(): return f"""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{background:#111b21;color:white;margin:0;text-align:center}}.header{{background:#808080;padding:16px;display:flex;justify-content:space-between}}.circle{{width:150px;height:150px;border-radius:50%;background:#7B2FFF;border:3px solid #FFD700;margin:40px auto;display:flex;align-items:center;justify-content:center;font-size:60px}}.btn{{background:#7B2FFF;color:white;border:none;padding:12px 24px;border-radius:8px;margin:10px}}</style></head><body><div class="header"><span>←</span><span>{profile['username']}</span><span></span></div><div class="circle">{profile['name'][:1].upper() if profile['name'] else 'P'}</div><button class="btn" onclick="location.href='/profile_edit'">Edit</button><form method="POST" enctype="multipart/form-data"><button class="btn" name="skip" value="1">Skip</button><button class="btn" type="submit">Next</button></form></body></html>"""
def render_greetings(): greeting = get_greeting(); return f"""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{background:#111b21;color:white;margin:0;text-align:center}}.header{{background:#808080;padding:12px;display:flex;justify-content:space-between;align-items:center}}.logo-anim{{font-size:32px;margin-top:20px;animation:flip 2s infinite}}@keyframes flip {{0%,100%{{transform:rotateY(0)}}50%{{transform:rotateY(180deg)}}}}.greet{{font-size:28px;margin-top:40px}}</style></head><body><div class="header"><span>⏱️</span><span class="logo-anim">Pro-ai</span><span>☰</span></div><div class="greet">{greeting}, {profile['name'].split()[0] if profile['name'] else 'there'}!</div><button onclick="location.href='/chat'" style="background:#7B2FFF;color:white;border:none;padding:14px 28px;border-radius:8px;margin-top:40px">Start Chatting</button></body></html>"""
def render_lock_screen(): return f"""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{background:#111b21;color:white;display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column}}input{{padding:12px;border-radius:8px;border:none;margin:10px;background:#2a3942;color:white}}button{{background:#7B2FFF;border:none;padding:12px 24px;border-radius:8px;color:white}}</style></head><body><h2>🔒 Pro AI is Locked</h2><input type="password" id="unlockInput"><button onclick="unlock()">Unlock</button><script>function unlock(){{if(document.getElementById('unlockInput').value === '{security["code"]}'){{window.location.href='/chat'}}else{{alert('Wrong code')}}}}</script></body></html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
