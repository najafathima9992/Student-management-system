from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"  # change this in production

# ------------------ DATABASE ------------------

def get_db():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()

    # Students table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        course TEXT NOT NULL
    )
    """)

    # Users table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.close()

create_tables()

# ------------------ AUTH ------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                         (username, password))
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            return "Username already exists"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?",
                            (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            return redirect("/")

        return "Invalid credentials"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()

    data = conn.execute("""
        SELECT course, COUNT(*) as count 
        FROM students 
        GROUP BY course
    """).fetchall()

    conn.close()

    courses = [row["course"] for row in data]
    counts = [row["count"] for row in data]

    return render_template("dashboard.html", courses=courses, counts=counts)


# ------------------ PROTECTED ROUTE ------------------

def is_logged_in():
    return "user" in session


# ------------------ HOME + SEARCH ------------------

@app.route("/")
def index():
    if not is_logged_in():
        return redirect("/login")

    search = request.args.get("search")

    conn = get_db()

    if search:
        students = conn.execute(
            "SELECT * FROM students WHERE name LIKE ?",
            ('%' + search + '%',)
        ).fetchall()
    else:
        students = conn.execute("SELECT * FROM students").fetchall()

    conn.close()

    return render_template("index.html", students=students)


# ------------------ ADD ------------------

@app.route("/add", methods=["GET", "POST"])
def add():
    if not is_logged_in():
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        course = request.form["course"]

        if not name or not age or not course:
            return "All fields are required!"

        conn = get_db()
        conn.execute("INSERT INTO students (name, age, course) VALUES (?, ?, ?)",
                     (name, age, course))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add.html")


# ------------------ DELETE ------------------

@app.route("/delete/<int:id>")
def delete(id):
    if not is_logged_in():
        return redirect("/login")

    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")


# ------------------ UPDATE ------------------

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if not is_logged_in():
        return redirect("/login")

    conn = get_db()

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        course = request.form["course"]

        if not name or not age or not course:
            return "All fields required!"

        conn.execute(
            "UPDATE students SET name=?, age=?, course=? WHERE id=?",
            (name, age, course, id)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    student = conn.execute(
        "SELECT * FROM students WHERE id=?", (id,)
    ).fetchone()

    conn.close()

    return render_template("edit.html", student=student)


# ------------------ REST API ------------------

@app.route("/api/students", methods=["GET"])
def api_get_students():
    conn = get_db()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    return jsonify([dict(row) for row in students])


@app.route("/api/students", methods=["POST"])
def api_add_student():
    data = request.json

    conn = get_db()
    conn.execute("INSERT INTO students (name, age, course) VALUES (?, ?, ?)",
                 (data["name"], data["age"], data["course"]))
    conn.commit()
    conn.close()

    return {"message": "Student added"}


@app.route("/api/students/<int:id>", methods=["DELETE"])
def api_delete_student(id):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return {"message": "Student deleted"}


# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(debug=True)