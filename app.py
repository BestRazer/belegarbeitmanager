from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

def create_tables():
    conn = sqlite3.connect('topics.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS topics
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       topic TEXT, fach TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS registrations
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       topic_id INTEGER,
                       student_name TEXT,
                       FOREIGN KEY (topic_id) REFERENCES topics (id))''')
    conn.commit()
    conn.close()

create_tables()

@app.route('/')
def index():
    conn = sqlite3.connect('topics.db')
    cursor = conn.cursor()
    cursor.execute("SELECT topics.id, topics.topic, topics.fach, COUNT(registrations.id) FROM topics LEFT JOIN registrations ON topics.id = registrations.topic_id GROUP BY topics.id")
    topics = cursor.fetchall()
    conn.close()
    return render_template('index.html', topics=topics)

@app.route('/submit', methods=['POST'])
def submit():
    topic_id = request.form['topic_id']
    student_name = request.form['name']
    conn = sqlite3.connect('topics.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM registrations WHERE topic_id = ?", (topic_id,))
    count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(id) FROM registrations WHERE student_name = ?", (student_name,))
    student_count = cursor.fetchone()[0]
    if count == 0:
        if student_count == 0:
            cursor.execute("INSERT INTO registrations (topic_id, student_name) VALUES (?, ?)", (topic_id, student_name))
            conn.commit()
    conn.close()
    return "Schüler " + student_name + " ist bereits eingetragen."

@app.route('/submit_topic', methods=['POST'])
def submit_topic():
    topic = request.form['topic']
    fach = request.form['fach']
    conn = sqlite3.connect('topics.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO topics (topic, fach) VALUES (?, ?)", (topic, fach))
    conn.commit()
    conn.close()
    return redirect('/teacher')

@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    if 'authenticated' in session and session['authenticated']:

        conn = sqlite3.connect('topics.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT topics.id, topics.fach, topics.topic, registrations.student_name
                        FROM topics
                        LEFT JOIN registrations ON topics.id = registrations.topic_id''')
        registrations = cursor.fetchall()
        conn.close()
        return render_template('teacher.html', registrations=registrations)

    if request.method == 'POST':
        auth_code = request.form['auth_code']
        if auth_code == 'authcode':

            session['authenticated'] = True
            conn = sqlite3.connect('topics.db')
            cursor = conn.cursor()
            cursor.execute('''SELECT topics.id, topics.fach, topics.topic, registrations.student_name
                            FROM topics
                            LEFT JOIN registrations ON topics.id = registrations.topic_id''')
            registrations = cursor.fetchall()
            conn.close()
            return render_template('teacher.html', registrations=registrations)
        else:
            return "Invalid authentication code"

    return render_template('auth.html')

@app.route('/delete', methods=['POST'])
def delete():
    if 'authenticated' in session and session['authenticated']:
        topic_id = request.form['topic_id']
        conn = sqlite3.connect('topics.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM topics WHERE id = ?', (topic_id,))
        cursor.execute('DELETE FROM registrations WHERE topic_id = ?', (topic_id,))
        cursor.execute('DELETE FROM sqlite_sequence WHERE name = ?', ('topics',))
        conn.commit()
        conn.close()
        return redirect('/teacher')
    else:
        return "Not authenticated"

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect('/teacher')

if __name__ == '__main__':
    app.run()