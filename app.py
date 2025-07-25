from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Create books table
    c.execute('''CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    available INTEGER DEFAULT 1)''')

    # Create members table
    c.execute('''CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT)''')

    # Create issued books table
    c.execute('''CREATE TABLE IF NOT EXISTS issued (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    member_id INTEGER,
                    issue_date TEXT,
                    return_date TEXT,
                    returned INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/books')
def view_books():
    conn = sqlite3.connect('database.db')
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('books.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title, author))
        conn.commit()
        conn.close()
        return redirect('/books')
    return render_template('add_book.html')

@app.route('/members')
def view_members():
    conn = sqlite3.connect('database.db')
    members = conn.execute('SELECT * FROM members').fetchall()
    conn.close()
    return render_template('members.html', members=members)

@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO members (name, email) VALUES (?, ?)', (name, email))
        conn.commit()
        conn.close()
        return redirect('/members')
    return render_template('add_member.html')

@app.route('/issue', methods=['GET', 'POST'])
def issue_book():
    conn = sqlite3.connect('database.db')
    books = conn.execute('SELECT * FROM books WHERE available=1').fetchall()
    members = conn.execute('SELECT * FROM members').fetchall()
    if request.method == 'POST':
        book_id = request.form['book_id']
        member_id = request.form['member_id']
        issue_date = datetime.now().strftime('%Y-%m-%d')
        return_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        conn.execute('INSERT INTO issued (book_id, member_id, issue_date, return_date) VALUES (?, ?, ?, ?)',
                     (book_id, member_id, issue_date, return_date))
        conn.execute('UPDATE books SET available=0 WHERE id=?', (book_id,))
        conn.commit()
        conn.close()
        return redirect('/books')
    conn.close()
    return render_template('issue_book.html', books=books, members=members)

@app.route('/return', methods=['GET', 'POST'])
def return_book():
    conn = sqlite3.connect('database.db')
    issued_books = conn.execute('''
        SELECT issued.id, books.title, members.name, issued.return_date 
        FROM issued
        JOIN books ON books.id = issued.book_id
        JOIN members ON members.id = issued.member_id
        WHERE issued.returned = 0
    ''').fetchall()

    if request.method == 'POST':
        issued_id = request.form['issued_id']
        issued_data = conn.execute('SELECT book_id, return_date FROM issued WHERE id=?', (issued_id,)).fetchone()
        book_id = issued_data[0]
        due_date = datetime.strptime(issued_data[1], '%Y-%m-%d')
        return_date = datetime.now()
        fine = max((return_date - due_date).days, 0) * 10  # ₹10 fine per day

        conn.execute('UPDATE issued SET returned=1 WHERE id=?', (issued_id,))
        conn.execute('UPDATE books SET available=1 WHERE id=?', (book_id,))
        conn.commit()
        conn.close()
        return f"<h3>Book Returned. Fine: ₹{fine}</h3><a href='/'>Home</a>"

    conn.close()
    return render_template('return_book.html', issued_books=issued_books)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

    