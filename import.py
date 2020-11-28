import cs50
from sys import argv, exit
import csv
import math

# USAGE: Used to import a larger csv file into my db. Used it for styles and states.

# open that file in sqlite
db = cs50.SQL("sqlite:///beer.db")

if len(argv) != 2:
    print("Usage: python import.py ______.csv")
    exit(1)

with open(argv[1], "r") as styles:
    reader = csv.DictReader(styles)
    for row in reader:
        cat_id = row['cat_id']
        style = row['style_name']
        db.execute("INSERT INTO styles (cat_id, style) VALUES(?, ?)",
                    cat_id, style)