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
    return datetime.datetime.now().strftime("%I:%M %p")

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
        elif action.startswith("delete_selected"):
            indexes = json.loads(request.form.get("selected_indexes", "[]"))
            chat_history = [msg for i, msg in enumerate(chat_history) if i not in indexes]
            data["chat_history"] = chat_history
            save_data(data)
        else:
            user_msg = request.form.get("msg")
            reply_to = request.form.get("reply_to")
            if user_msg:
                chat_history.append({"sender": "you", "msg": user_msg, "reply": reply_to, "time": get_time(), "ticks": 1})
                if "hey professor" in user_msg.lower():
                    reply = "Hello! I'm Pro AI. How can I help you today?"
                else:
                    reply = f"Got it: {user_msg}"
                chat_history[-1]["ticks"] = 2
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
            ticks_html = '<svg class="tick"><path d="M1 5.5L3.5 8L8 3"/></svg>'
        elif ticks == 2:
            ticks_html = '<svg class="tick blue"><path d="M1 5.5L3.5 8L8 3"/><path d="M4 5.5L6.5 8L11 3" transform="translate(-3 0)"/></svg>'
        else:
            ticks_html = ""
        
        messages_html += f'<div class="bubble {cls}" data-index="{i}" data-msg="{msg}">{reply_html}{msg}<div class="meta">{time} {ticks_html}</div></div>'

    pin_option = "Unpin Chat" if pinned else "Pin Chat"
    pin_banner = '<div class="pin-banner">📌 This chat is Pinned & Saved</div>' if pinned else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #111b21; color: white; font-family: Arial; margin: 0; padding: 0; touch-action: pan-y; user-select: none; }}
