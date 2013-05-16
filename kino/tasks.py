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

def calendar_events(url, event_name, timerange):
    "Get events named event_name from the calendar file at url in the specified timerange"
    events = []
    fd = urlopen(url)
    cal = vobject.readComponents(fd.read())
    for component in cal:
        if component.name == "VCALENDAR":
            for event in component.components():
                if event.name == 'VEVENT' and event.summary.value == event_name:
                    try:
                        description = event.description.value
                    except AttributeError:
                        description = None
                    if event.rruleset:
                        for date in event.rruleset.between(
                                *(time.replace(tzinfo=event.dtstart.value.tzinfo) for time in timerange)
                            ):
                            events.append(Event(date=date.replace(tzinfo=None), comment=description))
                    elif timerange[0] <= event.dtstart.value.replace(tzinfo=None) <= timerange[1]:
                        events.append(Event(date=event.dtstart.value.replace(tzinfo=None), comment=description))
    return events

@manager.command
def update_events():
    "Fetches new events from the calendar and marks canceled ones as canceled"
    timerange = (datetime.now(), datetime.now() + timedelta(days=app.config['CALENDAR_FUTURE']))
    calevents = calendar_events(app.config['CALENDAR_URL'], app.config['CALENDAR_EVENT_NAME'], timerange)
    caldates = dict((event.date, event) for event in calevents)
    dbevents = Event.query.filter(Event.date.between(*timerange))
    for event in dbevents:
        if event.date in caldates:
            # we already know about this event, and nothing changed
            calevents.remove(caldates[event.date])
        else:
            event.canceled = True
            db.session.add(event)
    # we don't have the remaining elements in the database, so add them!
    for event in calevents:
        db.session.add(event)
    db.session.commit()

@manager.command
def purge_events(days=7, verbose=False):
    "Deletes events older than specified amount of days"
    days = int(days)
    events = Event.query.filter(Event.date <= datetime.now() - timedelta(days=days))
    for event in events:
        db.session.delete(event)
    num = events.count()
    db.session.commit()

    print '%d event%s purged' % (num, '' if num == 1 else 's')

@manager.command
def write_mails():
    "Writes mails about new and canceled events"
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
