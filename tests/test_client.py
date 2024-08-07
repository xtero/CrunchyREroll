import unittest
import sys
import os
import logging
from addondev.support import Repo, initializer, logger
logger.setLevel(logging.DEBUG)

Repo.repo = "matrix"
root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
source_path = os.path.join(root_path, 'plugin.video.crunchyreroll')
initializer(source_path)

# Need to be imported after modules modifications
# pylint: disable=E0401,C0413,C0411
from resources.lib.client import CrunchyrollClient # noqa = E402

if 'CRUNCHYROLL_EMAIL' not in os.environ:
    print("You need to defined CRUNCHYROLL_EMAIL to run tests", file=sys.stderr)
    sys.exit(1)
EMAIL = os.environ['CRUNCHYROLL_EMAIL']

if 'CRUNCHYROLL_PASSWORD' not in os.environ:
    print("You need to defined CRUNCHYROLL_PASSWORD to run tests", file=sys.stderr)
    sys.exit(1)
PASSWORD = os.environ['CRUNCHYROLL_PASSWORD']
SETTINGS = {
    "prefered_audio": "fr-FR",
    "prefered_subtitle": "fr-FR",
    "page_size": 20
}


class ClientTest(unittest.TestCase):

    def test_client_creation(self):
        CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)

    def test_get_watchlist(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        client.get_watchlist()
        client.get_watchlist(start=10)

    def test_search_anime(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        client.search_anime(query="my hero")
        client.search_anime(query="my hero", start=10)

    def test_get_history(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        client.get_history()
        client.get_history(page=2)

    def test_get_crunchylists(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        crunchylists = client.get_crunchylists()
        client.get_crunchylist(crunchylists[0]['list_id'])

    def test_get_one_episode(self):
        # Frieren
        series_id = "GG5H5XQX4"
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        seasons = client.get_series_seasons(series_id)
        episodes = client.get_season_episodes(seasons[0].id)
        client.get_stream_infos(episodes[0].id)

    def test_get_one_episode_no_version(self):
        # Gundam Narrative
        series_id = "G1XHJVWD3"
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        seasons = client.get_series_seasons(series_id)
        episodes = client.get_season_episodes(seasons[0].id)
        client.get_stream_infos(episodes[0].id)

    def test_get_one_episode_special_number(self):
        # My Hero Academia OVA2
        episode_id = "G0DUN1QQ0"
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        client.get_stream_infos(episode_id)
        # One Piece SP13
        episode_id = "GMKUXPGV1"
        client.get_stream_infos(episode_id)

    def test_playhead_manipulation(self):
        # SPY x FAMILY E34
        episode_id = "GD9UVQPXZ"
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        playheads = client.get_playhead([episode_id])
        if len(playheads['data']) == 0:
            playheads = {'data': [{"playhead": 0, "content_id": episode_id, "fully_watched": False}]}
        client.update_playhead(episode_id, playheads['data'][0]['playhead']+10)
        client.update_playhead(episode_id, playheads['data'][0]['playhead'])

    def test_alpha_browse(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        index = client.get_alpha()
        client.browse(sort_by="alphabetical", start=index[0]['start'], number=index[0]['number'])

    def test_get_popular(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        client.get_popular()
        client.get_popular(start=10)
        client.get_popular(categories=['action'])
        client.get_popular(categories=['action,fantasy'])

    def test_newly_added(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        client.get_newly_added()
        client.get_newly_added(start=10)
        client.get_newly_added(categories=['action'])
        client.get_newly_added(categories=['action,fantasy'])

    def test_get_categories(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        categories = client.get_categories()
        client.get_sub_categories(categories[0].id)

    def test_get_seasonal_tags(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        client.get_seasonal_tags()

    def test_switch_profile(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        profiles = client.get_multiprofile()
        client.auth.switch_profile(profiles[1].id)
        client.auth.switch_profile(profiles[0].id)

    def test_next_episode(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        # Gundam The Witch from Mercury
        first_episode = "GMKUX2G9E"
        last_episode = "GX9UQZ497"
        next_episode = client.get_next_episode(first_episode)
        assert next_episode is not None
        assert next_episode.id == "GVWU0E4N1"
        next_episode = client.get_next_episode(last_episode)
        assert next_episode is None

    def test_reauth_non_primary(self):
        client = CrunchyrollClient(EMAIL, PASSWORD, SETTINGS)
        profiles = client.get_multiprofile()
        profile_id = profiles[1].id
        client.auth.switch_profile(profile_id)
        client.auth.data['expires_in'] = -1
        client.get_watchlist()
        assert profile_id == client.auth.data['profile_id']
