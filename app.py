from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///restaurant.db"

# Initialize database
db = SQLAlchemy(app)

# Menu table
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

# Homepage
@app.route("/")
def home():
    return render_template("menu.html")

if __name__ == "__main__":
    app.run(debug=True)