import json, os

from footie_scores import settings
from footie_scores.apis.football_data import FootballData
from footie_scores.apis.football_api import FootballAPI


def load_football_api_comps():
    with open(os.path.join(
            'data', 'football_api_competitions.json'), 'r') as cjson:
        fa_comps = json.loads(cjson.read())
    return fa_comps


def load_football_data_comps():
    with open(os.path.join(
            'data', 'football_data_competitions.json'), 'r') as cjson:
        fd_comps = json.loads(cjson.read())
    return fd_comps


def api_get_football_api_comps(comps=settings.COMPS):
    fa = FootballAPI()
    return fa.get_competitions(source_competitions=comps)


def api_get_football_data_comps(comps=settings.COMPS):
    fd = FootballData()
    return fd.get_competitions(source_competitions=comps)
