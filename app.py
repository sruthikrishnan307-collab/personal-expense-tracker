from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import csv
import io

from datetime import datetime
from flask import make_response
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# =========================
# CONFIGURATION
# =========================

=False,
        default=3000
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
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
# MONTHLY BUDGET MODEL
# =========================

class Budget(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    monthly_amount = db.Column(
        db.Float,
        nullable  existing_user = User.query.filter_by(
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
# =========================
# LOGOUT
# =========================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("You have been logged out successfully!", "success")

    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():

    from datetime import datetime, timedelta

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

    # Total spending for filtered results
    total_expenses = sum(
        expense.amount for expense in expenses
    )

    expense_count = len(expenses)

    # Category totals
    category_totals = {}

    for expense in expenses:
        category_totals[expense.category] = (
            category_totals.get(expense.category, 0)
            + expense.amount
        )

    # Monthly totals for chart
    monthly_totals = {}

    for expense in expenses:
        month = expense.date[:7]

        monthly_totals[month] = (
            monthly_totals.get(month, 0)
            + expense.amount
        )

    # =========================
    # MONTHLY BUDGET TRACKING
    # =========================

    current_month = datetime.now().strftime("%Y-%m")

    budget = Budget.query.filter_by(
        user_id=current_user.id
    ).first()

    if budget is None:
        budget = Budget(
            monthly_amount=3000,
            user_id=current_user.id
        )
        db.session.add(budget)
        db.session.commit()

    # Current month expenses
    current_month_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date.like(f"{current_month}%")
    ).all()

    current_month_spending = sum(
        expense.amount for expense in current_month_expenses
    )

    # Budget calculations FIRST
    monthly_budget = budget.monthly_amount

    budget_remaining = monthly_budget - current_month_spending

    budget_percentage = (
        (current_month_spending / monthly_budget) * 100
        if monthly_budget > 0 else 0
    )

    budget_progress = min(budget_percentage, 100)

    # =========================
    # MONTHLY EXPENSE INSIGHTS
    # =========================

    # Current month category spending
    current_category_totals = {}

    for expense in current_month_expenses:
        current_category_totals[expense.category] = (
            current_category_totals.get(expense.category, 0)
            + expense.amount
        )

    # Highest spending category
    if current_category_totals:
        top_category = max(
            current_category_totals,
            key=current_category_totals.get
        )
        top_category_amount = current_category_totals[top_category]
    else:
        top_category = "No expenses yet"
        top_category_amount = 0

    # Previous month calculation
    previous_month_date = (
        datetime.now().replace(day=1) - timedelta(days=1)
    )

    previous_month = previous_month_date.strftime("%Y-%m")

    previous_month_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date.like(f"{previous_month}%")
    ).all()

    previous_month_spending = sum(
        expense.amount for expense in previous_month_expenses
    )

    # Spending comparison
    if previous_month_spending > 0:
        spending_change = (
            (current_month_spending - previous_month_spending)
            / previous_month_spending
        ) * 100
    else:
        spending_change = 0

    if current_month_spending > previous_month_spending:
        spending_trend = "increased"
    elif current_month_spending < previous_month_spending:
        spending_trend = "decreased"
    else:
        spending_trend = "unchanged"

    # Smart saving suggestion
    if current_month_spending == 0:
        saving_tip = (
            "Start recording your expenses to receive personalized saving tips."
        )
    elif budget_percentage >= 100:
        saving_tip = (
            "You have exceeded your budget. "
            "Try reducing non-essential expenses."
        )
    elif budget_percentage >= 80:
        saving_tip = (
            "You are close to your budget limit. "
            "Be careful with additional spending."
        )
    elif top_category != "No expenses yet":
        saving_tip = (
            f"Your highest spending is on {top_category}. "
            "Review this category to find possible savings."
        )
    else:
        saving_tip = "Keep tracking your expenses to improve your savings."

    # =========================
    # RENDER DASHBOARD
    # =========================

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total_expenses=total_expenses,
        expense_count=expense_count,
        category_totals=category_totals,
        monthly_totals=monthly_totals,
        selected_category=category,
        selected_date=date,

        # Budget information
        monthly_budget=monthly_budget,
        current_month_spending=current_month_spending,
        budget_remaining=budget_remaining,
        budget_percentage=budget_percentage,
        budget_progress=budget_progress,

        # Monthly insights
        top_category=top_category,
        top_category_amount=top_category_amount,
        previous_month_spending=previous_month_spending,
        spending_change=spending_change,
        spending_trend=spending_trend,
        saving_tip=saving_tip
    )

# =========================
# ADD NEW EXPENSE
# =========================

