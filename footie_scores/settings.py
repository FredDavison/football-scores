import os
import logging
import datetime as dt

from footie_scores import constants

logger = logging.getLogger(__name__)

DB_PATH = os.environ['DATABASE_URL']
SQLA_ECHO = False
DB_DATEFORMAT = '%d.%m.%Y'
DB_TIMEFORMAT = '%H:%M'
DB_DATETIMEFORMAT = DB_DATEFORMAT + '-' + DB_TIMEFORMAT

START_TIME = dt.datetime.now()
# OVERRIDE_DAY = None
# OVERRIDE_TIME = None
OVERRIDE_DAY = dt.date(2017, 8, 6)
OVERRIDE_TIME = dt.time(19, 5, 00)

WEB_DATEFORMAT =  "%A %d %B, %Y" # e.g. Sun 16 April '17
WEB_DATEFORMAT_SHORT =  "%A %d %B" # e.g. Sun 16 April '17
WEB_TIMEFORMAT = None
FLASK_DEBUG = True

COMPS = constants.MAJOR_COMPS # ALL_COMPS, MOST_COMPS, MAJOR_COMPS, LIMITED_COMPS

ACTIVE_STATE_PAUSE = 20
PREP_STATE_PAUSE = 10
NO_GAMES_SLEEP = 10800
PRE_GAME_PREP_PERIOD = 3600
PRE_GAME_ACTIVE_PERIOD = 600
