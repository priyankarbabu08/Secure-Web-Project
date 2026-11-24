from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

app = Flask(__name__)
import os

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "development-only-change-me")
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///restaurant.db"

# Initialize database
db = SQLAlchemy(app)

# Menu table
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
# User table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def home():
    items = db.session.execute(db.select(MenuItem)).scalars().all()
    return render_template("menu.html", items=items)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or len(username) > 50:
            return "Invalid username", 400

        if len(password) < 8:
            return "Password must contain at least 8 characters", 400

        existing_user = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()

        if existing_user:
            return "Username already exists", 400

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role="customer"
        )

        db.session.add(new_user)
        db.session.commit()

        return "Registration successful!"

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return render_template("dashboard.html")

        return "Invalid username or password", 401

    return render_template("login.html")
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return "Logout successful!"
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")
if __name__ == "__main__":
    app.run(debug=True)