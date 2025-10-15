from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)


# Main route (your original one)
@app.route("/", methods=["GET"])
def test():
    return "hello world"

# Health check route (for AWS target group)
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    # Run on port 80 for ECS (HTTP, ALB handles HTTPS)
    app.run(host="0.0.0.0", port=80)
