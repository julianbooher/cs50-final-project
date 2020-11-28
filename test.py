import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

def id_lookup(idInput, idString, nameString, dblist):
    for x in dblist:
        if x[idString] == idInput:
            print(x[nameString])
db = SQL("sqlite:///beer.db")







def average_rating(beer_id):
    ratings_array = db.execute("SELECT * FROM ratings WHERE beer_id = :beer_id", beer_id = beer_id)
    average = 0
    for x in ratings_array:
        average += x["rating"]
    average = round(average/len(ratings_array))
    return average

print(average_rating(2))