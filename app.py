from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ FIX: uploads folder automatic ga create avvali
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect('contacts.db')
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS contacts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        phone TEXT,
        email TEXT,
        image TEXT,
        favorite INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------- IMAGE SERVE ----------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------- AUTH ----------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('contacts.db')
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users(username,password) VALUES(?,?)",(username,password))
            conn.commit()
        except:
            return "Username already exists"
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('contacts.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect('/')
        return "Invalid login"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------- HOME ----------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    search = request.args.get('search')

    conn = sqlite3.connect('contacts.db')
    cur = conn.cursor()

    if search:
        cur.execute("SELECT * FROM contacts WHERE user_id=? AND name LIKE ?",
                    (session['user_id'], '%' + search + '%'))
    else:
        cur.execute("SELECT * FROM contacts WHERE user_id=?",
                    (session['user_id'],))

    contacts = cur.fetchall()
    conn.close()

    return render_template('index.html', contacts=contacts, search=search)

# ---------- ADD ----------
@app.route('/add', methods=['GET','POST'])
def add():
    if request.method=='POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']

        file = request.files['image']
        filename = ""

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        conn = sqlite3.connect('contacts.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO contacts(user_id,name,phone,email,image) VALUES(?,?,?,?,?)",
                    (session['user_id'], name, phone, email, filename))
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('add.html')

# ---------- DELETE ----------
@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('contacts.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM contacts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# ---------- FAVORITE ----------
@app.route('/favorite/<int:id>')
def favorite(id):
    conn = sqlite3.connect('contacts.db')
    cur = conn.cursor()
    cur.execute("UPDATE contacts SET favorite = NOT favorite WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# ---------- EDIT ----------
@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    conn = sqlite3.connect('contacts.db')
    cur = conn.cursor()

    if request.method=='POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']

        cur.execute("UPDATE contacts SET name=?, phone=?, email=? WHERE id=?",
                    (name, phone, email, id))
        conn.commit()
        conn.close()
        return redirect('/')

    cur.execute("SELECT * FROM contacts WHERE id=?", (id,))
    contact = cur.fetchone()
    conn.close()

    return render_template('edit.html', contact=contact)

if __name__ == "__main__":
    app.run(debug=True)