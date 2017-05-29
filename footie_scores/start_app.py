''' Runs the web app '''

from multiprocessing import Process

from footie_scores import db, settings
from footie_scores.utils.log import start_logging
from footie_scores.app.run import app
from footie_scores import league_manager


def main():
    ''' Start web app and scores updater '''
    start_logging()
    web_app = Process(target=app.run, kwargs={'debug': settings.FLASK_DEBUG})
    api_caller = Process(target=league_manager.main, args=())
    web_app.start()
    api_caller.start()

def start_web_app():
    start_logging()
    app.run(kwargs={'debug': settings.FLASK_DEBUG})


def start_api_caller():
    start_logging()
    league_manager.main()


if __name__ == '__main__':
    start_logging()
    main()
