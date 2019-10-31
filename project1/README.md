# Project 1

Web Programming with Python and JavaScript

This Flask project uses Heroku's free Postgres SQL service, Goodreads API, and a few python libraries to make a simple book review site.

Files:
application.py - the Flask app.  Serves information to all of the templates.

layout.html - layout for all other html files.  contains a header block and body block to be used by other pages.

error.html - general purpose error page with a cconfigurable message to let users know what went wrong.

login.html - login page

register.html - page for new users to register

search.html - page for searching for a particular book, author, or isbn

book.html - detail page for a particular book where you can write a review or check out the goodreads stats.

config.py - contains the database information

credentials.py - contains goodreads credentials

import.py - used to seed the db

requirements.txt - libraries used
