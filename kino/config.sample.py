SQLALCHEMY_DATABASE_URI = 'sqlite://test.db'
SQLALCHEMY_BINDS = {'xbmc': 'mysql://user:password@localhost/MyVideos75'}

SERVER_NAME = 'example.org'
APPLICATION_ROOT = '/'
LOGGING_PATH = '/tmp/kino.log'

CALENDAR_URL = 'http://example.org/caldav/path/to/calendar/?export'
CALENDAR_FUTURE = 21 # number of days events are imported in advance
CALENDAR_EVENT_NAME = 'Filmtheater' # name of events to look for

EMAIL_RECIPIENTS = ['mailinglist@example.org', 'individual@example.org']
EMAIL_FUTURE = 7

MAIL_SERVER = 'smtp.example.org'
MAIL_USE_TLS = True
MAIL_USERNAME = 'username'
MAIL_PASSWORD = 'password'
DEFAULT_MAIL_SENDER = ('Mailinglist', 'mailinglist@example.org')