@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():

    if request.method == "POST":

        title = request.form.get("title")
        amount = request.form.get("amount")
        category = request.form.get("category")
        date = request.form.get("date")

        if not title or not amount or not category or not date:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("add_expense"))

        try:
            amount = float(amount)

            if amount <= 0:
                flash("Amount must be greater than zero.", "error")
                return redirect(url_for("add_expense"))

        except ValueError:
            flash("Please enter a valid amount.", "error")
            return redirect(url_for("add_expense"))

        new_expense = Expense(
            title=title,
            amount=amount,
            category=category,
            date=date,
            user_id=current_user.id
        )

        db.session.add(new_expense)
        db.session.commit()

        flash("Expense added successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_expense.html")

@app.route("/export-csv")
@login_required
def export_csv():

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Expense.query.filter_by(
        user_id=current_user.id
    )

    if start_date:
        query = query.filter(Expense.date >= start_date)

    if end_date:
        query = query.filter(Expense.date <= end_date)

    expenses = query.order_by(
        Expense.date.desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "Title", "Amount", "Category", "Date"])

    for expense in expenses:
        writer.writerow([
            expense.id,
            expense.title,
            expense.amount,
            expense.category,
            str(expense.date) if expense.date else "N/A"
        ])
    response = make_response(output.getvalue())

    response.headers["Content-Disposition"] = (
        "attachment; filename=expense_report.csv"
    )
    response.headers["Content-Type"] = "text/csv"

    return response
@app.route("/export-pdf")
@login_required
def export_pdf():

    from io import BytesIO

    buffer = BytesIO()

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Expense.query.filter_by(
        user_id=current_user.id
    )

    if start_date:
        query = query.filter(Expense.date >= start_date)

    if end_date:
        query = query.filter(Expense.date <= end_date)

    expenses = query.order_by(
        Expense.date.desc()
    ).all()

    total = sum(expense.amount for expense in expenses)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("ExpenseFlow - Expense Report", styles["Title"])
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            f"Total Expenses: Rs. {total:.2f}",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 20))

    data = [
        ["ID", "Title", "Category", "Date", "Amount"]
    ]

    for expense in expenses:
        data.append([
            str(expense.id),
            str(expense.title),
            str(expense.category),
            str(expense.date),
            f"Rs. {expense.amount:.2f}"
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6845c2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    response = make_response(buffer.getvalue())

    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        "attachment; filename=expense_report.pdf"
    )

    return response
@app.route("/expense-report")
@login_required
def expense_report():

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    expenses = Expense.query.filter(
        Expense.user_id == current_user.id
    )

    if start_date:
        expenses = expenses.filter(
            Expense.date >= start_date
        )

    if end_date:
        expenses = expenses.filter(
            Expense.date <= end_date
        )

    expenses = expenses.order_by(
        Expense.date.desc()
    ).all()

    report_total = sum(
        expense.amount for expense in expenses
    )

    return render_template(
        "expense_report.html",
        expenses=expenses,
        report_total=report_total,
        start_date=start_date,
        end_date=end_date
    )
# =========================
# EDIT EXPENSE
# =========================

@app.route("/edit-expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):

    expense = Expense.query.filter_by(
        id=expense_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        title = request.form.get("title")
        amount = request.form.get("amount")
        category = request.form.get("category")
        date = request.form.get("date")

        if not title or not amount or not category or not date:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("edit_expense", expense_id=expense.id))

        try:
            amount = float(amount)

            if amount <= 0:
                flash("Amount must be greater than zero.", "error")
                return redirect(url_for("edit_expense", expense_id=expense.id))

        except ValueError:
            flash("Please enter a valid amount.", "error")
            return redirect(url_for("edit_expense", expense_id=expense.id))

        expense.title = title
        expense.amount = amount
        expense.category = category
        expense.date = date

        db.session.commit()

        flash("Expense updated successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_expense.html", expense=expense)

@app.route("/delete-expense/<int:expense_id>")
@login_required
def delete_expense(expense_id):

    expense = Expense.query.filter_by(
        id=expense_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(expense)
    db.session.commit()

    flash("Expense deleted successfully!", "success")

    return redirect(url_for("dashboard"))
# =========================
# UPDATE MONTHLY BUDGET
# =========================

@app.route("/update-budget", methods=["POST"])
@login_required
def update_budget():

    try:
        new_budget = float(request.form["monthly_budget"])

        if new_budget <= 0:
            flash("Budget must be greater than zero!", "error")
            return redirect(url_for("dashboard"))

        budget = Budget.query.filter_by(
            user_id=current_user.id
        ).first()

        if budget is None:
            budget = Budget(
                monthly_amount=new_budget,
                user_id=current_user.id
            )
            db.session.add(budget)

        else:
            budget.monthly_amount = new_budget

        db.session.commit()

        flash("Monthly budget updated successfully!", "success")

    except ValueError:
        flash("Please enter a valid budget amount!", "error")

    return redirect(url_for("dashboard"))
# Initialize database for both local and Render deployment
with app.app_context():
    db.create_all()

if __name__ == "__main__":

    print("Starting ExpenseFlow...")

    print("Database initialized successfully!")

    app.run(host="127.0.0.1", port=5000, debug=True)