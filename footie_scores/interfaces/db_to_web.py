
import datetime as dt
from collections import defaultdict
import logging

from sqlalchemy import and_

from footie_scores import settings
from footie_scores import utils
from footie_scores.db import queries
from footie_scores.db.schema import Competition, Fixture


logger = logging.getLogger(__name__)
TIME_OVERRIDE = settings.OVERRIDE_TIME or settings.OVERRIDE_DAY


def get_comp_grouped_fixtures(
        session, start_date, comp_ids=settings.COMPS, end_date=None):

    grouped_fixtures = []
    end_date = start_date if end_date is None else end_date
    for id_ in comp_ids:
        competition = queries.get_competition_by_id(session, id_)
        fixtures = queries.get_fixtures_by_date_and_comp(session, start_date, id_, end_date)
        if TIME_OVERRIDE:
            fixtures = filter_events_by_time(fixtures)
        grouped_fixtures.append({'name': competition.name,
                                 'fixtures': fixtures})
    return grouped_fixtures


def get_date_grouped_fixtures(
        session, start_date, comp_id, end_date=None):

    grouped_fixtures = []
    date_keyed_dict = defaultdict(list)
    end_date = start_date if end_date is None else end_date

    fixtures = queries.get_fixtures_by_date_and_comp(session, start_date, comp_id, end_date)
    if TIME_OVERRIDE:
        fixtures = filter_events_by_time(fixtures)
    for fixture in fixtures:
        date_keyed_dict[fixture.date].append(fixture)

    for date, fixtures in date_keyed_dict.items():
        web_format_time = utils.time.custom_strftime(settings.WEB_DATEFORMAT, date)
        grouped_fixtures.append({'name': web_format_time,
                                 'fixtures': fixtures})

    return grouped_fixtures


def get_competitions_by_id(session, ids):
    return queries.get_competitions_by_id(session, ids)


def get_competition_by_id(session, id_):
    return queries.get_competition_by_id(session, id_)


def filter_events_by_time(fixtures):
    now = utils.time.now()
    for f in fixtures:
        time_filtered_events = {'home': [], 'away': []}
        for team in ('home', 'away'):
            for e in f.events[team]:
                event_real_time = dt.datetime.strptime(e['real_time'], settings.DB_DATETIMEFORMAT)
                if now > event_real_time:
                    time_filtered_events[team].append(e)
                else:
                    logger.info('%s vs %s: %s at %s filtered',
                                f.team_home, f.team_away, e['type'], e['real_time'])
        f.events = time_filtered_events
    return fixtures
