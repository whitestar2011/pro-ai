from flask import Flask, request, session
import json, os, datetime, time

app = Flask(__name__)
app.secret_key = "pro_ai_secret_key_2026"
DATA_FILE = "chat_data.json"
SECURITY_FILE = "security.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"chat_history": [], "pinned": False}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_security():
    if os.path.exists(SECURITY_FILE):
        with open(SECURITY_FILE, "r") as f:
            return json.load(f)
    return {"enabled": False, "type": "none", "code": "", "biometric": False}

def save_security(sec):
    with open(SECURITY_FILE, "w") as f:
        json.dump(sec, f)

def get_time():
    return datetime.datetime.now().strftime("%I:%M %p")

data = load_data()
security = load_security()

@app.route("/", methods=["GET", "POST"])
def home():
    global data, security
    chat_history = data["chat_history"]
    pinned = data["pinned"]
    search_query = request.args.get("search", "")
    incognito = session.get("incognito", False)
    sec_page = request.args.get("sec_page", "")

    if request.method == "POST":
        action = request.form.get("action")
        if action == "toggle_security":
            if request.form.get("state") == "true":
                return "open_security_page"
            else: # turning off
                if security["biometric"]:
                    session["need_bio_to_disable"] = True
                    return "need_biometric"
                security["enabled"] = False
                security["type"] = "none"
                save_security(security)
        elif action == "set_security":
            security["enabled"] = True
            security["type"] = request.form.get("sec_type")
            security["code"] = request.form.get("sec_code")
            save_security(security)
        elif action == "set_biometric":
            security["biometric"] = True
            save_security(security)
        elif action == "change_security_type":
            new_type = request.form.get("new_type")
            if security["biometric"]:
                session["need_bio_to_change"] = new_type
                return "need_biometric"
            security["type"] = new_type
            security["code"] = ""
            save_security(security)
        elif action == "toggle_incognito":
            session["incognito"] = not incognito
            session["last_active"] = time.time()
        elif action == "refresh":
            pass
        else:
            user_msg = request.form.get("msg")
            if user_msg:
                new_msg = {"sender": "you", "msg": user_msg, "time": get_time(), "ticks": 1, "timestamp": time.time()}
                if incognito: new_msg["incognito"] = True
                chat_history.append(new_msg)
                reply = "Incognito Mode: I won't save this." if incognito else f"Got it: {user_msg}"
                chat_history[-1]["ticks"] = 2
                ai_msg = {"sender": "ai", "msg": reply, "time": get_time(), "ticks": 0, "timestamp": time.time()}
                if incognito: ai_msg["incognito"] = True
                chat_history.append(ai_msg)
                data["chat_history"] = chat_history
                save_data(data)

    locked = False
    if security["enabled"]:
        last_active = session.get("last_active", 0)
        if time.time() - last_active > 300:
            locked = True

    filtered_chat = [msg for msg in chat_history if search_query.lower() in msg["msg"].lower()] if search_query else chat_history

    messages_html = ""
    for i, item in enumerate(filtered_chat):
        original_index = chat_history.index(item)
        cls = "you" if item["sender"] == "you" else "ai"
        messages_html += f'<div class="bubble {cls}" data-index="{original_index}" data-msg="{item["msg"]}">{item["msg"]}<div class="meta">{item["time"]}</div></div>'

    incognito_text = '<div class="incognito-banner" id="incognitoBanner">🕶️ You are on Incognito Mode</div>' if incognito else ""
    toggle_state = "checked" if security["enabled"] else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #111b21; color: white; font-family: Arial; margin: 0; }}
