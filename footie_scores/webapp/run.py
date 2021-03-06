#!/usr/bin/env python

''' Make webpage from API requests '''

import logging
import datetime as dt

from flask import Flask, render_template, jsonify

from footie_scores import settings, constants, db, utils
from footie_scores.utils.log import start_logging
from footie_scores.utils.time import month_list_define_first, month_list_define_last
from footie_scores.interfaces import db_to_web


logger = logging.getLogger(__name__)
app = Flask(__name__)


COMPS_FOR_PAGE = settings.COMPS
TODAY = utils.time.today()
THIS_YEAR = TODAY.year
MONTHS = constants.MONTHS
SHORT_MONTHS = constants.SHORT_MONTHS


class ResponseTracker():
    def __init__(self):
        self.previous = 'dummy'
    def is_different_to_last(self, current):
        previous = self.previous
        self.previous = current
        response_differs = current != previous
        logger.info('ResponseTracker: current response differs to last? %s', response_differs)
        return response_differs


response_tracker = ResponseTracker()

@app.route("/json/fixture_updates")
def fixture_updates():
    today = utils.time.today()
    with db.session_scope() as session:
        fixtures = db_to_web.get_fixtures_by_dates_and_comps(
            session, today, COMPS_FOR_PAGE)
        id_keyed_fixtures = {fixture.api_fixture_id: fixture.to_python() for fixture in fixtures}
    return jsonify(id_keyed_fixtures)
    

@app.route("/todays_games")
def todays_fixtures():
    today = utils.time.today()
    with db.session_scope() as session:
        all_comps = db_to_web.get_competitions_by_id(session, COMPS_FOR_PAGE)
        fixtures = db_to_web.get_comp_grouped_fixtures(session, today, COMPS_FOR_PAGE)
        comps_with_games = [f['name'] for f in fixtures if f['fixtures']]
        web_date = utils.time.custom_strftime(settings.WEB_DATEFORMAT_SHORT, today)
        todays_games = games_template(
            'scores.html',
            'scores',
            all_comps,
            fixtures,
            utils.time.today(),
            'Live Scores - ' + web_date,
            competitions_with_games_today=comps_with_games,
        )
    return todays_games


@app.route("/past_results_<comp_id>_<month_index>")
def past_results(comp_id, month_index=TODAY.month):
    comp_ids = settings.COMPS if comp_id == 'all' else [comp_id] 

    start_day = dt.date(year=THIS_YEAR, month=int(month_index), day=1)
    end_day = (dt.date(year=THIS_YEAR, month=int(month_index) % 12 + 1, day=1)
               - dt.timedelta(days=1))

    today = utils.time.today()
    with db.session_scope() as session:
        fixtures_today = db_to_web.get_comp_grouped_fixtures(session, today, COMPS_FOR_PAGE)
        comps_with_games = [f['name'] for f in fixtures_today if f['fixtures']]
        all_comps = db_to_web.get_competitions_by_id(session, COMPS_FOR_PAGE)
        fixtures = db_to_web.get_date_grouped_fixtures(session,
                                                       start_day,
                                                       comp_ids,
                                                       end_day)
        if comp_id == 'all':
            selected_comp = 'All Competitions'
        else:
            selected_comp = db_to_web.get_competition_by_id(session, int(comp_id)).name

        past_games = games_template(
            'fixtures_results.html',
            'results',
            all_comps,
            fixtures,
            utils.time.today(),
            selected_comp + ' - Results / Fixtures',
            comp_id,
            comps_with_games)
    return past_games


@app.route("/fixtures_<comp_id>")
def future_fixtures(comp_id):
    comp_ids = settings.COMPS if comp_id == 'all' else [comp_id]
    today = utils.time.today()
    start_day = (dt.date(year=THIS_YEAR, month=today.month % 12, day=today.day)
                 + dt.timedelta(days=1))
    end_day = (dt.date(year=THIS_YEAR, month=today.month % 12, day=today.day)
               + dt.timedelta(days=31))

    with db.session_scope() as session:
        fixtures_today = db_to_web.get_comp_grouped_fixtures(session, today, COMPS_FOR_PAGE)
        comps_with_games = [f['name'] for f in fixtures_today if f['fixtures']]
        all_comps = db_to_web.get_competitions_by_id(session, COMPS_FOR_PAGE)
        fixtures = db_to_web.get_date_grouped_fixtures(session,
                                                       start_day,
                                                       comp_ids, end_day)
        if comp_id == 'all':
            selected_comp = 'All Competitions'
        else:
            selected_comp = db_to_web.get_competition_by_id(session, int(comp_id)).name

        future_games = games_template(
            'fixtures_results.html',
            'fixtures',
            all_comps,
            fixtures,
            utils.time.today(),
            selected_comp + ' - Results / Fixtures',
            comp_id,
            comps_with_games)
    return future_games


