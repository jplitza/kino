from flask import render_template, request, redirect, url_for, session, Response, g, jsonify
from datetime import datetime
from operator import itemgetter
import json

from . import app
from .model import *

@app.before_request
def before_request():
    "Ensures that user is authenticated and fills some global variables"
    try:
        user = request.authorization.username
        if user:
            g.user = User.query.filter_by(name=user).first()
            if not g.user:
                g.user = User(name=user)
                db.session.add(g.user)
                db.session.commit()
    except AttributeError:
        return login()

    g.events = Event.query \
                    .filter_by(canceled=False) \
                    .filter(Event.date >= datetime.now()) \
                    .order_by(Event.date.asc())

@app.route('/login')
def login():
    """Sends a 401 response that enables basic auth"""
    return Response('You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/event/<int:id>')
def event(id):
    event = Event.query.filter_by(id=id).first()
    event.movies = {}
    voted_movies = [vote.movie for vote in Vote.query.filter_by(user=g.user, event=event)]
    for vote in event.votes:
        if event.movies.has_key(vote.movie.id):
            event.movies[vote.movie.id]['count'] += 1
        else:
            event.movies[vote.movie.id] = vote.movie.serialize
            event.movies[vote.movie.id]['voted'] = vote.movie in voted_movies
            event.movies[vote.movie.id]['count'] = 1
    event.movies = sorted(event.movies.values(), key=itemgetter('count'), reverse=True)
    event.voted = len(voted_movies) > 0
    return render_template('event.html', event=event)

@app.route('/find_movie')
def find_film():
    movies = Movie.query.filter(Movie.name.like('%%%s%%' % request.args['term'])).all()
    return Response(
        json.dumps([{'id': movie.id, 'value': movie.name + ' (' + movie.year + ')'} for movie in movies]),
        200,
        None,
        'application/json'
    )

@app.route('/movie/<int:id>')
def movie_info(id):
    movie = Movie.query.filter_by(id=id).first()
    return jsonify(movie.serialize)

@app.route('/vote', methods=['POST'])
def vote():
    event_id = request.form['event_id']
    event = Event.query.filter_by(id=event_id).first()
    if event.canceled:
        return render_template('error.html', errormsg='Voting for a canceled event isn\'t possible!')
    votes = Vote.query.filter_by(user=g.user, event=event)
    voted_movies = dict((vote.movie.id, vote) for vote in votes)
    for movie_id in request.form.getlist('movies[]'):
        movie = Movie.query.filter_by(id=movie_id)
        if movie:
            if movie_id in voted_movies.keys():
                # change nothing about this vote and remove it from the list
                votes.remove(voted_movies[movie_id])
            else:
                vote = Vote(user=g.user, event=event, movie_id=movie_id)
                db.session.add(vote)

    # the votes remaining in the list are no longer voted, so remove them
    for vote in votes:
        db.session.delete(vote)

    db.session.commit()
    return redirect(url_for('event', id=event_id))
