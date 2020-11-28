import os
import requests
import urllib.parse

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


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
db = SQL("sqlite:///beer.db")


def average_rating(beer_id):
    ratings_array = db.execute("SELECT * FROM ratings WHERE beer_id = :beer_id", beer_id = beer_id)
    average = 0
    for x in ratings_array:
        average += x["rating"]
    average = round(average/len(ratings_array))
    return average
# function to find something by id in my lists of dictionaries
def id_lookup(idInput, idString, nameString, dblist):
    for x in dblist:
        if x[idString] == idInput:
            return x[nameString]

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Index page. Will display the beers that the current user has rated.
@app.route("/")
@login_required
def index():
    ratings = db.execute("SELECT * FROM ratings JOIN beers ON ratings.beer_id = beers.beer_id JOIN breweries ON beers.brewery_id = breweries.brewery_id WHERE user_id = :user_id", user_id=session["user_id"])
    return render_template("index.html", ratings=ratings, username=session["username"])

# Beer database page.
@app.route("/beers", methods=["GET", "POST"])
@login_required
def beers():
    if request.method == "GET":
        beers = db.execute("SELECT * FROM beers JOIN breweries ON beers.brewery_id = breweries.brewery_id JOIN styles ON beers.style_id = styles.style_id ")
        return render_template("beers.html", beers=beers)
    if request.method == "POST":
        beers = db.execute("SELECT * FROM beers JOIN breweries ON beers.brewery_id = breweries.brewery_id JOIN styles ON beers.style_id = styles.style_id ")
        current_beer = request.form.get("rate_beer")
        return render_template("beer.html", beers=beers, show_beer=1, beer_id=current_beer)


# Displays a page that lists all of the info for a single beer as well as forms to rate it.

