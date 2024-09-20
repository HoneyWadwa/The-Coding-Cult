from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Your MySQL username
app.config['MYSQL_PASSWORD'] = 'your_mysql_password'  # Your MySQL password
app.config['MYSQL_DB'] = 'college_event_db'  # Your database name

app.secret_key = 'your_secret_key'  # Replace with a strong secret key

try:
    mysql = MySQL(app)
    print("MySQL initialized:", mysql is not None)
except Exception as e:
    print("MySQL connection error:", e)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()  # Close the cursor after use
    if user:
        return User(user['id'], user['username'], user['role'])
    return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()  # Close the cursor after use
        if user and check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['role']))
            return redirect(url_for('dashboard'))
        return 'Invalid credentials', 401  # Return a 401 Unauthorized status
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # Make sure this field is included in your signup form

        # Add logic to store the new user in the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)',
                       (username, email, generate_password_hash(password), role))
        mysql.connection.commit()
        cursor.close()  # Close the cursor after use

        return redirect(url_for('login'))  # Redirect to login page after signup
    
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if current_user.role == 'eventhead':
        cursor.execute('SELECT * FROM events WHERE added_by = %s', (current_user.id,))
    else:
        cursor.execute('SELECT * FROM events')
    events = cursor.fetchall()
    cursor.close()  # Close the cursor after use
    return render_template('dashboard.html', events=events)

@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    if current_user.role != 'eventhead':
        return 'Only event heads can add events', 403  # Return a 403 Forbidden status
    if request.method == 'POST':
        event_name = request.form['event_name']
        event_date = request.form['event_date']
        event_venue = request.form['event_venue']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO events (event_name, event_date, event_venue, added_by) VALUES (%s, %s, %s, %s)', 
                       (event_name, event_date, event_venue, current_user.id))
        mysql.connection.commit()
        cursor.close()  # Close the cursor after use
        return redirect(url_for('dashboard'))
    return render_template('add_event.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
