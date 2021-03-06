#!/usr/bin/env python

''' Runs the web app '''

from multiprocessing import Process

from footie_scores import db, settings
from footie_scores.utils.log import start_logging
from footie_scores.webapp.run import app
from footie_scores.engine import updating


def main():
    ''' Start web app and scores updater '''
    web_app = Process(target=app.run, kwargs={'debug': settings.FLASK_DEBUG})
    api_caller = Process(target=updating.start_updater, args=())
    web_app.start()
    api_caller.start()


if __name__ == '__main__':
    start_logging()
    main()
