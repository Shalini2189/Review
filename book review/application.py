import os
import sqlite3
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
import requests
import csv

app = Flask(__name__)
    
@app.route("/")
def index():

    return redirect(url_for('register'))

@app.route("/register", methods=["GET", "POST"])
def register():
    con = sqlite3.connect('database.db')
    c = con.cursor()
    if request.method == "POST":
        usern = request.form["username"]
        passw = request.form["password"]
        c.execute("""create table if not exists accounts(username, password)""")
        
        result = c.execute("INSERT INTO accounts (username, password) VALUES (:u, :p)", {"u": usern, "p": passw})
        con.commit()

        return render_template("login.html", message='Succesfully registered')
    return render_template("registration.html", message=None)

@app.route("/logout")
def logout():
    return redirect(url_for('register'))

@app.route("/login", methods=["GET", "POST"])
def login():
    con = sqlite3.connect('database.db')
    c = con.cursor()
    if request.method == "POST":
        usern = request.form["username"]
        passw = request.form["password"]
        result = c.execute("SELECT * FROM accounts WHERE username = :u and password = :p", {"u": usern, "p" : passw}).fetchone()

        if result is not None:         
            if os.path.exists('log.txt'):
                os.remove('log.txt')
            f = open('log.txt', 'w')
            f.write(str(usern))
            f.close()
            
            return redirect(url_for('dashboard'))

        message = "Username or password is incorrect."
        return render_template("login.html", message=message)
    return render_template("login.html", message = None)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/dashboard/search", methods=["POST"])
def search():
    if request.method == 'POST':
        message = None
        con = sqlite3.connect('database.db')
        c = con.cursor()
        query = request.form["searchbox"]
        query = '%' + query.lower() + '%'
        results = c.execute("SELECT * FROM books WHERE lower(title) LIKE :q OR isbn LIKE :q OR lower(author) LIKE :q OR lower(year) LIKE :q", {"q": query}).fetchall()
        print(results)
        return render_template("search.html", results=results)
    return render_template("dashboard.html")

@app.route("/searching/<name>")
def searching(name):
    message = None
    con = sqlite3.connect('database.db')
    c = con.cursor()
    # query = request.form["searchbox"]
    query = '%' + name.lower() + '%'
    results = c.execute("SELECT * FROM books WHERE lower(author) LIKE :q", {"q": query}).fetchall()
    print(results)
    return render_template("search.html", results=results)


@app.route("/info/<string:isbn>", methods=["GET", "POST"])
def info(isbn):
    con = sqlite3.connect('database.db')
    c = con.cursor()
    if request.method == "POST":
        comment = request.form["comment"]
        my_rating = request.form["rating"]
        print(my_rating)
        f = open('log.txt', 'r')
        user=f.read()
        f.close()
        c.execute("""create table if not exists review(book_id, comment, rating)""")
        book = c.execute("INSERT INTO review (user, book_id, comment, rating) VALUES (:u, :b, :c, :r)", {"u": user, "b": isbn, "c": comment, "r": my_rating})
        con.commit()

    book = c.execute("SELECT * FROM books WHERE isbn = :q", {"q": isbn}).fetchone()
    reviews = c.execute("SELECT * FROM review WHERE book_id = :q1", {"q1": isbn}).fetchall()

    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "1O7xiWC9D6p2JmdhgX4LTw", "isbns": isbn})
    data = response.json()
    gr_rating = (data['books'][0]['average_rating'])

    return render_template("info.html", book_info=book, reviews=reviews, rating=gr_rating)

@app.route("/api/<string:isbn>")
def api(isbn):
    con = sqlite3.connect('database.db')
    c = con.cursor()
    book = c.execute("SELECT * FROM books WHERE isbn = :q", {"q": isbn}).fetchone()
    
    if book is None:
        return jsonify({"error": "Invalid ISBN"}), 404
    
    c.execute("""create table if not exists review(user, book_id, comment, rating)""")
    book = c.execute("SELECT * FROM books WHERE isbn = :q", {"q": isbn}).fetchone()
    reviews = c.execute("SELECT * FROM review WHERE book_id = :q1", {"q1": isbn}).fetchall()

    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "1O7xiWC9D6p2JmdhgX4LTw", "isbns": isbn})
    data = response.json()
    gr_rating = (data['books'][0]['average_rating'])

    return render_template("info.html", book_info=book, reviews=reviews, rating=gr_rating)

if __name__ == "__main__":
    app.run(debug=True)