@app.route("/beer", methods=["GET", "POST"])
@login_required
def rate():
    if request.method == "GET":
        # Beer ID coming from "beers.html", will be used in sql query to display all of the info about that beer, and later to be a part of the rating for that beer.
        current_beer = request.args.get("rate_beer")
        # Create a dict that has all of the info for the specified beer.
        current_beer_info = db.execute("SELECT * FROM beers JOIN breweries ON beers.brewery_id = breweries.brewery_id JOIN styles ON beers.style_id = styles.style_id WHERE beer_id=:beer_id", beer_id=current_beer )
        # List to check if the user has already rated this beer.
        rating_check = db.execute ("SELECT * FROM ratings WHERE user_id = :user_id AND beer_id = :beer_id", user_id=session["user_id"], beer_id=current_beer)
        if len(rating_check) > 0:
            return render_template("beer.html", avg_rating=current_beer_info[0]["avg_rating"], rating_check=rating_check, current_beer = current_beer, beer=current_beer_info[0]["beer_name"], brewery=current_beer_info[0]["brewery_name"],
            style=current_beer_info[0]["style"], abv=current_beer_info[0]["abv"], city=current_beer_info[0]["city"], state=current_beer_info[0]["state"],
            img=current_beer_info[0]["beer_img"])
        else:
            return render_template("beer.html", avg_rating=current_beer_info[0]["avg_rating"], rating_check=None, current_beer = current_beer, beer=current_beer_info[0]["beer_name"], brewery=current_beer_info[0]["brewery_name"],
            style=current_beer_info[0]["style"], abv=current_beer_info[0]["abv"], city=current_beer_info[0]["city"], state=current_beer_info[0]["state"],
            img=current_beer_info[0]["beer_img"])


    if request.method == "POST":
        # Variable to hold the current beer's id
        current_beer = request.form.get("submit_rating")
        # Create a dict that has all of the info for the specified beer.
        current_beer_info = db.execute("SELECT * FROM beers JOIN breweries ON beers.brewery_id = breweries.brewery_id JOIN styles ON beers.style_id = styles.style_id WHERE beer_id=:beer_id", beer_id=current_beer )
        # Integer, the user's rating of the current beer.
        rating = request.form.get("beerRating")
        # String, the user's tasting notes of the current beer
        tasting_notes = request.form.get("beerNotes")
        # List to check if the user has already rated that beer.
        rating_check = db.execute ("SELECT * FROM ratings WHERE user_id = :user_id AND beer_id = :beer_id", user_id=session["user_id"], beer_id=current_beer)
        if current_beer == None:
            # Variable to hold the current beer's id
            current_beer = request.form.get("update_rating")
            # Create a dict that has all of the info for the specified beer.
            current_beer_info = db.execute("SELECT * FROM beers JOIN breweries ON beers.brewery_id = breweries.brewery_id JOIN styles ON beers.style_id = styles.style_id WHERE beer_id=:beer_id", beer_id=current_beer )
            # List to check if the user has already rated that beer.
            rating_check = db.execute ("SELECT * FROM ratings WHERE user_id = :user_id AND beer_id = :beer_id", user_id=session["user_id"], beer_id=current_beer)
            # If the user doesn't enter tasting notes it will enter it as null into the SQL database.
            if tasting_notes == "None":
                tasting_notes = None
            if not rating:
                return render_template("beer.html", avg_rating=current_beer_info[0]["avg_rating"], error=1, rating_check=rating_check, rating=rating, tasting_notes=tasting_notes, current_beer=current_beer, beer=current_beer_info[0]["beer_name"], brewery=current_beer_info[0]["brewery_name"],
                style=current_beer_info[0]["style"], abv=current_beer_info[0]["abv"], city=current_beer_info[0]["city"], state=current_beer_info[0]["state"],
                img=current_beer_info[0]["beer_img"])
            if not tasting_notes:
                # Delete old rating.
                db.execute("DELETE FROM ratings WHERE user_id = :user_id AND beer_id = :beer_id", user_id=session["user_id"], beer_id=current_beer)
                # Insert new rating w/o tasting notes.
                db.execute("INSERT INTO ratings (beer_id, user_id, rating) VALUES (:beer_id, :user_id, :rating)",
                beer_id=current_beer, user_id=session["user_id"], rating=rating)
                rating_check = db.execute ("SELECT * FROM ratings WHERE user_id = :user_id AND beer_id = :beer_id", user_id=session["user_id"], beer_id=current_beer)
                avg_rating = average_rating(current_beer)
                db.execute("UPDATE beers SET avg_rating = :avg_rating WHERE beer_id = :beer_id", beer_id=current_beer, avg_rating=avg_rating)
                current_beer_info = db.execute("SELECT * FROM beers JOIN breweries ON beers.brewery_id = breweries.brewery_id JOIN styles ON beers.style_id = styles.style_id WHERE beer_id=:beer_id", beer_id=current_beer )
                return render_template("beer.html", avg_rating=avg_rating, message=4, rating_check=rating_check, rating=rating, tasting_notes=tasting_notes, current_beer=current_beer, beer=current_beer_info[0]["beer_name"], brewery=current_beer_info[0]["brewery_name"],
                style=current_beer_info[0]["style"], abv=current_beer_info[0]["abv"], city=current_beer_info[0]["city"], state=current_beer_info[0]["state"],
                img=current_beer_info[0]["beer_img"])
            else:
                # Delete old rating.
                db.execute("DELETE FROM ratings WHERE user_id = :user_id AND beer_id = :beer_id", user_id=session["user_id"], beer_id=current_beer)
                # Insert new rating w/ tasting notes.
                db.execute("INSERT INTO ratings (beer_id, user_id, rating, tasting_notes) VALUES (:beer_id, :user_id, :rating, :tasting_notes)",
                beer_id=current_beer, user_id=session["user_id"], rating=rating, tasting_notes=tasting_notes)
                rating_check = db.execute ("SELECT * FROM ratings WHERE user_id = :user_id AND beer_id = :beer_id", user_id=session["user_id"], beer_id=current_beer)
                avg_rating = average_rating(current_beer)
                db.execute("UPDATE beers SET avg_rating = :avg_rating WHERE beer_id = :beer_id", beer_id=current_beer, avg_rating=avg_rating)
                current_beer_info = db.execute("SELECT * FROM beers JOIN breweries ON beers.brewery_id = breweries.brewery_id JOIN styles ON beers.style_id = styles.style_id WHERE beer_id=:beer_id", beer_id=current_beer )
                return render_template("beer.html", avg_rating=avg_rating, message=3, rating_check=rating_check, rating=rating, tasting_notes=tasting_notes, current_beer=current_beer, beer=current_beer_info[0]["beer_name"], brewery=current_beer_info[0]["brewery_name"],
                style=current_beer_info[0]["style"], abv=current_beer_info[0]["abv"], city=current_beer_info[0]["city"], state=current_beer_info[0]["state"],
                img=current_beer_info[0]["beer_img"])

        else:
            if not rating:
                return render_template("beer.html", avg_rating=current_beer_info[0]["avg_rating"], rating_check=None, error=1, rating=rating, tasting_notes=tasting_notes, current_beer=current_beer, beer=current_beer_info[0]["beer_name"], brewery=current_beer_info[0]["brewery_name"],
                style=current_beer_info[0]["style"], abv=current_beer_info[0]["abv"], city=current_beer_info[0]["city"], state=current_beer_info[0]["state"],
                img=current_beer_info[0]["beer_img"])
            if not tasting_notes or tasting_notes.isspace() == True:
                db.execute("INSERT INTO ratings (beer_id, user_id, rating) VALUES (:beer_id, :user_id, :rating)",
                beer_id=current_beer, user_id=session["user_id"], rating=rating)
                rating_check = db.execute ("SELECT * FROM ratings WHERE user_id = :user_id AND beer_id = :beer_id", user_id=session["user_id"], beer_id=current_beer)
                avg_rating = average_rating(current_beer)
                db.execute("UPDATE beers SET avg_rating = :avg_rating WHERE beer_id = :beer_id", beer_id=current_beer, avg_rating=avg_rating)
                current_beer_info = db.execute("SELECT * FROM beers JOIN breweries ON beers.brewery_id = breweries.brewery_id JOIN styles ON beers.style_id = styles.style_id WHERE beer_id=:beer_id", beer_id=current_beer )
                return render_template("beer.html", avg_rating=avg_rating, rating_check=rating_check, message=2, rating=rating, tasting_notes=tasting_notes, current_beer=current_beer, beer=current_beer_info[0]["beer_name"], brewery=current_beer_info[0]["brewery_name"],
                style=current_beer_info[0]["style"], abv=current_beer_info[0]["abv"], city=current_beer_info[0]["city"], state=current_beer_info[0]["state"],
                img=current_beer_info[0]["beer_img"])
            else:
                db.execute("INSERT INTO ratings (beer_id, user_id, rating, tasting_notes) VALUES (:beer_id, :user_id, :rating, :tasting_notes)",
                beer_id=current_beer, user_id=session["user_id"], rating=rating, tasting_notes=tasting_notes)
                rating_check = db.execute ("SELECT * FROM ratings WHERE user_id = :user_id AND beer_id = :beer_id", user_id=session["user_id"], beer_id=current_beer)
                avg_rating = average_rating(current_beer)
                db.execute("UPDATE beers SET avg_rating = :avg_rating WHERE beer_id = :beer_id", beer_id=current_beer, avg_rating=avg_rating)
                current_beer_info = db.execute("SELECT * FROM beers JOIN breweries ON beers.brewery_id = breweries.brewery_id JOIN styles ON beers.style_id = styles.style_id WHERE beer_id=:beer_id", beer_id=current_beer )
                return render_template("beer.html", avg_rating=avg_rating, rating_check=rating_check, message=1, rating=rating, tasting_notes=tasting_notes, current_beer=current_beer, beer=current_beer_info[0]["beer_name"], brewery=current_beer_info[0]["brewery_name"],
                style=current_beer_info[0]["style"], abv=current_beer_info[0]["abv"], city=current_beer_info[0]["city"], state=current_beer_info[0]["state"],
                img=current_beer_info[0]["beer_img"])


