'''
Takes data returned by FootballAPICaller derived objects,
converts to db objects and adds them to the db.

Should be the single link between API and db.
'''

import logging

from footie_scores import db
from footie_scores.apis import response_merges
from footie_scores.maps import competition_map
from footie_scores.apis.football_api import FootballAPI
from footie_scores.apis.football_data import FootballData
from footie_scores.db.schema import Fixture, Competition, Lineups, Team
from footie_scores.db.queries import row_exists, check_rows_in_db
from footie_scores.utils.log import log_list

logger = logging.getLogger(__name__)


def save_fixtures(session, *api_fixtures):
    fixture_map = {fix['api_fixture_id']: db.schema.Fixture(**fix)
                   for fix in api_fixtures}
    fixture_ids = fixture_map.keys()

    logger.info('Checking if fixtures already in db')
    fixtures_in_db = check_rows_in_db(session,
                                      row_type=Fixture,
                                      row_key=Fixture.api_fixture_id,
                                      match_keys=fixture_ids)
    missing_ids = set(fixture_ids).difference([f.api_fixture_id for f in fixtures_in_db])
    missing_fixtures = [fixture_map[id_] for id_ in missing_ids]

    cq = session.query(Competition)
    for fixture in missing_fixtures:
        fixture.competition = cq.filter(Competition.api_id == fixture.comp_api_id).one()
    session.bulk_save_objects(missing_fixtures)
    log_list(missing_fixtures, logger, template='%s added to db')

    for db_fixture in fixtures_in_db:
        api_fixture = fixture_map[db_fixture.api_fixture_id]
        if db_fixture.update_from_equivalent(api_fixture):
            logger.info('%s updated in db', api_fixture)
        else:
            logger.info('%s already up to date in db', api_fixture)


def save_lineups(session, api_lineups):
    fq = session.query(Fixture)
    for api_lineup in api_lineups:
        db_lineup = Lineups(**api_lineup)
        fixture = fq.filter(Fixture.api_fixture_id == db_lineup.api_fixture_id).one()
        if fixture.lineups is None:
            fixture.lineups = db_lineup
            logger.info('%s added to db', db_lineup.api_fixture_id)
        else:
            fixture.lineups.update_from_equivalent(db_lineup)


def save_competitions():
    fapi_comps = FootballAPI().get_competitions()
    fdata_comps = FootballData().get_competitions()
    competitions = response_merges.merge_two_lists(
        fapi_comps,
        fdata_comps,
        id_map=competition_map['football-api_to_football-data'],
        consistent_keys=True)
    with db.session_scope() as session:
        for comp in competitions:
            if not row_exists(session, Competition, Competition.api_id, comp['api_id']):
                db_comp = Competition(**comp)
                session.add(db_comp)


def save_teams():
    api = FootballData()
    api_teams = api.get_competition_teams()
    with db.session_scope() as session:
        for team in api_teams:
            db_team = Team(**team)
            session.add(db_team)
            print('{} saved in db'.format(team['team_name']))
