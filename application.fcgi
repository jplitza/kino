#!/usr/bin/python
from flup.server.fcgi import WSGIServer
from kino import app
import sys
import logging

def excepthook(*exc_info):
    logging.critical('Unhandled exception:', exc_info=exc_info)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=app.config['LOGGING_PATH'],
        filemode='a')

    sys.excepthook = excepthook

    if len(sys.argv) > 1:
        WSGIServer(app, bindAddress=sys.argv[1]).run()
    else:
        WSGIServer(app).run()
