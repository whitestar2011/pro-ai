from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    reply = ""
    if request.method == "POST":
        user_msg = request.form.get("msg")
        if "hey professor" in user_msg.lower():
            reply = "Hello! I'm Pro AI. How can I help you today?"
        else:
            reply = f"You said: {user_msg}"

    return f"""
    <h1>Pro AI 🤖</h1>
    <form method="POST">
        <input name="msg" placeholder="Type here..." style="width:70%; padding:10px">
        <button type="submit" style="padding:10px">Send</button>
    </form>
    <p><b>Pro AI:</b> {reply}</p>
    """

if __name__ == "__main__":
    app.run()