# Brewery database page.
@app.route("/breweries", methods=["GET", "POST"])
@login_required
def breweries():
    if request.method == "GET":
        breweries = db.execute("SELECT * FROM breweries")
        return render_template("breweries.html", breweries=breweries)

# Submission page for submitting a brewery to admin approval.
@app.route("/submit_brewery", methods=["GET", "POST"])
@login_required
def submit_brewery():
    if request.method == "GET":
        # Dictionary with a list of states for the Brewery Submission form
        states = db.execute("SELECT abbreviation, state FROM states ORDER BY abbreviation")
        return render_template("submit_brewery.html", states=states)
    if request.method == "POST":
        # Dictionary with a list of states for the Brewery Submission form.
        states = db.execute("SELECT abbreviation, state FROM states ORDER BY abbreviation")
        # Variables from the forms on the submit page
        brewery_name = request.form.get("brewery_name")
        city = request.form.get("city")
        state = request.form.get("state")
        # Error check to make sure no forms were left blank.
        if not brewery_name or not city or not state:
            return render_template("submit_brewery.html", error=1, states=states)
        else:
            # If they past the error check, it will send their submission to be approved by an admin.
            db.execute("INSERT INTO brewery_submissions (brewery_name, city, state) VALUES (:name, :city, :state)",
            name=brewery_name, city=city, state=state)
            return render_template("submit_brewery.html", message=1, states=states, state=state, brewery_name=brewery_name, city=city)

