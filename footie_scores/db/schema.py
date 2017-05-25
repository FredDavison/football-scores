import json
import logging
import sqlalchemy as sqla
from sqlalchemy.ext.declarative import declarative_base

from footie_scores import db


logger = logging.getLogger(__name__)
Base = declarative_base()


class _JsonEncodedDict(sqla.TypeDecorator):
    impl = sqla.String

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)


# class FixtureEvents(Base):
#     __tablename__ = 'events'

#     id = sqla.Column(sqla.Integer, primary_key=True)
#     fixture_id = sqla.Column(sqla.String, sqla.ForeignKey('fixtures.id'))

#     fixture = relationship('Fixture', back_populates='events')

class Updatable():
    def __init__(self):
        self.atts_to_update = []

    def update_from_equivalent(self, equivalent):
        for name in self.atts_to_update:
            setattr(self, name, getattr(equivalent, name))


class Competition(Base):
    __tablename__ = 'competitions'

    id = sqla.Column(sqla.Integer, primary_key=True)
    api_id = sqla.Column(sqla.String)
    name = sqla.Column(sqla.String)
    region = sqla.Column(sqla.String)
    fixtures = sqla.orm.relationship('Fixture', back_populates='competition')

    def __init__(self, api_id, name, region):
        self.api_id = api_id
        self.name = name
        self.region = region
        self.print_name = None

    def __repr__(self):
        return "<Competition(%s %s (api id %s) (db id %s))>" %(
            self.region, self.name, self.api_id, self.id)

class Lineups(Base, Updatable):
    # TODO make name singular
    __tablename__ = 'lineups'

    id = sqla.Column(sqla.Integer, primary_key=True)
    api_fixture_id = sqla.Column(sqla.String)
    home = sqla.Column(_JsonEncodedDict)
    away = sqla.Column(_JsonEncodedDict)

    fixture_id = sqla.Column(sqla.Integer, sqla.ForeignKey('fixtures.id'))
    fixture = sqla.orm.relationship('Fixture', back_populates='lineups')

    atts_to_update = ('home', 'away')

    def __init__(self, api_fixture_id, home_lineup, away_lineup):
        self.api_fixture_id = api_fixture_id
        self.home = home_lineup
        self.away = away_lineup

    def __repr__(self):
        return "<Lineups(for match id %s)>" %self.api_fixture_id


class Fixture(Base, Updatable):
    # TODO lineups, players, events can be stored as own table
    __tablename__ = 'fixtures'

    id = sqla.Column(sqla.Integer, primary_key=True)
    date = sqla.Column(sqla.String)
    time = sqla.Column(sqla.String)
    team_home = sqla.Column(sqla.String)
    team_away = sqla.Column(sqla.String)
    score = sqla.Column(sqla.String)
    comp_api_id = sqla.Column(sqla.String)
    api_fixture_id = sqla.Column(sqla.String)
    events = sqla.Column(_JsonEncodedDict)

    lineups = sqla.orm.relationship('Lineups', uselist=False, back_populates='fixture')

    competition_id = sqla.Column(sqla.Integer, sqla.ForeignKey('competitions.id'))
    competition = sqla.orm.relationship(
        'Competition',
        back_populates='fixtures')

    atts_to_update = ('score', 'events', 'lineups')

    def __init__(
            self, team_home, team_away, comp_api_id, api_fixture_id,
            score, date, time, events=None):

        self.team_home = team_home
        self.team_away = team_away
        self.comp_api_id = comp_api_id
        self.api_fixture_id = api_fixture_id
        self.score = score
        self.date = date
        self.time = time
        if events:
            self.events = events

        self.date_format = db.date_format
        self.time_format = db.time_format


    def __repr__(self):
        return "<Fixture(%s vs %s on %s at %s)>" %(
            self.team_home, self.team_away, self.date, self.time)


def create_tables_if_not_present():
    if not db.engine.table_names() == ['fixtures', 'competitions']:
        Base.metadata.create_all(db.engine)


def drop_tables():
    Base.metadata.drop_all(db.engine)


def drop_table(table):
    table.__table__.drop(db.engine)