.lock-screen {{ display: { 'flex' if locked else 'none' }; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #111b21; z-index: 100; align-items: center; justify-content: center; flex-direction: column; }}
.header {{ background: #202c33; padding: 10px 16px; height: 59px; display: flex; justify-content: space-between; align-items: center; position: fixed; width: 100%; top: 0; }}
.menu-btn {{ background: none; border: none; color: white; font-size: 24px; }}
.dropdown {{ display: none; position: absolute; right: 10px; top: 55px; background: #2a3942; min-width: 220px; }}
.dropdown-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; }}
.switch {{ position: relative; display: inline-block; width: 50px; height: 24px; }}
.switch input {{ opacity: 0; width: 0; height: 0; }}
.slider {{ position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #555; transition:.4s; border-radius: 24px; }}
.slider:before {{ position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition:.4s; border-radius: 50%; }}
input:checked +.slider {{ background-color: #7B2FFF; }}
input:checked +.slider:before {{ transform: translateX(26px); }}
.security-page {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: white; color: black; z-index: 99; }}
.security-header {{ background: white; color: black; padding: 16px; display: flex; align-items: center; gap: 16px; }}
.security-option {{ padding: 16px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; justify-content: space-between; }}
.black-page {{ background: #111b21; color: white; }}
.pattern-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; width: 300px; margin: 50px auto; }}
.dot {{ width: 20px; height: 20px; background: white; border-radius: 50%; }}
.btn {{ background: #7B2FFF; color: white; border: none; padding: 12px 24px; border-radius: 8px; position: absolute; bottom: 20px; right: 20px; }}
.biometric-sheet {{ position: fixed; bottom: 0; left: 0; width: 100%; height: 50%; background: #111b21; border-radius: 20px 20px 0 0; padding: 20px; display: none; }}
.chat {{ padding: 90px 10px 80px 10px; height: 100vh; overflow-y: scroll; }}
.bubble {{ padding: 6px 7px; border-radius: 7.5px; margin: 6px 0; max-width: 65%; clear: both; }}
.you {{ background: #7B2FFF; float: right; }}
.ai {{ background: #202c33; float: left; }}
.incognito-banner {{ background: #FF5722; text-align: center; padding: 6px; position: fixed; top: 59px; width: 100%; display: none; }}
.input {{ position: fixed; bottom: 0; width: 100%; background: #202c33; padding: 8px 16px; }}
    </style>
    </head>
    <body>
        <div class="lock-screen" id="lockScreen">
            <h2>Unlock Pro AI</h2>
            <input type="password" id="unlockInput">
            <button onclick="unlock()">Unlock</button>
        </div>

        <div class="security-page" id="securityPage">
            <div class="security-header">
                <button onclick="closeSecurity()" style="background:none;border:none;font-size:24px">←</button>
                <h2>Security</h2>
            </div>
            <div class="security-option" onclick="startPattern()">Pattern</div>
            <div class="security-option" onclick="startPassword()">Password</div>
            <div class="security-option" onclick="startPin()">PIN</div>
            <div class="security-option" onclick="startBiometric()">Biometrics</div>
            { '<div class="security-option" onclick="openOthers()">Others →</div>' if security["enabled"] else "" }
        </div>

        <div class="security-page black-page" id="othersPage">
            <div class="security-header black-page">
                <button onclick="closeOthers()" style="background:none;border:none;font-size:24px;color:white">←</button>
                <h2>Others</h2>
            </div>
            <div class="security-option" onclick="editSecurity()">Edit Security</div>
            <div class="security-option" onclick="changeSecurity()">Change Security</div>
            <div class="security-option" onclick="turnOffSecurity()">Turn Off Security</div>
        </div>

        <div class="security-page black-page" id="changePage">
            <div class="security-header black-page">
                <button onclick="closeChange()" style="background:none;border:none;font-size:24px;color:white">←</button>
                <h2>Change Security Type</h2>
            </div>
            <div class="security-option" onclick="setNewType('pin')">Pattern/Password → PIN</div>
            <div class="security-option" onclick="setNewType('password')">Pattern/PIN → Password</div>
            <div class="security-option" onclick="setNewType('pattern')">Password/PIN → Pattern</div>
        </div>

        <div class="biometric-sheet" id="bioSheet">
            <h3>Authenticate</h3>
            <p>Use fingerprint to continue</p>
            <p style="font-size:12px;opacity:0.7">Note: chat locks after 5 minutes of inactivity or when opening the app</p>
            <button onclick="verifyBiometric()">Verify</button>
            <button onclick="closeBiometric()">Cancel</button>
        </div>

        <div class="header">
            <span>Pro AI</span>
            <button class="menu-btn" onclick="toggleMenu()">⋮</button>
            <div class="dropdown" id="menu">
                <div class="dropdown-row">
                    <span>Security</span>
                    <label class="switch">
                        <input type="checkbox" {toggle_state} onchange="toggleSecurity(this)">
                        <span class="slider"></span>
                    </label>
                </div>
                <button onclick="toggleIncognito()">{"Disable" if incognito else "Enable"} Incognito</button>
                <button onclick="refresh()">Refresh</button>
                <button>{ "Unpin Chat" if pinned else "Pin Chat"}</button>
            </div>
        </div>
        {incognito_text}
        <div class="chat" id="chat" onscroll="showIncognitoBanner()">{messages_html}</div>
        <form method="POST" class="input">
            <input name="msg" placeholder="Message">
            <button type="submit" style="background:#7B2FFF;border:none;border-radius:50%;width:48px;height:48px;color:white">➤</button>
        </form>

    <script>
    let bioAction = "";

    function toggleSecurity(toggle) {{
        let form = document.createElement('form');
        form.method = 'POST';
        form.innerHTML = `<input name="action" value="toggle_security"><input name="state" value="${{toggle.checked}}">`;
        document.body.appendChild(form);
        let result = form.submit();
        if(toggle.checked) openSecurity();
        else if('{security["biometric"]}' === 'True') openBiometric('disable');
    }}

    function openSecurity() {{
        document.getElementById('securityPage').style.display = 'block';
        document.getElementById('menu').style.display = 'none';
    }}
    function closeSecurity() {{ document.getElementById('securityPage').style.display = 'none'; }}
    function openOthers() {{ document.getElementById('othersPage').style.display = 'block'; }}
    function closeOthers() {{ document.getElementById('othersPage').style.display = 'none'; }}
    function changeSecurity() {{ document.getElementById('changePage').style.display = 'block'; }}
    function closeChange() {{ document.getElementById('changePage').style.display = 'none'; }}

    function editSecurity() {{
        alert('Enter old ' + '{security["type"]}' + ' first, then set new one');
        openSecurity();
    }}

    function turnOffSecurity() {{
        if('{security["biometric"]}' === 'True') openBiometric('disable');
        else {{
            let form = document.createElement('form');
            form.method = 'POST';
            form.innerHTML = '<input name="action" value="toggle_security"><input name="state" value="false">';
            document.body.appendChild(form);
            form.submit();
        }}
    }}

    function setNewType(type) {{
        if('{security["biometric"]}' === 'True') openBiometric('change_' + type);
        else {{
            let form = document.createElement('form');
            form.method = 'POST';
            form.innerHTML = `<input name="action" value="change_security_type"><input name="new_type" value="${{type}}">`;
            document.body.appendChild(form);
            form.submit();
        }}
    }}

    function openBiometric(action) {{
        bioAction = action;
        document.getElementById('bioSheet').style.display = 'block';
    }}
    function closeBiometric() {{ document.getElementById('bioSheet').style.display = 'none'; }}

    function verifyBiometric() {{
        if(bioAction === 'disable') {{
            let form = document.createElement('form');
            form.method = 'POST';
            form.innerHTML = '<input name="action" value="toggle_security"><input name="state" value="false">';
            document.body.appendChild(form);
            form.submit();
        }} else if(bioAction.startsWith('change_')) {{
            let newType = bioAction.split('_')[1];
            let form = document.createElement('form');
            form.method = 'POST';
            form.innerHTML = `<input name="action" value="change_security_type"><input name="new_type" value="${{newType}}">`;
            document.body.appendChild(form);
            form.submit();
        }}
        closeBiometric();
    }}

    function unlock() {{
        if(document.getElementById('unlockInput').value === '{security["code"]}') {{
            document.getElementById('lockScreen').style.display = 'none';
        }}
    }}

    function toggleMenu() {{
        document.getElementById('menu').style.display = document.getElementById('menu').style.display === 'block'? 'none' : 'block';
    }}

    function showIncognitoBanner() {{
        if({str(incognito).lower()}) {{
            document.getElementById('incognitoBanner').style.display = 'block';
            setTimeout(() => document.getElementById('incognitoBanner').style.display = 'none', 5000);
        }}
    }}
    showIncognitoBanner();
    </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
