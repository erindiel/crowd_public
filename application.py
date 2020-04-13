import os
import json

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///crowd.db")

@app.route("/")
@login_required
def index():
    lights = db.execute("SELECT * FROM lights")

    lat_lights = []
    lng_lights = []

    for light in lights:
        lat_lights.append(light["lat"])
        lng_lights.append(light["lng"])

    crosswalks = db.execute("SELECT * FROM crosswalks")

    lat_crosswalks = []
    lng_crosswalks = []

    for crosswalk in crosswalks:
        lat_crosswalks.append(crosswalk["lat"])
        lng_crosswalks.append(crosswalk["lng"])

    return render_template("index.html",lat_lights=lat_lights,lng_lights=lng_lights,lat_crosswalks=lat_crosswalks,lng_crosswalks=lng_crosswalks)

@app.route('/annotate', methods = ["GET","POST"])
def annotate():
    if request.method == "GET":

        crosswalks = db.execute("SELECT * FROM crosswalks")

        lat_crosswalks = []
        lng_crosswalks = []

        for crosswalk in crosswalks:
            lat_crosswalks.append(crosswalk["lat"])
            lng_crosswalks.append(crosswalk["lng"])

        return render_template("annotate.html",lat_crosswalks=lat_crosswalks,lng_crosswalks=lng_crosswalks)

    else:
        # read json + reply
        data = request.get_json()
        result = ''

        for item in data:
            # loop over every row
            result += 'added' + str(item['lat']) + ', ' + str(item['lng']) + '\n'
            db.execute("INSERT INTO crosswalks (lat, lng, creatorID) VALUES (:lat, :lng, :userid)", lat = item['lat'], lng = item['lng'], userid = session["user_id"])

        # return result
        crosswalks = db.execute("SELECT * FROM crosswalks")

        lat_crosswalks = []
        lng_crosswalks = []

        for crosswalk in crosswalks:
            lat_crosswalks.append(crosswalk["lat"])
            lng_crosswalks.append(crosswalk["lng"])

        return render_template("annotate.html",lat_crosswalks=lat_crosswalks,lng_crosswalks=lng_crosswalks)

@app.route('/stats', methods = ["GET"])
def stats():

    allcrosswalks = db.execute("SELECT * FROM crosswalks;")
    total = len(allcrosswalks)

    crosswalks = db.execute("SELECT * FROM crosswalks JOIN users ON crosswalks.creatorID = users.id WHERE users.id == :userid;", userid=session["user_id"])

    lat_crosswalks = []
    lng_crosswalks = []

    for crosswalk in crosswalks:
        lat_crosswalks.append(crosswalk["lat"])
        lng_crosswalks.append(crosswalk["lng"])

    sub = len(lat_crosswalks)

    return render_template("stats.html",lat_crosswalks=lat_crosswalks,lng_crosswalks=lng_crosswalks,sub=sub,total=total)

@app.route('/latenight', methods = ["GET"])
def latenight():

    lights = db.execute("SELECT * FROM lights")

    lat_lights = []
    lng_lights = []

    for light in lights:
        lat_lights.append(light["lat"])
        lng_lights.append(light["lng"])

    return render_template("latenight.html",lat_lights=lat_lights,lng_lights=lng_lights)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # # Ensure username does not exist
        if len(rows) != 0:
            return apology("username already exists", 403)

        row_ID = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=request.form.get("username"), hash = generate_password_hash(request.form.get("password")))

        # Remember which user has logged in
        session["user_id"] = row_ID

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
