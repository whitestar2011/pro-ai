from flask import Flask, request
import json, os

app = Flask(__name__)
DATA_FILE = "chat_data.json"

# Load chat + pin on startup
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
    
    if request.method == "POST":
        if "pin" in request.form:
            data["pinned"] = not pinned  # toggle pin
            save_data(data)
        else:
            user_msg = request.form.get("msg")
            if user_msg:
                chat_history.append(("you", user_msg))
                if "hey professor" in user_msg.lower():
                    reply = "Hello! I'm Pro AI. How can I help you today?"
                else:
                    reply = f"Got it: {user_msg}"
                chat_history.append(("ai", reply))
                data["chat_history"] = chat_history
                save_data(data)

    messages_html = ""
    for sender, msg in chat_history:
        if sender == "you":
            messages_html += f'<div class="bubble you">{msg}</div>'
        else:
            messages_html += f'<div class="bubble ai">{msg}</div>'

    pin_text = "📌 Unpin" if pinned else "📌 Pin Chat"
    pin_banner = '<div class="pin-banner">📌 This chat is Pinned & Saved</div>' if pinned else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #111b21; color: white; font-family: Arial; margin: 0; padding: 0; }}
        .header {{ background: #202c33; padding: 15px; text-align: center; font-weight: bold; font-size: 18px; position: fixed; width: 100%; top: 0; display: flex; justify-content: space-between; }}
        .pin-btn {{ background: #7B2FFF; border: none; color: white; padding: 6px 10px; border-radius: 8px; font-size: 13px; }}
        .pin-banner {{ background: #7B2FFF; text-align: center; padding: 6px; font-size: 13px; position: fixed; top: 55px; width: 100%; }}
        .chat {{ padding: 90px 10px 80px 10px; height: 100vh; overflow-y: scroll; box-sizing: border-box; }}
        .bubble {{ padding: 8px 12px; border-radius: 8px; margin: 6px 0; max-width: 70%; clear: both; font-size: 15px; }}
        .you {{ background: #7B2FFF; float: right; border-bottom-right-radius: 2px; }} /* Purple */
        .ai {{ background: #202c33; float: left; border-bottom-left-radius: 2px; }}   /* Dark */
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
        <div class="chat">{messages_html}</div>
        <form method="POST" class="input" enctype="multipart/form-data">
            <span class="icon">😊</span>
            <input name="msg" placeholder="Message" autocomplete="off">
            <label class="icon">📷
                <input type="file" name="photo" accept="image/*" capture="camera" style="display:none">
            </label>
            <button type="submit">➤</button>
        </form>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run()
