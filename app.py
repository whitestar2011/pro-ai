from flask import Flask, request
import json, os, datetime

app = Flask(__name__)
DATA_FILE = "chat_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"chat_history": [], "pinned": False}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_time():
    return datetime.datetime.now().strftime("%I:%M %p") # 9:36 AM

data = load_data()

@app.route("/", methods=["GET", "POST"])
def home():
    global data
    chat_history = data["chat_history"]
    pinned = data["pinned"]
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "pin":
            data["pinned"] = not pinned
            save_data(data)
        elif action == "delete":
            data["chat_history"] = []
            data["pinned"] = False
            save_data(data)
        else:
            user_msg = request.form.get("msg")
            reply_to = request.form.get("reply_to")
            if user_msg:
                # First add with 1 tick = sent
                chat_history.append({"sender": "you", "msg": user_msg, "reply": reply_to, "time": get_time(), "ticks": 1})
                # Then AI replies instantly = 2 ticks = seen
                if "hey professor" in user_msg.lower():
                    reply = "Hello! I'm Pro AI. How can I help you today?"
                else:
                    reply = f"Got it: {user_msg}"
                chat_history[-1]["ticks"] = 2 # upgrade to double tick
                chat_history.append({"sender": "ai", "msg": reply, "reply": None, "time": get_time(), "ticks": 0})
                data["chat_history"] = chat_history
                save_data(data)

    messages_html = ""
    for i, item in enumerate(chat_history):
        sender = item["sender"]
        msg = item["msg"]
        reply = item.get("reply")
        time = item.get("time", "")
        ticks = item.get("ticks", 0)
        cls = "you" if sender == "you" else "ai"
        
        reply_html = f'<div class="quoted">{reply[:80]}...</div>' if reply else ""
        if ticks == 1:
            ticks_html = '<span class="ticks gray">✔️</span>' # sent
        elif ticks == 2:
            ticks_html = '<span class="ticks blue">✔️✔️</span>' # delivered + seen
        else:
            ticks_html = ""
        
        messages_html += f'<div class="bubble {cls}" data-msg="{msg}">{reply_html}{msg}<div class="meta">{time} {ticks_html}</div></div>'

    pin_option = "Unpin Chat" if pinned else "Pin Chat"
    pin_banner = '<div class="pin-banner">📌 This chat is Pinned & Saved</div>' if pinned else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #111b21; color: white; font-family: Arial; margin: 0; padding: 0; touch-action: pan-y; }}
    .header {{ background: #202c33; padding: 15px; text-align: center; font-weight: bold; font-size: 18px; position: fixed; width: 100%; top: 0; display: flex; justify-content: space-between; align-items: center; z-index: 10; }}
    .menu-btn {{ background: none; border: none; color: white; font-size: 24px; cursor: pointer; }}
    .dropdown {{ display: none; position: absolute; right: 10px; top: 50px; background: #2a3942; border-radius: 8px; box-shadow: 0 2px 10px #000; min-width: 160px; }}
    .dropdown button {{ background: none; border: none; color: white; padding: 12px 16px; width: 100%; text-align: left; cursor: pointer; font-size: 15px; }}
    .dropdown button:hover {{ background: #7B2FFF; }}
    .pin-banner {{ background: #7B2FFF; text-align: center; padding: 6px; font-size: 13px; position: fixed; top: 55px; width: 100%; z-index: 9; }}
    .chat {{ padding: 90px 10px 140px 10px; height: 100vh; overflow-y: scroll; box-sizing: border-box; }}
    .bubble {{ padding: 8px 12px 4px 12px; border-radius: 8px; margin: 6px 0; max-width: 70%; clear: both; font-size: 15px; position: relative; }}
    .you {{ background: #7B2FFF; float: right; border-bottom-right-radius: 2px; }}
    .ai {{ background: #202c33; float: left; border-bottom-left-radius: 2px; }}
    .quoted {{ background: rgba(0,0,0,0.2); border-left: 3px solid #7B2FFF; padding: 6px; margin-bottom: 6px; border-radius: 4px; font-size: 13px; opacity: 0.8; }}
    .meta {{ font-size: 11px; color: #8696a0; text-align: right; margin-top: 4px; }}
    .ticks.gray {{ color: #8696a0; }} /* Single gray tick */
    .ticks.blue {{ color: #53bdeb; }} /* Double blue ticks */
    .input {{ position: fixed; bottom: 0; width: 100%; background: #202c33; padding: 8px; box-sizing: border-box; }}
    .reply-box {{ display: none; background: #2a3942; border-left: 4px solid #7B2FFF; padding: 8px; margin-bottom: 8px; border-radius: 8px; }}
    .reply-box span {{ font-size: 13px; opacity: 0.8; }}
    .close-reply {{ float: right; cursor: pointer; font-weight: bold; }}
    .input-row {{ display: flex; align-items: center; }}
        input {{ flex: 1; padding: 12px 15px; border-radius: 25px; border: none; background: #2a3942; color: white; outline: none; }}
    .icon {{ font-size: 24px; margin: 0 6px; cursor: pointer; }}
    .send-btn {{ background: #7B2FFF; color: white; border: none; border-radius: 50%; width: 42px; height: 42px; margin-left: 6px; font-size: 18px; }}
    .error-toast {{ display: none; position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%); background: #e74c3c; padding: 10px 16px; border-radius: 20px; font-size: 13px; }}
    </style>
    </head>
    <body>
        <div class="header">
            <span>Pro AI 🤖</span>
            <button class="menu-btn" onclick="toggleMenu()">⋮</button>
            <div class="dropdown" id="menu">
                <form method="POST">
                    <button name="action" value="pin">{pin_option}</button>
                    <button name="action" value="delete" onclick="return confirm('Delete all messages?')">Delete Chat</button>
                </form>
            </div>
        </div>
        {pin_banner}
        <div class="chat" id="chat">{messages_html}</div>
        <div class="error-toast" id="errorToast">⚠️ Check your internet connection or connect to WiFi for better service</div>
        
        <form method="POST" class="input" id="msgForm">
            <div class="reply-box" id="replyBox">
                <span id="replyText"></span>
                <span class="close-reply" onclick="clearReply()">×</span>
            </div>
            <input type="hidden" name="reply_to" id="reply_to">
            <div class="input-row">
                <span class="icon">😊</span>
                <input name="msg" id="msgInput" placeholder="Message" autocomplete="off">
                <label class="icon">📷
                    <input type="file" name="photo" accept="image/*" capture="camera" style="display:none">
                </label>
                <button type="submit" class="send-btn" id="sendBtn">➤</button>
            </div>
        </form>

    <script>
    let sendTimeout;
    document.getElementById('msgForm').addEventListener('submit', function() {{
        // Start 30s timer
        sendTimeout = setTimeout(() => {{
            document.getElementById('errorToast').style.display = 'block';
            setTimeout(() => {{ document.getElementById('errorToast').style.display = 'none'; }}, 4000);
        }}, 30000);
    }});
    
    // Clear timer if page reloads = message went through
    window.onload = () => clearTimeout(sendTimeout);

    function toggleMenu() {{
        var menu = document.getElementById("menu");
        menu.style.display = menu.style.display === "block"? "none" : "block";
    }}
    window.onclick = function(e) {{
        if(!e.target.matches('.menu-btn')) {{
            document.getElementById("menu").style.display = "none";
        }}
    }}
    
    function clearReply() {{
        document.getElementById("replyBox").style.display = "none";
        document.getElementById("reply_to").value = "";
    }}
    
    let startX = 0;
    document.querySelectorAll('.bubble').forEach(bubble => {{
        bubble.addEventListener('touchstart', e => {{ startX = e.touches[0].clientX }});
        bubble.addEventListener('touchend', e => {{
            let endX = e.changedTouches[0].clientX;
            if(endX - startX > 80) {{
                let msg = bubble.getAttribute('data-msg');
                document.getElementById('reply_to').value = msg;
                document.getElementById('replyText').innerText = msg;
                document.getElementById('replyBox').style.display = "block";
                document.getElementById('msgInput').focus();
            }}
        }});
    }});
    </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run()
