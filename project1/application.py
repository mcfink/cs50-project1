import os
import requests

from flask import Flask, session, render_template, request, url_for, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import config

import credentials as cred

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=['GET', 'POST'])
def index():
    books = db.execute("SELECT * FROM books").fetchall()

    if session.get("user") is None:
        message = "Please log in or create an account"
        return render_template("index.html",
                               books=books,
                               message=message,
                               login_form_class='show',
                               user='')

    else:
        message = f"Welcome {session['user']}!"
        return render_template("index.html",
                               books=books,
                               message=message,
                               login_form_class='hide',
                               user=session['user'])


@app.route('/logout')
def logout():
    print('logging out')
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['username']
    return redirect(url_for("index"))

@app.route("/search", methods= ['GET', 'POST'])
def search():
    if request.method == 'GET':
        listofbooks = []
    if request.method == 'POST':
        search_term = request.form.get('search_term')

        listofbooks = db.execute(f"SELECT * FROM books WHERE LOWER(author) LIKE LOWER('{search_term}%') OR LOWER(title) LIKE LOWER('{search_term}%') OR isbn LIKE '%{search_term}%'").fetchall()

    return render_template('search.html',  listofbooks=listofbooks)

@app.route("/books/<isbn>", methods= ['GET', 'POST'])
def book(isbn):
    # make sure book exists
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    book_id = book['id']
    five_reviews = db.execute(f"SELECT * FROM reviews JOIN users ON reviews.user_id = users.id WHERE book_id = {book_id}").fetchall()
    good_reads_stats = requests.get('https://www.goodreads.com/book/review_counts.json', params={'key': cred.GOODREADS_KEY, 'isbns': f'{isbn}', 'format': 'json'}).json()
    good_reads_iframe = requests.get(f'https://www.goodreads.com/book/isbn/{isbn}?format=json&user_id=103548334').json()['reviews_widget']
    if book is None:
        return render_template('error.html', message="ISBN not found.")

    if request.method == 'POST':
        review_text = request.form.get('review-text')
        username = session['user']
        user_id = db.execute(f"SELECT id FROM users WHERE username = '{username}'").fetchone()[0]
        print(user_id)
        book_id = book['id']
        print(review_text)
        print(username)
        print(book_id)
        previous_review = db.execute(f"SELECT * FROM reviews WHERE user_id = {user_id} AND book_id = {book_id}").fetchone()
        print(previous_review)
        if previous_review is not None:
            return render_template('error.html', message="Greetings Chap! It appears you've already submitted a review for this book -- only one review per book, please!")

        db.execute("INSERT INTO reviews (user_id, book_id, review_text) VALUES (:user_id, :book_id, :review_text)",
                   {"user_id": user_id, "book_id": book_id, "review_text": review_text})
        db.commit()

    return render_template("book.html", book=book,
                           five_reviews=five_reviews,
                           good_reads_total_ratings=good_reads_stats['books'][0]['ratings_count'],
                           good_reads_average_rating=good_reads_stats['books'][0]['average_rating'],
                           good_reads_iframe=good_reads_iframe)

@app.route("/hello", methods=["POST"])
def hello():
    name = request.form.get("name")
    return render_template("hello.html", name=name)

@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/register_land", methods=['POST'])
def register_land():
    username = request.form.get("username")
    password = request.form.get("password")
    print(username)
    print(password)

    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password})
    db.commit()
    message = f'Welcome {username} -- Thank you for registering!'
    users = db.execute(f"SELECT * FROM users").fetchall()

    print(users)
    return render_template('register_land.html',
                           username=username,
                           password=password,
                           message=message)


@app.route("/api/<isbn>")
def book_api(isbn):
    """Return stats on book - json response with title, author, year, isbn, review_count, average_score """
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "ISBN not in database"}), 404
    good_reads_stats = requests.get('https://www.goodreads.com/book/review_counts.json',
                                    params={'key': cred.GOODREADS_KEY, 'isbns': f'{isbn}', 'format': 'json'}).json()
    return jsonify({
        "title": book['title'],
        "author": book['author'],
        "year": book['year'],
        "isbn": book['isbn'],
        "review_count": good_reads_stats['books'][0]['ratings_count'],
        "average_score": good_reads_stats['books'][0]['average_rating']
    })




