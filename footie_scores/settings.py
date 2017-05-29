import datetime as dt

from footie_scores import constants

DB_PATH = None
SQLA_ECHO = False

DB_DATEFORMAT = '%d.%m.%Y'
DB_TIMEFORMAT = '%H:%M'
DB_DATETIMEFORMAT = DB_DATEFORMAT + '-' + DB_TIMEFORMAT

OVERRIDE_DAY = dt.date(2017, 5, 28)
OVERRIDE_TIME = dt.time(16, 58, 00)

WEB_DATEFORMAT =  "%A %d %B %y" # e.g. Sunday 16 April 2017
WEB_TIMEFORMAT = None

COMPS = constants.MAJOR_COMPS # ALL_COMPS, MOST_COMPS, MAJOR_COMPS, LIMITED_COMPS

ACTIVE_STATE_PAUSE = 5
PREP_STATE_PAUSE = 5
