from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
import sqlite3
import os
import cv2
from live_demo import predict

app = Flask(__name__)
app.secret_key = "supersecretkey"
DATABASE = "database.db"


# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------- LANDING PAGE ---------------- #

@app.route('/')
def landing():
    return render_template("landing.html")


# ---------------- HOME PAGE ---------------- #

@app.route('/home')
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("index.html", user=session["user"])


# ---------------- REGISTER ---------------- #

@app.route('/register', methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except:
            conn.close()
            return "Username already exists"

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route('/login', methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("home"))   # redirect to HOME

        else:
            return "Invalid credentials"

    return render_template("login.html")


# ---------------- LOGOUT ---------------- #

@app.route('/logout')
def logout():

    session.pop("user", None)

    return redirect(url_for("landing"))


# ---------------- CAMERA DETECTION ---------------- #

camera = cv2.VideoCapture(0)

current_prediction = ""


def generate_frames():

    global current_prediction

    while True:

        success, frame = camera.read()

        if not success:
            break

        else:
            result, confidence = predict(frame)

            current_prediction = result

            ret, buffer = cv2.imencode('.jpg', frame)

            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   frame +
                   b'\r\n')


# ---------------- VIDEO STREAM ---------------- #

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/prediction')
def prediction():
    return jsonify({'prediction': current_prediction})


# ---------------- OTHER PAGES ---------------- #

@app.route('/books')
def books():
    return render_template('books.html')


@app.route('/courses')
def courses():
    return render_template('courses.html')


@app.route('/social')
def social():
    return render_template('social.html')


@app.route('/pdf/<filename>')
def view_pdf(filename):
    return render_template('pdf_viewer.html', filename=filename)


@app.route('/upload_post', methods=['POST'])
def upload_post():

    file = request.files['media']

    if file:
        filepath = os.path.join('static/posts', file.filename)
        file.save(filepath)

    return redirect('/social')


@app.route('/search')
def search():

    query = request.args.get('query')

    if query:
        return f"Search results for: {query}"

    return "No search query provided"


# ---------------- RUN APP ---------------- #

if __name__ == '__main__':
    app.run(debug=True)