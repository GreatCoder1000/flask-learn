from flask import Flask, request, redirect, url_for, render_template, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database initialization
def init_db():
    conn = sqlite3.connect('topics.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS topics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS entries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, topic_id INTEGER, content TEXT,
                  FOREIGN KEY (topic_id) REFERENCES topics (id))''')
    conn.commit()
    conn.close()

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('topics.db')
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(*user)
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('topics.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already taken")
            return redirect(url_for('register'))
        conn.close()
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('topics.db')
        c = conn.cursor()
        c.execute("SELECT id, username, password FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            login_user(User(*user))
            return redirect(url_for('index'))
        flash("Invalid username or password")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully")
    return redirect(url_for('login'))

@app.route('/deregister', methods=['POST'])
@login_required
def deregister():
    user_id = current_user.id
    conn = sqlite3.connect('topics.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    logout_user()
    flash("Account deregistered successfully")
    return redirect(url_for('index'))

@app.route('/')
@login_required
def index():
    conn = sqlite3.connect('topics.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM topics")
    topics = c.fetchall()
    conn.close()
    return render_template('index.html', topics=topics)

@app.route('/create_topic', methods=['POST'])
@login_required
def create_topic():
    name = request.form['name']
    conn = sqlite3.connect('topics.db')
    c = conn.cursor()
    c.execute("INSERT INTO topics (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/topics/<int:topic_id>')
@login_required
def view_topic(topic_id):
    conn = sqlite3.connect('topics.db')
    c = conn.cursor()
    c.execute("SELECT id, content FROM entries WHERE topic_id = ?", (topic_id,))
    entries = c.fetchall()
    conn.close()
    return render_template('topic.html', entries=entries, topic_id=topic_id)

@app.route('/topics/<int:topic_id>/add_entry', methods=['POST'])
@login_required
def add_entry(topic_id):
    content = request.form['content']
    conn = sqlite3.connect('topics.db')
    c = conn.cursor()
    c.execute("INSERT INTO entries (topic_id, content) VALUES (?, ?)", (topic_id, content))
    conn.commit()
    conn.close()
    return redirect(url_for('view_topic', topic_id=topic_id))

@app.route('/topics/<int:topic_id>/<int:entry_id>')
@login_required
def view_entry(topic_id, entry_id):
    conn = sqlite3.connect('topics.db')
    c = conn.cursor()
    c.execute("SELECT content FROM entries WHERE id = ?", (entry_id,))
    entry = c.fetchone()
    conn.close()
    if entry:
        return render_template('entry.html', entry_content=entry[0])
    else:
        return "Entry not found", 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
