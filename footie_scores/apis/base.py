''' Interfaces to football score APIs '''

import json
import logging
import datetime as dt

import requests

from footie_scores import db
from footie_scores.utils.exceptions import *
from footie_scores.db import date_format
from footie_scores.db.interface import save_fixture_dicts_to_db, save_competitions_to_db
from footie_scores.utils.strings import correct_unicode_to_bin


logger = logging.getLogger(__name__)


DEFAULT_COMMENTARY = {
    'lineup': {
        'visitorteam': [],
        'localteam': []}
}

class FootballAPICaller(object):
    '''
    Base class for classes which call specific football score APIs.

    Implements generic calls. Should not be instantiated.
    '''


    def __init__(self):
        self.id_league = None
        self.base_url = None
        self.headers = None
        self.url_suffix = ""
        self.match_page_ready_map = None
        self.api_date_format = None
        self.api_time_format = None
        self.db_date_format =  db.date_format
        self.db_time_format = db.time_format

    def request(self, url, correct_unicode=False):
        logger.info('Making request to %s', self.base_url + url)
        request_url = self.base_url + url + self.url_suffix
        raw_response = requests.get(request_url, headers=self.headers)
        if correct_unicode:
            response = json.loads(correct_unicode_to_bin(raw_response.content))
        else:
            response = raw_response.json()
        assert self._is_valid_response(response), "Error in request to %s\nResponse: %s" %(
            request_url, response)
        return response

    def todays_fixtures_to_db(self, competitions):
        fixtures = self._todays_fixtures(competitions)
        save_fixture_dicts_to_db(fixtures)

    def competitions_to_db(self):
        competitions = self.get_competitions()
        save_competitions_to_db(competitions)

    def page_ready_fixture_details(self, fixture_id):
        return self._get_commentary_for_fixture(fixture_id)

    def get_competitions(self):
        raise NotImplementedError(
            "Implemented in child classes - base class should not be instantiated")

    def _todays_fixtures(self, competitions):
        fixtures = self._get_fixtures_for_date(dt.date.today(), competitions)
        # from datetime import timedelta
        # yesterday = date.today() - timedelta(days=1)
        # fixtures = self._get_fixtures_for_date(yesterday, competitions)
        return self._make_fixtures_db_ready(fixtures)

    def _make_date_db_ready(self, sdate):
        dt_obj = dt.datetime.strptime(sdate, self.db_date_format).date()
        return dt.datetime.strftime(dt_obj, self.db_date_format)

    def _make_time_db_ready(self, stime):
        dt_obj = dt.datetime.strptime(stime, self.db_time_format).time()
        return dt.time.strftime(dt_obj, self.db_time_format)

    def _filter_by_competition(self, competitions):
        raise NotImplementedError(
            "Implemented in child classes - base class should not be instantiated")

    def _get_fixtures_for_date(self, *args):
        raise NotImplementedError(
            "Implemented in child classes - base class should not be instantiated")

    def _get_commentary_for_fixture(self, *args):
        raise NotImplementedError(
            "Implemented in child classes - base class should not be instantiated")

    def _make_fixtures_page_ready(self, *args):
        raise NotImplementedError(
            "Implemented in child classes - base class should not be instantiated")

    def _make_fixtures_db_ready(self, *args):
        raise NotImplementedError(
            "Implemented in child classes - base class should not be instantiated")

    def _is_valid_response(self, *args):
        raise NotImplementedError(
            "Implemented in child classes - base class should not be instantiated")