# Submission function for submitting a beer to admin approval table.
@app.route("/submit_beer", methods=["GET", "POST"])
@login_required
def submit_beer():
    if request.method == "GET":
        # Dict of styles and their respective id's
        styles = db.execute("SELECT style, style_id FROM styles")
        # Dict of breweries and their respective id's
        breweries = db.execute("SELECT brewery_name, brewery_id FROM breweries")
        return render_template("submit_beer.html", styles=styles, breweries=breweries)
    if request.method == "POST":
        styles = db.execute("SELECT style, style_id FROM styles")
        breweries = db.execute("SELECT brewery_name, brewery_id FROM breweries")
        # Variables from the forms on the submit page
        style_id = request.form.get("style")
        brewery_id = request.form.get("brewery")
        # Look up the names of the brewery and the style to display back to the user when the beer is submitted.
        style_name =  id_lookup(int(style_id), 'style_id', 'style', styles)
        brewery_name = id_lookup(int(brewery_id), 'brewery_id', 'brewery_name', breweries)
        abv = request.form.get("abv")
        name = request.form.get("name")
        beer_img = request.form.get("img")
        # Error check to make sure no forms were left blank.
        if not style_id or not brewery_id or not name or not beer_img:
            return render_template("submit_beer.html", styles=styles, breweries=breweries, error=1)
        # Not all beer has ABV listed, so it will be null if they don't send it with an abv.
        if not abv:
            abv = None
        # If it passes the error checks, send it to the submissions table for admin approval.
        db.execute("INSERT INTO beer_submissions (beer_name, brewery_id, style_id, abv, beer_img) VALUES (:name, :brewery_id, :style_id, :abv, :beer_img)",
        name=name, style_id=style_id, brewery_id=brewery_id, abv=abv, beer_img=beer_img)
        return render_template("submit_beer.html", styles=styles, breweries=breweries, style=style_id, brewery=brewery_id,
        abv=abv, name=name, brewery_name=brewery_name, style_name=style_name, message=1)

# Submission function for submitting a style to admin approval table.
@app.route("/submit_style", methods=["GET", "POST"])
@login_required
def submit_style():
    if request.method == "GET":
        return render_template("submit_style.html")
    if request.method == "POST":
        return render_template("submit_style.html")

