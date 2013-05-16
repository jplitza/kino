from sqlalchemy import *
from sqlalchemy.ext.associationproxy import association_proxy, _AssociationSet
import operator

from . import db

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, unique=True, index=True, nullable=False)
    canceled = db.Column(db.Boolean, nullable=False, default=False)
    mailed = db.Column(db.Boolean, nullable=False, default=False)
    comment = db.Column(db.String(256))
#    movies = association_proxy('votes', 'movie')
    users = association_proxy('votes', 'user')

    def __repr__(self):
        return '<Event at %s>' % self.date.strftime("%Y-%m-%d %H:%M:%S")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, index=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.name

class Movie(db.Model):
    __bind_key__ = 'xbmc'
    __tablename__ = 'movie'
    id = db.Column('idMovie', db.Integer, primary_key=True)
    name = db.Column('c00', db.Text)
    description = db.Column('c01', db.Text)
    year = db.Column('c07', db.Text)
    imdb_id = db.Column('c09', db.Text)
    orig_name = db.Column('c16', db.Text)
    thumb = db.Column('c08', db.Text)

    def __repr__(self):
        return '<Movie %r>' % self.name

    @property
    def serialize(self):
        return dict((col, getattr(self, col)) for col in ('id', 'name', 'description', 'year', 'imdb_id', 'orig_name', 'thumb'))

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False, index=True)
    movie_id = db.Column(db.Integer, nullable=False)
    event = db.relationship("Event", backref=db.backref('votes', cascade='all, delete-orphan'))
    user = db.relationship("User", backref=db.backref('votes', cascade='all, delete-orphan'))

    def __repr__(self):
        return '<Vote of %r for %r at %r>' % (self.user.name, self.movie.name, self.event.date.strftime("%Y-%m-%d %H:%M:%S"))

Vote.movie = db.relationship(
    "Movie",
    primaryjoin="Movie.id==Vote.movie_id",
    foreign_keys=[Vote.movie_id],
    backref=db.backref("votes", cascade='all, delete-orphan')
)
