from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a more secure secret key

# Database setup
def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            income REAL DEFAULT 0.0,
            expenses REAL DEFAULT 0.0
        )
    ''')
    # Create transactions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            type TEXT NOT NULL,  -- 'income' or 'expense'
            amount REAL NOT NULL,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Call the database initialization
init_db()

# Function to add a transaction
def add_transaction(username, transaction_type, amount, description):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute('INSERT INTO transactions (username, type, amount, description) VALUES (?, ?, ?, ?)', 
              (username, transaction_type, amount, description))
    # Update user's balance, income, and expenses
    if transaction_type == 'income':
        c.execute('UPDATE users SET balance = balance + ?, income = income + ? WHERE username = ?', 
                  (amount, amount, username))
    elif transaction_type == 'expense':
        c.execute('UPDATE users SET balance = balance - ?, expenses = expenses + ? WHERE username = ?', 
                  (amount, amount, username))
    conn.commit()
    conn.close()

# Home route
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose a different one.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        if user:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
        conn.close()
    return render_template('login.html')

# User dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    
    if request.method == 'POST':
        transaction_type = request.form['transaction_type']
        amount = float(request.form['amount'])
        description = request.form['description']
        add_transaction(username, transaction_type, amount, description)
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('dashboard'))

    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute('SELECT * FROM transactions WHERE username = ?', (username,))
    transactions = c.fetchall()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user_data = c.fetchone()
    conn.close()

    return render_template('dashboard.html', transactions=transactions, user_data=user_data)

# User logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)