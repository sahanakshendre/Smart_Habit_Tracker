from flask import Flask, render_template, request, redirect, url_for, session
from storage import initialize_storage, load_habits, save_habits
from datetime import datetime, timedelta
import random
import os
import json
import calendar

app = Flask(__name__)
app.secret_key = "supersecretkey"

initialize_storage()

USER_FILE = "data/users.json"

if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

quotes = [
    "Small steps every day lead to big results.",
    "Consistency beats motivation.",
    "Discipline creates freedom.",
    "Success is built daily."
]

# ---------------- USER FUNCTIONS ----------------

def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# ---------------- AUTH ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = load_users()
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return render_template("register.html", error="User already exists")

        users[username] = {
            "password": password,
            "created": str(datetime.now().date())
        }

        save_users(users)
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ---------------- DASHBOARD (EXACTLY SAME AS YOUR ORIGINAL) ----------------

@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    habits = load_habits()

    # -------- FILTERS --------
    category_filter = request.args.get("category")
    search = request.args.get("search", "").lower()
    priority_filter = request.args.get("priority")
    selected_date = request.args.get("date")

    # Category filter
    if category_filter and category_filter != "All":
        habits = [h for h in habits if h.get("category") == category_filter]

    # Search filter
    if search:
        habits = [h for h in habits if search in h.get("name", "").lower()]

    # Priority filter
    if priority_filter:
        habits = [h for h in habits if h.get("priority") == priority_filter]

    # -------- CATEGORY LIST --------
    all_habits = load_habits()
    categories = list(set(h.get("category") for h in all_habits))

    # -------- CALENDAR --------
    today = datetime.now()
    year = today.year
    month = today.month
    cal = calendar.monthcalendar(year, month)

    if not selected_date:
        selected_date = str(today.date())

    # -------- PROGRESS --------
    total = len(habits)
    completed = sum(
        1 for h in habits
        if selected_date in h.get("history", [])
    )

    progress = (completed / total * 100) if total > 0 else 0

    return render_template(
        "index.html",
        habits=habits,
        categories=categories,
        selected_category=category_filter,
        calendar=cal,
        current_month=today.strftime("%B"),
        current_month_number=month,   # ✅ FIXED
        current_year=year,
        selected_date=selected_date,
        progress=progress
    )

# ---------------- NEW SEPARATE CALENDAR PAGE ----------------

@app.route("/calendar")
def calendar_page():
    if "user" not in session:
        return redirect(url_for("login"))

    habits = load_habits()
    selected_date = request.args.get("date")

    if not selected_date:
        selected_date = str(datetime.now().date())

    # ONLY completed habits for that date
    completed_habits = [
        h for h in habits
        if selected_date in h.get("history", [])
    ]

    today = datetime.now()
    year = today.year
    month = today.month
    cal = calendar.monthcalendar(year, month)

    return render_template(
        "calendar.html",
        completed_habits=completed_habits,
        calendar=cal,
        current_month=today.strftime("%B"),
        current_month_number=month,
        selected_date=selected_date
    )

@app.route("/complete_date/<int:habit_index>/<date>")
def complete_date(habit_index, date):
    habits = load_habits()

    if date not in habits[habit_index]["history"]:
        habits[habit_index]["history"].append(date)
        habits[habit_index]["streak"] += 1

    save_habits(habits)
    return redirect(url_for("dashboard", date=date))



# ---------------- HABIT ACTIONS (UNCHANGED) ----------------

@app.route("/add", methods=["POST"])
def add():
    habits = load_habits()

    habits.append({
        "name": request.form["name"],
        "category": request.form["category"],
        "priority": request.form["priority"],
        "history": [],
        "streak": 0
    })

    save_habits(habits)
    return redirect(url_for("dashboard"))

@app.route("/complete/<int:index>")
def complete(index):
    habits = load_habits()
    today = str(datetime.now().date())

    if today not in habits[index]["history"]:
        habits[index]["history"].append(today)
        habits[index]["streak"] += 1

    save_habits(habits)
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:index>")
def delete(index):
    habits = load_habits()
    habits.pop(index)
    save_habits(habits)
    return redirect(url_for("dashboard"))

@app.route("/reset")
def reset():
    habits = load_habits()
    for h in habits:
        h["history"] = []
        h["streak"] = 0
    save_habits(habits)
    return redirect(url_for("dashboard"))

# ---------------- ANALYTICS (UNCHANGED) ----------------

@app.route("/analytics")
def analytics():
    habits = load_habits()
    categories = {}

    for habit in habits:
        categories.setdefault(habit["category"], 0)
        categories[habit["category"]] += len(habit["history"])

    return render_template("analytics.html", categories=categories)

# ---------------- PROFILE (UNCHANGED) ----------------

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    users = load_users()
    created = users[session["user"]]["created"]
    days = (datetime.now() - datetime.strptime(created, "%Y-%m-%d")).days

    return render_template("profile.html", created=created, days=days)

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
