from flask import Flask, request
import json, os

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

data = load_data()

@app.route("/", methods=["GET", "POST"])
def home():
    global data
    chat_history = data["chat_history"]
    pinned = data["pinned"]
    reply_to = request.form.get("reply_to")
    
    if request.method == "POST":
        if "pin" in request.form:
            data["pinned"] = not pinned
            save_data(data)
        else:
            user_msg = request.form.get("msg")
            if user_msg:
                if reply_to:
                    user_msg = f"↩️ Replying to: {reply_to}\n{user_msg}"
                chat_history.append(("you", user_msg))
                if "hey professor" in user_msg.lower():
                    reply = "Hello! I'm Pro AI. How can I help you today?"
                else:
                    reply = f"Got it: {user_msg}"
                chat_history.append(("ai", reply))
                data["chat_history"] = chat_history
                save_data(data)

    messages_html = ""
    for i, (sender, msg) in enumerate(chat_history):
        cls = "you" if sender == "you" else "ai"
        messages_html += f'<div class="bubble {cls}" data-index="{i}" data-msg="{msg}">{msg}</div>'

    pin_text = "📌 Unpin" if pinned else "📌 Pin Chat"
    pin_banner = '<div class="pin-banner">📌 This chat is Pinned & Saved</div>' if pinned else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #111b21; color: white; font-family: Arial; margin: 0; padding: 0; touch-action: pan-y; }}
       .header {{ background: #202c33; padding: 15px; text-align: center; font-weight: bold; font-size: 18px; position: fixed; width: 100%; top: 0; display: flex; justify-content: space-between; z-index: 10; }}
       .pin-btn {{ background: #7B2FFF; border: none; color: white; padding: 6px 10px; border-radius: 8px; font-size: 13px; }}
       .pin-banner {{ background: #7B2FFF; text-align: center; padding: 6px; font-size: 13px; position: fixed; top: 55px; width: 100%; z-index: 10; }}
       .chat {{ padding: 90px 10px 80px 10px; height: 100vh; overflow-y: scroll; box-sizing: border-box; }}
       .bubble {{ padding: 8px 12px; border-radius: 8px; margin: 6px 0; max-width: 70%; clear: both; font-size: 15px; position: relative; transition: transform 0.2s; }}
       .you {{ background: #7B2FFF; float: right; border-bottom-right-radius: 2px; }}
       .ai {{ background: #202c33; float: left; border-bottom-left-radius: 2px; }}
       .reply-preview {{ background: #2a3942; border-left: 3px solid #7B2FFF; padding: 6px; margin-bottom: 6px; border-radius: 4px; font-size: 13px; opacity: 0.8; }}
       .input {{ position: fixed; bottom: 0; width: 100%; display: flex; align-items: center; background: #202c33; padding: 8px; box-sizing: border-box; }}
        input {{ flex: 1; padding: 12px 15px; border-radius: 25px; border: none; background: #2a3942; color: white; outline: none; }}
       .icon {{ font-size: 24px; margin: 0 6px; cursor: pointer; }}
        button {{ background: #7B2FFF; color: white; border: none; border-radius: 50%; width: 42px; height: 42px; margin-left: 6px; font-size: 18px; }}
    </style>
    </head>
    <body>
        <div class="header">
            <span>Pro AI 🤖</span>
            <form method="POST" style="margin:0">
                <button class="pin-btn" name="pin" value="1">{pin_text}</button>
            </form>
        </div>
        {pin_banner}
        <div class="chat" id="chat">{messages_html}</div>
        <form method="POST" class="input" id="msgForm">
            <input type="hidden" name="reply_to" id="reply_to">
            <div id="replyPreview"></div>
            <span class="icon">😊</span>
            <input name="msg" id="msgInput" placeholder="Message" autocomplete="off">
            <label class="icon">📷
                <input type="file" name="photo" accept="image/*" capture="camera" style="display:none">
            </label>
            <button type="submit">➤</button>
        </form>

    <script>
    let startX = 0;
    document.querySelectorAll('.bubble').forEach(bubble => {{
        bubble.addEventListener('touchstart', e => {{ startX = e.touches[0].clientX }});
        bubble.addEventListener('touchend', e => {{
            let endX = e.changedTouches[0].clientX;
            if(endX - startX > 80) {{ // swiped right
                let msg = bubble.getAttribute('data-msg');
                document.getElementById('reply_to').value = msg;
                document.getElementById('replyPreview').innerHTML = '<div class="reply-preview">↩️ ' + msg.substring(0,60) + '...</div>';
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
