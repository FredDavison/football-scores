#!/usr/bin/env python

'''
Contains logic for indefinitely updating active fixtures
'''

import time
import logging
import datetime as dt

from footie_scores import db, settings, utils
from footie_scores.db import maintenance
from footie_scores.utils.time import chop_microseconds
from footie_scores.interfaces import api_to_db
from footie_scores.utils.log import start_logging, log_list
from footie_scores.apis.football_api import FootballAPI


logger = logging.getLogger(__name__)


def log_time_util_next_fixture(tdelta, sleeptime):
    logger.info('Next game in: %s (UTC time now %s)',
                chop_microseconds(dt.timedelta(seconds=tdelta)),
                dt.datetime.strftime(utils.time.now(), settings.DB_TIMEFORMAT))
    logger.info('Sleeping for: %s', chop_microseconds(dt.timedelta(seconds=sleeptime)))


def lineup_check_gen():
    last_request = (utils.time.now()
                    - dt.timedelta(seconds=settings.LINEUP_CHECK_COOLDOWN + 1))
    while True:
        seconds_elapsed = (utils.time.now() - last_request).total_seconds()
        if seconds_elapsed > settings.LINEUP_CHECK_COOLDOWN:
            last_request = utils.time.now()
            yield True
        else:
            yield False


LINEUP_CHECK = lineup_check_gen()
def lineup_requests_due():
    return next(LINEUP_CHECK)


def start_updater():
    next_state = _StartupState
    while True:
        state = next_state()
        next_state = state.run()


class _UpdaterState():
    '''
    Base class for the various state objects used to monitor whether
    fixtures are active and update them if so.
    '''
    def __init__(self):
        self.api = FootballAPI()
        logger.info('%s initialised', self.__class__.__name__)

    def run(self):
        raise NotImplementedError

    def update_fixtures_lineups(self, session, fixtures):
        needs_lineups = [f for f in fixtures if not f.has_lineups()]
        if not lineup_requests_due():
            logger.info('Lineups not requested due to cooldown timer')
            return
        if needs_lineups:
            log_list(needs_lineups, logger, '{} fixtures kicking off soon do not have complete lineups:'.format(len(needs_lineups)))
            fixture_ids = [f.api_fixture_id for f in needs_lineups]
            lineups = self.api.get_lineups_for_fixtures(fixture_ids)
            api_to_db.save_lineups(session, lineups)

    def refresh_and_get_todays_fixtures(self, session):
        todays_api_fixtures = self.api.todays_fixtures(settings.COMPS)
        api_to_db.save_fixtures(session, *todays_api_fixtures)
        todays_fixtures = db.queries.get_fixtures_by_date(session, utils.time.today())
        return todays_fixtures

    def time_to_next_kickoff(self, fixtures):
        times_to_kickoff = [f.time_to_kickoff() for f in fixtures]
        return sorted(times_to_kickoff)[0]


class _StartupState(_UpdaterState):
    '''
    Startup state which initialises the state machine by checking
    today's fixtures and determining whether active or idle state
    should be entered.
    '''

    def run(self):
        with db.session_scope() as session:
            fixtures_today = self.refresh_and_get_todays_fixtures(session)
            fixtures_active = [f for f in fixtures_today if f.is_active()]
            fixtures_soon = [f for f in fixtures_today if f.kicks_off_within(settings.PRE_GAME_PREP_PERIOD)]
            logger.info('%d fixtures today, %d active, %d in prep state (KO within %.0f minutes)',
                        len(fixtures_today), len(fixtures_active), len(fixtures_soon), settings.PRE_GAME_PREP_PERIOD / 60)
        if fixtures_active or fixtures_soon:
            return _ActiveState
        else:
            return _MaintenanceState


class _IdleState(_UpdaterState):
    ''' Checks when next game kicks off and sleeps until closer to then '''

    def run(self):
        with db.session_scope() as session:
            fixtures_today = db.queries.get_fixtures_by_date(session, utils.time.today())
            future_fixtures = [f for f in fixtures_today if f.status != 'FT']
            if not future_fixtures:
                logger.info('No games today, sleeping for %d seconds (time is %s)',
                            settings.NO_GAMES_SLEEP, utils.time.now())
                time.sleep(settings.NO_GAMES_SLEEP)
                logger.info('Awoken')
                return _IdleState
            else:
                log_list(fixtures_today, logger, intro='Todays fixtures:')
                time_to_next_game = self.time_to_next_kickoff(future_fixtures)
                if time_to_next_game < settings.PRE_GAME_ACTIVE_PERIOD:
                    return _ActiveState
                elif time_to_next_game < settings.PRE_GAME_PREP_PERIOD:
                    return _PreparationState
                else:
                    sleeptime = time_to_next_game - settings.PRE_GAME_PREP_PERIOD
                    log_time_util_next_fixture(time_to_next_game, sleeptime)
                    time.sleep(sleeptime)
                    return _PreparationState


class _PreparationState(_UpdaterState):
    ''' Try and get lineups in the period leading up to kick-offs '''

    def run(self):
        active_fixtures = False
        with db.session_scope() as session:
            fixtures_today = self.refresh_and_get_todays_fixtures(session)
            while not active_fixtures:
                active_fixtures = [f for f in fixtures_today if f.is_active()]
                fixtures_soon = [f for f in fixtures_today
                                 if f.kicks_off_within(settings.PRE_GAME_PREP_PERIOD)]
                needs_lineups = [f for f in fixtures_soon if not f.has_lineups()]
                if needs_lineups:
                    self.update_fixtures_lineups(session, needs_lineups)
                    logger.info('Prep state pausing for %d seconds', settings.PREP_STATE_PAUSE)
                    time.sleep(settings.PREP_STATE_PAUSE)
                else:
                    time_to_next_game = self.time_to_next_kickoff(fixtures_soon)
                    log_time_util_next_fixture(time_to_next_game, time_to_next_game)
                    time.sleep(time_to_next_game)
                    return _ActiveState
        return _ActiveState


class _ActiveState(_UpdaterState):
    ''' Update fixture scores periodically when games are ongoing'''

    def run(self):
        active_fixtures, needs_lineups = True, True
        while active_fixtures or needs_lineups:
            with db.session_scope() as session:
                fixtures = self.refresh_and_get_todays_fixtures(session)
                active_fixtures = [f for f in fixtures if f.is_active()]
                fixtures_soon = [f for f in fixtures
                                 if f.kicks_off_within(settings.PRE_GAME_PREP_PERIOD)]
                needs_lineups = [f for f in fixtures_soon + active_fixtures
                                 if not f.has_lineups()]
                if needs_lineups:
                    self.update_fixtures_lineups(session, needs_lineups)
            logger.info('Active state pausing for %d seconds', settings.ACTIVE_STATE_PAUSE)
            time.sleep(settings.ACTIVE_STATE_PAUSE)
        return _IdleState


class _MaintenanceState(_UpdaterState):
    '''Perform maintenance on the database during idle hours'''

    def run(self):
        maintenance.update_all_fixtures()
        return _IdleState
