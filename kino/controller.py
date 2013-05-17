from flask import render_template, make_response, request, redirect, url_for, Response, g, jsonify
from datetime import datetime
from operator import attrgetter
import json

from . import app, db
from .model import *

@app.before_request
def before_request():
    """Ensures that user is authenticated and fills some global variables"""
    try:
        user = request.authorization.username
        if user:
            g.user = User.query.filter_by(name=user).first()
            if not g.user:
                g.user = User(name=user)
                db.session.add(g.user)
                db.session.commit()
        else:
            return login()
    except AttributeError:
        return login()

    g.events = Event.query \
                    .filter_by(canceled=False) \
                    .filter(Event.date >= datetime.now()) \
                    .order_by(Event.date.asc())
    g.now = datetime.now()

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
    """Shows the voted movies for an event"""
    event = Event.query.filter_by(id=id).first()
    if not event:
        return make_response(
            render_template('error.html', errormsg='The event you requested was not found.'),
            404
        )
    event.movies = {}
    voted_movies = [vote.movie for vote in Vote.query.filter_by(user=g.user, event=event)]
    for vote in event.votes:
        if event.movies.has_key(vote.movie.id):
            event.movies[vote.movie.id].count += 1
        else:
            event.movies[vote.movie.id] = vote.movie
            event.movies[vote.movie.id].voted = vote.movie in voted_movies
            event.movies[vote.movie.id].count = 1
    event.movies = sorted(event.movies.values(), key=attrgetter('count'), reverse=True)
    event.voted = len(voted_movies) > 0
    return render_template('event.html', event=event)

@app.route('/find_movie')
def find_film():
    """Searches for movies using a partial movie name"""
    movies = Movie.query.filter(Movie.name.like('%%%s%%' % request.args['term'])).all()
    return Response(
        json.dumps([{'id': movie.id, 'value': movie.name + ' (' + movie.year + ')'} for movie in movies]),
        200,
        None,
        'application/json'
    )

@app.route('/movie/<int:id>')
def movie_info(id):
    """Gives detailed information about a movie"""
    movie = Movie.query.filter_by(id=id).first()
    if not movie:
        return jsonify({})
    return jsonify(movie.serialize)

@app.route('/movie/next_winning')
def next_winning_movie_info():
    """Gives detailed information about the currently winning movie of the next event"""
    # to get the currently running event if some event is running, we ask for
    # the next event after today's mitdnight
    event = Event.query \
                .filter_by(canceled=False) \
                .filter(Event.date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)) \
                .order_by(Event.date.asc()) \
                .first()
    if not event:
        return jsonify({})
    if not event.votes:
        return jsonify({})
    event.movies = {}
    for vote in event.votes:
        if vote.movie.id in event.movies:
            event.movies[vote.movie.id].count += 1
        else:
            event.movies[vote.movie.id] = vote.movie
            event.movies[vote.movie.id].count = 1
    event.movies = sorted(event.movies.values(), key=attrgetter('count'), reverse=True)
    return movie_info(event.movies[0].id)

@app.route('/vote', methods=['POST'])
def vote():
    """Votes for a set of movies for an event. Can update previous votes."""
    event_id = request.form['event_id']
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        return make_response(
            render_template('error.html', errormsg='The event you voted for doesn\'t exist!'),
            404
        )
    if event.date < datetime.now():
        return make_response(
            render_template('error.html', errormsg='Voting for an event in the past isn\'t possible!'),
            403
        )
    if event.canceled:
        return make_response(
            render_template('error.html', errormsg='Voting for a canceled event isn\'t possible!'),
            403
        )
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
