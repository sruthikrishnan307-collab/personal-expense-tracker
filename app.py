from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# =========================
# CONFIGURATION
# =========================

import os

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expense_tracker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# =========================
# EXTENSIONS
# =========================

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# =========================
# USER MODEL
# =========================

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )


# =========================
# EXPENSE MODEL
# =========================

class Expense(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    date = db.Column(
        db.String(20),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )


# =========================
# LOAD USER
# =========================

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(User, int(user_id))


# =========================
# HOME
# =========================

@app.route("/")
def home():

    return render_template("index.html")


# =========================
# DATABASE CREATION
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            return "Username already exists!"

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        new_user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username
        ).first()

        if user and bcrypt.check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(url_for("dashboard"))

        return "Invalid username or password!"

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():

    category = request.args.get("category")
    date = request.args.get("date")

    query = Expense.query.filter_by(
        user_id=current_user.id
    )

    if category:
        query = query.filter_by(category=category)

    if date:
        query = query.filter_by(date=date)

    expenses = query.all()

    # Total spending for the filtered results
    total_expenses = sum(
        expense.amount for expense in expenses
    )

    expense_count = len(expenses)

    # Category totals
    category_totals = {}

    for expense in expenses:

        if expense.category not in category_totals:
            category_totals[expense.category] = 0

        category_totals[expense.category] += expense.amount
        monthly_totals = {}

    for expense in expenses:
        month = expense.date[:7]

        if month not in monthly_totals:
            monthly_totals[month] = 0

        monthly_totals[month] += expense.amount

    return render_template(
    "dashboard.html",
    expenses=expenses,
    total_expenses=total_expenses,
    expense_count=expense_count,
    category_totals=category_totals,
    monthly_totals=monthly_totals,
    selected_category=category,
    selected_date=date
)
@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():

    if request.method == "POST":

        title = request.form["title"]
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]

        new_expense = Expense(
            title=title,
            amount=float(amount),
            category=category,
            date=date,
            user_id=current_user.id
        )

        db.session.add(new_expense)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("add_expense.html")
@app.route("/edit-expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):

    expense = Expense.query.filter_by(
        id=expense_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        expense.title = request.form["title"]
        expense.amount = float(request.form["amount"])
        expense.category = request.form["category"]
        expense.date = request.form["date"]

        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template(
        "edit_expense.html",
        expense=expense
    )
@app.route("/delete-expense/<int:expense_id>")
@login_required
def delete_expense(expense_id):

    expense = Expense.query.filter_by(
        id=expense_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(expense)
    db.session.commit()

    return redirect(url_for("dashboard"))
if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)