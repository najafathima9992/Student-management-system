from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# DB connection
def get_db():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create table
def create_table():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        course TEXT NOT NULL
    )
    """)
    conn.close()

create_table()

# 🔹 HOME + SEARCH
@app.route("/")
def index():
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


# 🔹 ADD
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        course = request.form["course"]

        # Validation
        if not name or not age or not course:
            return "All fields are required!"

        conn = get_db()
        conn.execute("INSERT INTO students (name, age, course) VALUES (?, ?, ?)",
                     (name, age, course))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add.html")


# 🔹 DELETE
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


# 🔹 UPDATE (EDIT)
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
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


if __name__ == "__main__":
    app.run(debug=True)