.header {{ background: #202c33; padding: 10px 16px; height: 59px; display: flex; justify-content: space-between; align-items: center; position: fixed; width: 100%; top: 0; box-sizing: border-box; z-index: 10; }}
.header.select-mode {{ background: #7B2FFF; }}
.header-left {{ display: flex; align-items: center; gap: 16px; }}
.logo {{ width: 40px; height: 40px; border-radius: 50%; background: #7B2FFF; }}
.header-icons {{ display: flex; gap: 20px; }}
.icon-btn {{ background: none; border: none; padding: 0; cursor: pointer; }}
.icon-btn svg {{ width: 24px; height: 24px; fill: white; }}
.menu-btn {{ background: none; border: none; color: white; font-size: 24px; cursor: pointer; }}
.dropdown {{ display: none; position: absolute; right: 10px; top: 55px; background: #2a3942; border-radius: 3px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); min-width: 180px; }}
.dropdown button {{ background: none; border: none; color: white; padding: 12px 16px; width: 100%; text-align: left; cursor: pointer; font-size: 15px; }}
.dropdown button:hover {{ background: #7B2FFF; }}
.pin-banner {{ background: #7B2FFF; text-align: center; padding: 6px; font-size: 13px; position: fixed; top: 59px; width: 100%; z-index: 9; }}
.chat {{ padding: 90px 10px 80px 10px; height: 100vh; overflow-y: scroll; box-sizing: border-box; }}
.bubble {{ padding: 6px 7px 8px 9px; border-radius: 7.5px; margin: 6px 0; max-width: 65%; clear: both; font-size: 15px; position: relative; }}
.bubble.selected {{ background: #3b2a55!important; }}
.you {{ background: #7B2FFF; float: right; }}
.ai {{ background: #202c33; float: left; }}
.quoted {{ background: rgba(0,0,0,0.2); border-left: 3px solid #7B2FFF; padding: 6px; margin-bottom: 6px; border-radius: 4px; font-size: 13px; opacity: 0.8; }}
.meta {{ font-size: 11px; color: #8696a0; text-align: right; margin-top: 4px; display: flex; align-items: center; justify-content: flex-end; gap: 4px; }}
.tick {{ width: 16px; height: 11px; fill: none; stroke: #8696a0; stroke-width: 2; }}
.tick.blue {{ stroke: #53bdeb; }}
.input {{ position: fixed; bottom: 0; width: 100%; background: #202c33; padding: 8px 16px; box-sizing: border-box; }}
.reply-box {{ display: none; background: #2a3942; border-left: 4px solid #7B2FFF; padding: 8px; margin-bottom: 8px; border-radius: 8px; }}
.input-row {{ display: flex; align-items: center; gap: 8px; }}
        input {{ flex: 1; padding: 12px 15px; border-radius: 25px; border: none; background: #2a3942; color: white; outline: none; }}
.icon {{ width: 24px; height: 24px; fill: #8696a0; cursor: pointer; }}
.send-btn {{ background: #7B2FFF; border: none; border-radius: 50%; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; }}
.send-btn svg {{ width: 24px; height: 24px; fill: white; }}
.error-toast {{ display: none; position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%); background: #e74c3c; padding: 10px 16px; border-radius: 20px; font-size: 13px; }}
.emoji-picker {{ display: none; position: absolute; bottom: 70px; left: 10px; background: #2a3942; padding: 10px; border-radius: 12px; width: 300px; flex-wrap: wrap; gap: 8px; z-index: 20; }}
.emoji-picker span {{ font-size: 24px; cursor: pointer; padding: 4px; }}
.emoji-picker span:hover {{ background: #7B2FFF; border-radius: 6px; }}
    </style>
    </head>
    <body>
        <div class="header" id="header">
            <div class="header-left">
                <img src="/static/logo.png" class="logo" onerror="this.style.display='none'">
                <span id="headerTitle">Pro AI</span>
            </div>
            <button class="menu-btn" id="menuBtn" onclick="toggleMenu()">⋮</button>
            <div class="header-icons" id="selectIcons" style="display:none">
                <button class="icon-btn" onclick="exitSelect()"><svg viewBox="0 0 24 24"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg></button>
                <span id="selectedCount">1</span>
                <button class="icon-btn" onclick="replySelected()"><svg viewBox="0 0 24 24"><path d="M10 9V5l-7 7 7 7v-4.1c5 0 8.5 1.6 11 5.1-1-5-4-10-11-11z"/></svg></button>
                <button class="icon-btn" onclick="forwardSelected()"><svg viewBox="0 0 24 24"><path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/></svg></button>
                <button class="icon-btn" onclick="copySelected()"><svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2.9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2.9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg></button>
                <button class="icon-btn" onclick="deleteSelected()"><svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg></button>
            </div>
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
        
        <div class="emoji-picker" id="emojiPicker">
            <span>😀</span><span>😂</span><span>😍</span><span>🥰</span><span>😭</span><span>😡</span>
            <span>🙏</span><span>👍</span><span>❤️</span><span>🔥</span><span>💯</span><span>✨</span>
            <span>🎉</span><span>😎</span><span>🤔</span><span>😅</span><span>🙌</span><span>👏</span>
        </div>
        
        <form method="POST" class="input" id="msgForm" enctype="multipart/form-data">
            <div class="reply-box" id="replyBox">
                <span id="replyText"></span>
                <span style="float:right;cursor:pointer" onclick="clearReply()">✕</span>
            </div>
            <input type="hidden" name="reply_to" id="reply_to">
            <input type="hidden" name="action" id="action_input">
            <input type="hidden" name="selected_indexes" id="selected_indexes">
            <div class="input-row">
                <svg class="icon" id="emojiBtn" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10c5.51 0 10-4.48 10-10S17.51 2 12 2zm6.605 4.61a8.502 8.502 0 011.93 5.295c-.028.853-.053 1.886-.19 2.257l-.004.004c-.142.428-1.683.952-2.232 1.01-1.528.466-3.818.544-4.667.544-.845 0-3.096-.083-4.623-.54-1.075-.27-2.036-.924-2.23-1.01-.676-.386-.617-1.498-.608-2.276.017-.92.218-1.8.57-2.61.717-1.65 1.9-3.1 3.4-4.1C9.89 4.16 10.93 4 12 4c1.07 0 2.11.16 3.08.47.51.22.995.49 1.45.8.02.01.03.02.05.03l.002.002z"/></svg>
                <input name="msg" id="msgInput" placeholder="Message" autocomplete="off">
                <label><svg class="icon" viewBox="0 0 24 24"><path d="M9 16h6v-6h4l-8-8-8 8h4zm3-14C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.51 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>
                    <input type="file" name="photo" accept="image/*" capture="camera" style="display:none">
                </label>
                <button type="submit" class="send-btn"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></button>
            </div>
        </form>

    <script>
    let selected = [];
    let longPressTimer;

    document.getElementById('emojiBtn').onclick = () => {{
        let picker = document.getElementById('emojiPicker');
        picker.style.display = picker.style.display === 'flex'? 'none' : 'flex';
    }}
    document.querySelectorAll('.emoji-picker span').forEach(emoji => {{
        emoji.onclick = () => {{
            document.getElementById('msgInput').value += emoji.innerText;
            document.getElementById('msgInput').focus();
            document.getElementById('emojiPicker').style.display = 'none';
        }}
    }})

    function enterSelect(index) {{
        document.getElementById('header').classList.add('select-mode');
        document.getElementById('headerTitle').style.display = 'none';
        document.getElementById('menuBtn').style.display = 'none';
        document.getElementById('selectIcons').style.display = 'flex';
        toggleSelect(index);
    }}
    
    function exitSelect() {{
        selected = [];
        document.querySelectorAll('.bubble').forEach(b => b.classList.remove('selected'));
        document.getElementById('header').classList.remove('select-mode');
        document.getElementById('headerTitle').style.display = 'block';
        document.getElementById('menuBtn').style.display = 'block';
        document.getElementById('selectIcons').style.display = 'none';
    }}
    
    function toggleSelect(index) {{
        let bubble = document.querySelector(`[data-index="${{index}}"]`);
        if(selected.includes(index)) {{
            selected = selected.filter(i => i!= index);
            bubble.classList.remove('selected');
        }} else {{
            selected.push(index);
            bubble.classList.add('selected');
        }}
        document.getElementById('selectedCount').innerText = selected.length;
        if(selected.length === 0) exitSelect();
    }}
    
    function replySelected() {{
        let msg = document.querySelector(`[data-index="${{selected[0]}}"]`).getAttribute('data-msg');
        document.getElementById('reply_to').value = msg;
        document.getElementById('replyText').innerText = msg;
        document.getElementById('replyBox').style.display = "block";
        exitSelect();
        document.getElementById('msgInput').focus();
    }}
    
    function copySelected() {{
        let text = selected.map(i => document.querySelector(`[data-index="${{i}}"]`).getAttribute('data-msg')).join('\\n');
        navigator.clipboard.writeText(text);
        exitSelect();
    }}
    
    function deleteSelected() {{
        if(confirm('Delete ' + selected.length + ' messages?')) {{
            document.getElementById('action_input').value = 'delete_selected';
            document.getElementById('selected_indexes').value = JSON.stringify(selected);
            document.getElementById('msgForm').submit();
        }}
    }}
    
    function forwardSelected() {{
        alert('Forward: We can add share to WhatsApp next');
        exitSelect();
    }}

    document.querySelectorAll('.bubble').forEach(bubble => {{
        let index = bubble.getAttribute('data-index');
        let startX = 0;
        bubble.addEventListener('touchstart', e => {{ 
            startX = e.touches[0].clientX;
            longPressTimer = setTimeout(() => enterSelect(index), 500);
        }});
        bubble.addEventListener('touchend', e => {{
            clearTimeout(longPressTimer);
            let endX = e.changedTouches[0].clientX;
            if(endX - startX > 80 && selected.length === 0) {{
                let msg = bubble.getAttribute('data-msg');
                document.getElementById('reply_to').value = msg;
                document.getElementById('replyText').innerText = msg;
                document.getElementById('replyBox').style.display = "block";
                document.getElementById('msgInput').focus();
            }}
        }});
        bubble.addEventListener('touchmove', () => clearTimeout(longPressTimer));
        bubble.addEventListener('click', () => {{ if(selected.length > 0) toggleSelect(index) }});
    }});

    let sendTimeout;
    document.getElementById('msgForm').addEventListener('submit', function() {{
        sendTimeout = setTimeout(() => {{
            document.getElementById('errorToast').style.display = 'block';
            setTimeout(() => {{ document.getElementById('errorToast').style.display = 'none'; }}, 4000);
        }}, 30000);
    }});
    window.onload = () => clearTimeout(sendTimeout);

    function toggleMenu() {{
        var menu = document.getElementById("menu");
        menu.style.display = menu.style.display === "block"? "none" : "block";
    }}
    window.onclick = function(e) {{
        if(!e.target.matches('.menu-btn') &&!e.target.closest('.dropdown')) {{
            document.getElementById("menu").style.display = "none";
        }}
        if(!e.target.closest('#emojiBtn') &&!e.target.closest('#emojiPicker')) {{
            document.getElementById("emojiPicker").style.display = "none";
        }}
    }}
    function clearReply() {{
        document.getElementById("replyBox").style.display = "none";
        document.getElementById("reply_to").value = "";
    }}
    </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run()
