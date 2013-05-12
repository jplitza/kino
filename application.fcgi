#!/usr/bin/python
from flup.server.fcgi import WSGIServer
from kino import app
from sys import argv

if __name__ == '__main__':
    if len(argv) > 1:
        WSGIServer(app, bindAddress=argv[1])
    else:
        WSGIServer(app).run()