# Submissions list for admin. Allows the admin to approve/deny Beer/Brewery/Style Submissions.
@app.route("/submissions", methods=["GET", "POST"])
@login_required
def submissions():
    if session["admin"] == True:
        if request.method == "GET":
            brewery_submissions = db.execute("SELECT * FROM brewery_submissions")
            beer_submissions = db.execute("SELECT * FROM beer_submissions JOIN breweries ON beer_submissions.brewery_id = breweries.brewery_id JOIN styles ON beer_submissions.style_id = styles.style_id")
            return render_template("submissions.html", brewery_submissions=brewery_submissions, beer_submissions=beer_submissions)

        if request.method == "POST":
            brewery_submissions = db.execute("SELECT * FROM brewery_submissions")
            beer_submissions = db.execute("SELECT * FROM beer_submissions JOIN breweries ON beer_submissions.brewery_id = breweries.brewery_id JOIN styles ON beer_submissions.style_id = styles.style_id")
            # Approve/Decline buttons, the value of which is the submission ID of the respective beer/brewery/style.
            approve_brewery = request.form.get("approve_brewery")
            decline_brewery = request.form.get("decline_brewery")
            approve_beer = request.form.get("approve_beer")
            decline_beer = request.form.get("decline_beer")
            # What happens when each approval/decline is pressed. Eventually these will post the submission to the corresponding database if approved
            # or deleted from the submissions database if declined.
            if approve_brewery != None:
                # Makes a dict of the values from the approved brewery
                approved_brewery = db.execute("SELECT * FROM brewery_submissions WHERE submission_id = :submission_id", submission_id = approve_brewery)
                # Insert those values into the breweries table
                db.execute("INSERT INTO breweries (brewery_name, city, state) VALUES (:brewery_name, :city, :state)",
                brewery_name=approved_brewery[0]["brewery_name"], city=approved_brewery[0]["city"], state=approved_brewery[0]["state"])
                # Delete the submission from the submissions table, as it has now been approved.
                db.execute("DELETE FROM brewery_submissions WHERE submission_id = :submission_id", submission_id = approve_brewery)
                # Refresh the brewery submissions table to be passed to the HTML page that will be rendered.
                brewery_submissions = db.execute("SELECT * FROM brewery_submissions")
                return render_template("submissions.html", brewery_submissions=brewery_submissions, beer_submissions=beer_submissions, message=1,
                brewery=approved_brewery[0]["brewery_name"], city=approved_brewery[0]["city"], state=approved_brewery[0]["state"])
            if decline_brewery != None:
                # Dict of the declined brewery's info, to be passed to the html message after a brewery is declined.
                declined_brewery = db.execute("SELECT * FROM brewery_submissions WHERE submission_id = :submission_id", submission_id = decline_brewery)
                # Delete the submission from the submissions table, as it has now been declined.
                db.execute("DELETE FROM brewery_submissions WHERE submission_id = :submission_id", submission_id = decline_brewery)
                # Refreshes the list of brewery submissions to be passed to the HTML page that will be rendered.
                brewery_submissions = db.execute("SELECT * FROM brewery_submissions")
                return render_template("submissions.html", brewery_submissions=brewery_submissions, beer_submissions=beer_submissions, message=2,
                brewery=declined_brewery[0]["brewery_name"], city=declined_brewery[0]["city"], state=approved_brewery[0]["state"])
            if approve_beer != None:
                # Dict of the approved beer's information.
                approved_beer = db.execute("SELECT * FROM beer_submissions JOIN breweries ON beer_submissions.brewery_id = breweries.brewery_id JOIN styles ON beer_submissions.style_id = styles.style_id WHERE submission_id = :submission_id", submission_id = approve_beer)
                # Insert the approved beer's information into the beer sql database.
                db.execute("INSERT INTO beers (beer_name, brewery_id, style_id, abv, beer_img) VALUES (:beer_name, :brewery_id, :style_id, :abv, :beer_img)",
                beer_name=approved_beer[0]["beer_name"], brewery_id=approved_beer[0]["brewery_id"], style_id=approved_beer[0]["style_id"],
                abv=approved_beer[0]["abv"], beer_img=approved_beer[0]["beer_img"])
                # Delete the submission from the submission's database as it has been approved.
                db.execute("DELETE FROM beer_submissions WHERE submission_id = :submission_id", submission_id = approve_beer)
                # Update the beer submissions table to be passed to the html page that will be rendered.
                beer_submissions = db.execute("SELECT * FROM beer_submissions")
                return render_template("submissions.html", brewery_submissions=brewery_submissions, beer_submissions=beer_submissions, message=3,
                beer=approved_beer[0]["beer_name"], brewery=approved_beer[0]["brewery_name"])
            if decline_beer != None:
                # Dict of the declined beer's information.
                declined_beer = db.execute("SELECT * FROM beer_submissions JOIN breweries ON beer_submissions.brewery_id = breweries.brewery_id JOIN styles ON beer_submissions.style_id = styles.style_id WHERE submission_id = :submission_id", submission_id = decline_beer)
                # Delete the declined beer from the submissions table.
                db.execute("DELETE FROM beer_submissions WHERE submission_id = :submission_id", submission_id=decline_beer)
                # Update the beer submissions table to be passed to the html page that will be rendered.
                beer_submissions = db.execute("SELECT * FROM beer_submissions")
                return render_template("submissions.html", brewery_submissions=brewery_submissions, beer_submissions=beer_submissions, message=4,
                beer=declined_beer[0]["beer_name"], brewery=declined_beer[0]["brewery_name"])


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
        session["user_id"] = rows[0]["user_id"]
        session["username"] = rows[0]["username"]

        # Remember if logged in user is admin
        if rows[0]["admin"] == "TRUE":
            session["admin"] = True

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

# Registration page.
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        #ensure the user submitted a username
        if not username:
            return apology("Must provide username")

        password = request.form.get("password")
        # ensure the user submitted a password
        if not password:
            return apology("Must Provide Password")

        confirmation = request.form.get("confirmation")
        # ensure the user submitted a password confirmation
        if not confirmation:
            return apology("Must Provide Password Confirmation")

        # ensure the confirmation and the password match
        if confirmation != password:
            return apology("password must match password confirmation")

        # error checking to ensure username doesn't exist yet
        check = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if len(check) > 0:
            return apology("Sorry, username already exists.")

        # hash the password to store in the database
        passwordhash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :passwordhash)", username=username, passwordhash=passwordhash)
    return login()

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

