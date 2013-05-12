from flask import render_template
from flask.ext.script import Manager
from flask.ext.mail import Mail, Message
import vobject
from datetime import datetime, timedelta
from urllib import urlopen

from . import app
from .model import *

manager = Manager(app)
mail = Mail(app)

def calendar_events(url, event_name, days_in_future):
    "Get events from the calendar file at url up to days_in_future days ahead"
    events = []
    fd = urlopen('test.ics')
    cal = vobject.readComponents(fd.read())
    for component in cal:
        if component.name == "VCALENDAR":
            for event in component.components():
                if event.name == 'VEVENT' and event.summary.value == event_name:
                    if event.rruleset:
                        events.extend(event.rruleset.between(
                            datetime.now(event.dtstart.value.tzinfo),
                            datetime.now(event.dtstart.value.tzinfo) + timedelta(days=days_in_future)
                        ))
                    else:
                        events.append(event.dtstart.value)
    return [event.replace(tzinfo=None) for event in events]

@manager.command
def update_events():
    days_in_future = app.config['CALENDAR_FUTURE']
    calevents = calendar_events(
        app.config['CALENDAR_URL'],
        app.config['CALENDAR_EVENT_NAME'],
        days_in_future
    )
    dbevents = Event.query.filter(Event.date.between(
        datetime.now(), datetime.now() + timedelta(days=days_in_future)
    ))
    for event in dbevents:
        if event.date in calevents:
            # we already know about this event, and nothing changed
            calevents.remove(event.date)
        else:
            event.canceled = True
            db.session.add(event)

    # we don't have the remaining elements in the database, so add them!
    for event in calevents:
        db.session.add(Event(date=event.replace(tzinfo=None)))
    db.session.commit()

@manager.command
def write_mails():
    app.jinja_env.trim_blocks = True
    days = app.config['EMAIL_FUTURE']
    new_events = Event.query.filter_by(mailed=False, canceled=False).filter(
        Event.date.between(datetime.now(), datetime.now() + timedelta(days=days)))
    canceled_events = Event.query.filter_by(mailed=True, canceled=True)
    if new_events.count() > 0 or canceled_events.count() > 0:
        msg = Message(
            subject=render_template('mail_subject.txt', new=new_events.count(), canceled=canceled_events.count()),
            sender=app.config['DEFAULT_MAIL_SENDER'],
            recipients=app.config['EMAIL_RECIPIENTS'],
            body=render_template('mail.txt', new_events=new_events, canceled_events=canceled_events)
        )
        mail.send(msg)

        for event in new_events:
            event.mailed = True
            db.session.add(event)
        for event in canceled_events:
            event.mailed = False
            db.session.add(event)
        db.session.commit()
