from flask import Flask, render_template, request, redirect, url_for, session, Response, g, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
import locale

try:
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'de_DE')
    except locale.Error:
        pass

app = Flask(__name__)
app.config.from_object(__name__ + '.config')
app.template_filter('set')(set) # register set() as a filter
db = SQLAlchemy(app)

from model import *
from controller import *

if __name__ == "__main__":
    # run standalone webserver
    app.run(debug=True)
