from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"  

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  
    'database': 'blog'
}


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None


def create_tables():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
    
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
       
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        connection.commit()
        connection.close()
    else:
        print("Error: Unable to connect to the database for table creation")


create_tables()


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, title, slug FROM posts")
        posts = cursor.fetchall()
        connection.close()
        return render_template('index.html', posts=posts)
    else:
        return "Error connecting to the database", 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, password_hash)
                )
                connection.commit()
                connection.close()
                return redirect(url_for('login'))
            except mysql.connector.Error as e:
                connection.close()
                return f"Error: {e}", 400

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            connection.close()
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                return redirect(url_for('index'))
            else:
                return "Invalid credentials", 401

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        description = request.form['description']

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO posts (title, slug, description) VALUES (%s, %s, %s)",
                (title, slug, description)
            )
            connection.commit()
            connection.close()
            return redirect(url_for('index'))
        else:
            return "Error connecting to the database", 500

    return render_template('create_post.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    if not connection:
        return "Error connecting to the database", 500

    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        description = request.form['description']

        cursor = connection.cursor()
        cursor.execute(
            "UPDATE posts SET title = %s, slug = %s, description = %s WHERE id = %s",
            (title, slug, description, id)
        )
        connection.commit()
        connection.close()
        return redirect(url_for('index'))

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
    post = cursor.fetchone()
    connection.close()

    if not post:
        return "Post not found", 404

    return render_template('edit_post.html', post=post)


@app.route('/post/<slug>')
def view_post(slug):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT title, description FROM posts WHERE slug = %s", (slug,))
        post = cursor.fetchone()
        connection.close()
        if not post:
            return "Post not found", 404
        return render_template('view_post.html', post=post)
    else:
        return "Error connecting to the database", 500

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    if not connection:
        return "Error connecting to the database", 500

    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        description = request.form['description']

        cursor = connection.cursor()
        cursor.execute(
            "UPDATE posts SET title = %s, slug = %s, description = %s WHERE id = %s",
            (title, slug, description, id)
        )
        connection.commit()
        connection.close()
        return redirect(url_for('index'))

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
    post = cursor.fetchone()
    connection.close()

    if not post:
        return "Post not found", 404

    return render_template('edit_post.html', post=post)

if __name__ == '__main__':
    app.run(debug=True)