@app.route("/details_<fixture_id>")
def match_details(fixture_id):
    today = utils.time.today()
    with db.session_scope() as session:
        all_comps = db_to_web.get_competitions_by_id(session, COMPS_FOR_PAGE)
        fixture = db_to_web.get_fixture_by_id(session, fixture_id)
        grouped_fixtures = [{'name': fixture.competition.name, 'fixtures': (fixture,)},]
        comps_with_games = [f['name'] for f in grouped_fixtures if f['fixtures']]
        web_date = utils.time.custom_strftime(settings.WEB_DATEFORMAT_SHORT, today)
        fixture.lineups = db_to_web.determine_substitutions(fixture.lineups, fixture.events)
        todays_games_with_details = games_template(
            'details.html',
            'details',
            all_comps,
            grouped_fixtures,
            utils.time.today(),
            'Live Scores - ' + web_date,
            competitions_with_games_today=comps_with_games,
        )
    return todays_games_with_details 


def games_template(
        template, page, page_competitions, grouped_fixtures, date_,
        title, comp_id='', competitions_with_games_today=None):

    today = utils.time.today()
    options = {
        'results': {
            'display_todays_games_sublist': 'none',
            'display_results_sublist': 'block',
            'display_fixtures_sublist': 'none',
            'games_today_filter': False,
            'games_today_link': True,
            'months': month_list_define_last(today.month),
            'short_months': month_list_define_last(today.month, month_list=SHORT_MONTHS),
            'display_lineups': False,
            'first_month': today.month+1%12,
        },
        'fixtures': {
            'display_todays_games_sublist': 'none',
            'display_results_sublist': 'none',
            'display_fixtures_sublist': 'block',
            'games_today_filter': False,
            'games_today_link': True,
            'months': month_list_define_first(today.month),
            'short_months': month_list_define_first(TODAY.month, month_list=SHORT_MONTHS),
            'display_lineups': False,
            'first_month': today.month,
        },
        'scores': {
            'display_todays_games_sublist': 'block',
            'display_results_sublist': 'none',
            'display_fixtures_sublist': 'none',
            'games_today_filter': True,
            'games_today_link': False,
            'months': None,
            'short_months': None,
            'display_lineups': False,
            'first_month': None,
        },
        'details': {
            'display_todays_games_sublist': 'block',
            'display_results_sublist': 'none',
            'display_fixtures_sublist': 'none',
            'games_today_filter': False,
            'games_today_link': True,
            'months': None,
            'short_months': None,
            'display_lineups': True,
            'first_month': None,
        }
    }

    display_todays_games_sublist = options[page]['display_todays_games_sublist']
    display_results_sublist = options[page]['display_results_sublist']
    display_fixtures_sublist = options[page]['display_fixtures_sublist']
    games_today_filter = options[page]['games_today_filter']
    games_today_link = options[page]['games_today_link']
    months = options[page]['months']
    short_months = options[page]['short_months']
    display_lineups = options[page]['display_lineups']
    first_month = options[page]['first_month']

    return render_template(
        template,
        title=title,
        date=date_.strftime(settings.WEB_DATEFORMAT),
        competitions=page_competitions,
        competitions_with_games=competitions_with_games_today,
        grouped_fixtures=grouped_fixtures,
        comp_id=comp_id,
        games_today_filter=games_today_filter,
        games_today_link=games_today_link,
        todays_games_sublist_display=display_todays_games_sublist,
        past_results_sublist_display=display_results_sublist,
        future_fixtures_sublist_display=display_fixtures_sublist,
        months=months,
        short_months=short_months,
        time=utils.time.now().strftime(settings.DB_DATETIMEFORMAT),
        display_lineups=display_lineups,
        first_month=first_month,
    )


if __name__ == '__main__':
    start_logging()
    app.run(debug=settings.FLASK_DEBUG)
