from flask import Flask, render_template, request
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
app = Flask(__name__)
import os

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
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
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_item.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def home():
    items = db.session.execute(db.select(MenuItem)).scalars().all()
    return render_template("menu.html", items=items)
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))
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
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            if user.role == "admin":
                 return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

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
    if current_user.role != "customer":
        return "Access denied", 403

    return render_template("dashboard.html")
@app.route("/order/<int:item_id>", methods=["POST"])
@login_required
def place_order(item_id):
    if current_user.role != "customer":
        return "Access denied", 403

    item = db.session.get(MenuItem, item_id)

    if not item:
        return "Food item not found", 404

    quantity = request.form.get("quantity", type=int)

    if quantity is None or not 1 <= quantity <= 10:
        return "Invalid quantity", 400

    new_order = Order(
        user_id=current_user.id,
        menu_item_id=item.id,
        quantity=quantity,
        total_price=round(item.price * quantity, 2)
    )

    db.session.add(new_order)
    db.session.commit()

    return "Order placed successfully!"
@app.route("/my-orders")
@login_required
def my_orders():
    if current_user.role != "customer":
        return "Access denied", 403

    orders = db.session.execute(
        db.select(Order, MenuItem)
        .join(MenuItem, Order.menu_item_id == MenuItem.id)
        .where(Order.user_id == current_user.id)
    ).all()

    return render_template("orders.html", orders=orders)
@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return "Access denied", 403

    return render_template("admin_dashboard.html")
@app.route("/admin/add-item", methods=["GET", "POST"])
@login_required
def add_item():
    if current_user.role != "admin":
        return "Access denied", 403

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", type=float)

        if not name or len(name) > 100:
            return "Invalid food name", 400

        if price is None or not 0.01 <= price <= 1000:
            return "Invalid price", 400

        if price != round(price, 2):
            return "Price must have a maximum of two decimal places", 400

        new_item = MenuItem(
            name=name,
            price=round(price, 2)
        )

        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for("admin_dashboard"))

    return render_template("add_item.html")
@app.route("/admin/manage-items")
@login_required
def manage_items():
    if current_user.role != "admin":
        return "Access denied", 403

    items = db.session.execute(
        db.select(MenuItem).order_by(MenuItem.id)
    ).scalars().all()

    return render_template("manage_items.html", items=items)
@app.route("/admin/edit-item/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    if current_user.role != "admin":
        return "Access denied", 403

    item = db.session.get(MenuItem, item_id)

    if not item:
        return "Food item not found", 404

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", type=float)

        if not name or len(name) > 100:
            return "Invalid food name", 400

        if price is None or not 0.01 <= price <= 1000:
            return "Invalid price", 400

        if price != round(price, 2):
            return "Price must have a maximum of two decimal places", 400

        item.name = name
        item.price = round(price, 2)

        db.session.commit()

        return redirect(url_for("manage_items"))

    return render_template("edit_item.html", item=item)
@app.route("/admin/delete-item/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    if current_user.role != "admin":
        return "Access denied", 403

    item = db.session.get(MenuItem, item_id)

    if not item:
        return "Food item not found", 404

    existing_order = db.session.execute(
        db.select(Order).filter_by(menu_item_id=item.id)
    ).scalars().first()

    if existing_order:
        return "Cannot delete food item with existing orders", 409

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for("manage_items"))
@app.route("/admin/orders")
@login_required
def admin_orders():
    if current_user.role != "admin":
        return "Access denied", 403

    orders = db.session.execute(
        db.select(Order, User, MenuItem)
        .join(User, Order.user_id == User.id)
        .join(MenuItem, Order.menu_item_id == MenuItem.id)
        .order_by(Order.id)
    ).all()

    return render_template("admin_orders.html", orders=orders)
if __name__ == "__main__":
    app.run(debug=True)