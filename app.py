from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Pro AI is Live 🚀</h1>
    <p>Say: hey professor</p>
    """

if __name__ == "__main__":
    app.run()
