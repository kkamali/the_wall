from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from flask.ext.bcrypt import Bcrypt
import re

app = Flask(__name__)
app.secret_key = 'ThisIsSecret'
mysql = MySQLConnector(app,'the_wall')
bcrypt = Bcrypt(app)


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    canGoOn = True
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    session['email'] = request.form['email']
    password = request.form['password']
    confirmation = request.form['confirm']
    if (len(first_name) < 2):
        flash("First Name cannot be empty!")
        canGoOn = False
    if (not first_name.isalpha()):
        flash("First Name cannot contain numbers!")
        canGoOn = False
    if (not last_name.isalpha()):
        flash("Last Name cannot contain numbers!")
        canGoOn = False
    if (len(last_name) < 2):
        flash("Last Name cannot be empty!")
        canGoOn = False
    if (not EMAIL_REGEX.match(request.form['email'])):
        flash("Not valid email address!")
        canGoOn = False
    if (len(password) < 8):
        flash("Password cannot be less than 8 characters!")
        canGoOn = False
    if (confirmation != password):
        flash("Passwords don't match!")
        canGoOn = False
    if (canGoOn == False):
        return redirect("/")
    else:
        pw_hash = bcrypt.generate_password_hash(password)
        query = "INSERT INTO the_wall.users (email, password, first_name, last_name, created_at, updated_at) VALUES (:email, :password, :first_name, :last_name, NOW(), NOW())"
        data = {
            'email' : request.form["email"],
            'password' : pw_hash,
            'first_name' : request.form["first_name"],
            'last_name' : request.form["last_name"]
            }
        mysql.query_db(query, data)
        return render_template("wall.html", first_name = first_name)

@app.route("/login", methods=["POST"])
def login():
    session['email'] = request.form['email']
    password = request.form['password']
    user_query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    query_data = { 'email': session['email'] }
    user = mysql.query_db(user_query, query_data)
    session['commenter'] = user[0]['first_name'] + " " + user[0]['last_name']
    if bcrypt.check_password_hash(user[0]['password'], password):
        user_id = user[0]['id']
        messages_query = ("SELECT messages.id, messages.message, messages.created_at, users.first_name, users.last_name, users.id AS user_id FROM users JOIN messages ON messages.user_id = users.id ")
        session['messages'] = mysql.query_db(messages_query)
        return render_template("wall.html", first_name = user[0]['first_name'], messages = session['messages'], comments = session["comments"])
    else:
        flash("Login incorrect!")
        return redirect("/")

@app.route("/submit_message", methods=["POST"])
def submit_message():
    message = request.form['message']
    user_query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    query_data = { 'email': session['email'] }
    user = mysql.query_db(user_query, query_data)
    user_id = user[0]['id']
    query = "INSERT INTO the_wall.messages (user_id, message, created_at, updated_at) VALUES (:user_id, :message, NOW(), NOW())"
    add_data = {
        'user_id' : user_id,
        'message' : message
    }
    add_messages = mysql.query_db(query, add_data)
    messages_query = ("SELECT messages.id, messages.message, messages.created_at, users.first_name, users.last_name, users.id AS user_id FROM users JOIN messages ON messages.user_id = users.id ")
    session['messages'] = mysql.query_db(messages_query)
    return render_template("wall.html", first_name = user[0]['first_name'], messages = session['messages'], comments = session["comments"])

@app.route("/comment", methods=["POST"])
def submit_comment():
    message_id = request.form['message_id']
    comment = request.form['comment']
    user_id = request.form['user_id']
    user_query = "SELECT * FROM users WHERE id = :user_id"
    query_data = { 'user_id': user_id }
    user = mysql.query_db(user_query, query_data)
    query = ("INSERT INTO the_wall.comments (users_id, messages_id, comment, created_at, updated_at) VALUES (:user_id, :message_id, :comment, NOW(), NOW())")
    add_data = {
        'user_id' : user_id,
        'message_id' : message_id,
        'comment' : comment
    }
    add_comments = mysql.query_db(query, add_data)
    comments_query = ("SELECT messages.message, comments.comment, comments.created_at, users.first_name, users.last_name, messages.id AS messages_id FROM users JOIN messages ON messages.user_id = users.id JOIN comments ON comments.messages_id = messages.id")
    session['comments'] = mysql.query_db(comments_query)
    return render_template("wall.html", first_name = user[0]['first_name'], messages = session['messages'], comments = session['comments'], commenter = session['commenter'])

app.run(debug=True)
