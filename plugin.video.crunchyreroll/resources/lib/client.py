# -*- coding: utf-8 -*-
# ${LICENSE_HEADER}

import requests
from requests.exceptions import HTTPError
import xbmc
import urlquick
from . import auth, utils
from .model import Series, Season, Episode, Category, User


class CrunchyrollClient:

    def _log(self, msg):
        xbmc.log(f"[Crunchyroll-Client] {msg}")

    # pylint: disable=R0913
    def __init__(self, email, password, settings):
        self.auth = auth.CrunchyrollAuth(email, password)
        self.prefered_subtitle = settings['prefered_subtitle']
        self.prefered_audio = settings['prefered_audio']
        self.page_size = settings['page_size']

    # pylint: disable=W0102
    def _post(self, url, params={}, headers={}, data={}, json=False, authenticated=True):
        if authenticated:
            headers['User-Agent'] = self.auth.user_agent

        if json:
            response = requests.post(url, params=params, headers=headers, auth=self.auth, json=data, timeout=30)
        else:
            response = requests.post(url, params=params, headers=headers, auth=self.auth, data=data, timeout=30)
        response.raise_for_status()
        return response

    # pylint: disable=W0102
    def _get(self, url, params={}, headers={}, localized=True, cached=False, authenticated=True):

        if authenticated:
            headers['User-Agent'] = self.auth.user_agent

        if localized:
            headers['locale'] = self.prefered_subtitle
            if self.prefered_audio != "original":
                headers['preferred_audio_language'] = self.prefered_audio

        if cached:
            response = urlquick.get(url, params=params, headers=headers, auth=self.auth, timeout=30)
        else:
            response = requests.get(url, params=params, headers=headers, auth=self.auth, timeout=30)

        response.raise_for_status()

        return response

    def get_watchlist(self, start=0):
        self._log("Showing watchlist")
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/discover/{self.auth.data['account_id']}/watchlist"
        params = {
            "n": self.page_size,
            "start": start
        }
        data = self._get(url, params=params).json()
        ids = list(map(lambda item: item['panel']['id'], data['data']))
        data = self.get_objects(ids)
        playheads = self.get_playhead(ids)
        if len(data['data']) > 0:
            res = []
            for item in data['data']:
                playhead = utils.lookup_playhead(playheads['data'], item['id'])
                res.append(Episode(item, playhead))

            next_link = None
            if start + self.page_size < data['total']:
                next_link = {"start": start + self.page_size}
            return res, next_link
        return False, None

    def search_anime(self, query, start=0):
        self._log(f"Looking up for animes with query {query}, from {start}")
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/discover/search"
        params = {
            "q": query,
            "n": self.page_size,
            "type": "series",
            "start": start
        }
        data = self._get(url, params=params).json()
        if len(data['data']) > 0:
            res = []
            for item in data['data'][0]['items']:
                res.append(Series(item))
            next_link = None
            if start + self.page_size < data['data'][0]['count']:
                next_link = {"start": start + self.page_size}
            return res, next_link
        return False, None

    def get_history(self, page=1):
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/{self.auth.data['account_id']}/watch-history"
        params = {
            "page_size": self.page_size,
            "page": page
        }
        data = self._get(url, params=params).json()
        playheads = self.get_playhead([item['panel']['id'] for item in data['data']])
        res = []
        for item in data['data']:
            playhead = utils.lookup_playhead(playheads['data'], item['id'])
            res.append(Episode(item['panel'], playhead))
        next_link = None
        if page * self.page_size < data['total']:
            next_link = {"page": page + 1}
        return res, next_link

    def get_crunchylists(self):
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/{self.auth.data['account_id']}/custom-lists"
        data = self._get(url).json()
        return data['data']

    def get_crunchylist(self, list_id):
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/{self.auth.data['account_id']}/custom-lists/{list_id}"
        data = self._get(url).json()
        res = []
        for item in data['data']:
            res.append(Series(item['panel']))
        return res

    def get_series_seasons(self, series_id):
        self._log(f"Get seasons of series {series_id}")
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/cms/series/{series_id}/seasons"
        data = self._get(url).json()
        res = []
        for item in data['data']:
            res.append(Season(item))
        return res

    def get_season_episodes(self, season_id):
        self._log(f"Get episodes of seasons {season_id}")
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/cms/seasons/{season_id}/episodes"
        data = self._get(url).json()
        list_ids = [item['id'] for item in data['data']]
        playheads = self.get_playhead(list_ids)
        episodes = self.get_objects(list_ids)
        res = []
        for item in data['data']:
            episode = utils.lookup_episode(episodes['data'], item['id'])
            playhead = utils.lookup_playhead(playheads['data'], item['id'])
            res.append(Episode(episode, playhead))
        return res

    def get_objects(self, id_list):
        objects = ",".join(id_list)
        self._log(f"Get objects {objects}")
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/cms/objects/{objects}"
        response = self._get(url)
        return response.json()

    def get_stream_infos(self, episode_id):
        self._log(f"Get streams for episode id {episode_id}")
        episode = self.get_objects([episode_id])["data"][0]
        obj_episode = Episode(episode, 0)
        stream = utils.lookup_stream(episode, self.prefered_audio)
        url = f"{utils.CRUNCHYROLL_PLAY_URL}/v1/{stream['stream_id']}/android/phone/play"
        data = self._get(url, localized=False).json()
        infos = {
            "url": data['url'],
            "subtitles": data["subtitles"],
            "name": obj_episode.label,
            "auth": f"Bearer {self.auth.data['access_token']}",
            "token": data['token'],
            "stream_id": stream['stream_id'],
            "actual_audio": stream['actual_audio']
        }
        return infos

    def get_playhead(self, id_list):
        episodes = ','.join(id_list)
        self._log(f"Getting playhead of episodes {episodes}")
        params = {
            "content_ids": episodes
        }
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/{self.auth.data['account_id']}/playheads"
        data = self._get(url, params=params).json()
        return data

    def update_playhead(self, episode_id, time):
        self._log(f"Update playhead of episode {episode_id} with time {time}")
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/{self.auth.data['account_id']}/playheads"
        data = {
            "content_id": episode_id,
            "playhead": time
        }
        self._post(url, data=data, json=True)

    def browse(self, sort_by=None, start=0, number=10, categories=[], seasonal_tag=None):
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/discover/browse"
        params = {
            "n": number,
            "start": start
        }
        if sort_by:
            params['sort_by'] = sort_by
        if len(categories) > 0:
            params['categories'] = ",".join(categories)
        if seasonal_tag:
            params['seasonal_tag'] = seasonal_tag

        data = self._get(url, params=params).json()
        res = []
        for item in data['data']:
            res.append(Series(item))
        next_link = None
        if start + number < data['total']:
            next_link = {"start": start + number}
        return res, next_link

    def browse_index(self, sort_by):
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/discover/browse/index"
        params = {
            "sort_by": sort_by
        }
        response = self._get(url, params=params)
        return response.json()

    def get_alpha(self):
        data = self.browse_index('alphabetical')
        res = []
        for item in data['data']:
            res.append({
                'prefix': item['prefix'],
                'start': item['offset'],
                'number': item['total']
            })
        return res

    def get_popular(self, start=0, categories=[]):
        self._log(f"Looking up for popular animes from {start}")
        return self.browse(sort_by="popularity", start=start, number=self.page_size, categories=categories)

    def get_newly_added(self, start=0, categories=[]):
        self._log(f"Looking up for animes to discover from {start}")
        return self.browse(sort_by="newly_added", start=start, number=self.page_size, categories=categories)

    def get_categories(self):
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/discover/categories"
        data = self._get(url).json()
        res = []
        for category in data['data']:
            res.append(Category(category))
        return res

    def get_sub_categories(self, parent_id):
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/discover/categories/{parent_id}/sub_categories"
        data = self._get(url).json()
        res = []
        for category in data['data']:
            res.append(Category(category, parent_id))
        return res

    def get_seasonal_tags(self):
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/discover/seasonal_tags"
        data = self._get(url).json()
        return data['data']

    def get_episode_skip_events(self, episode_id):
        url = f"{utils.CRUNCHYROLL_STATIC_URL}/skip-events/production/{episode_id}.json"
        try:
            response = self._get(url, localized=False, authenticated=False)
            return response.json()
        except HTTPError as err:
            if err.response.status_code == 403:
                self._log(f"No skip events for episode {episode_id}")
            else:
                self._log(f"Unexpected status_code {err.response.status_code} for episode {episode_id}")
                self._log(f"{err.response.reason} - {err.response.text}")
            return {}

    def get_multiprofile(self):
        url = f"{utils.CRUNCHYROLL_API_URL}/accounts/v1/me/multiprofile"
        data = self._get(url).json()
        res = []
        for user in data['profiles']:
            res.append(User(user))
        return res

    def get_profile(self, profile_id):
        url = f"{utils.CRUNCHYROLL_API_URL}/accounts/v1/me/multiprofile/{profile_id}"
        data = self._get(url).json()
        return data

    def get_next_episode(self, episode_id):
        url = f"{utils.CRUNCHYROLL_API_URL}/content/v2/discover/up_next/{episode_id}"
        resp = self._get(url)
        if resp.status_code == 200:
            data = resp.json()
            episode = data['data'][0]
            episode_id = episode['panel']['id']
            playhead = utils.lookup_playhead(self.get_playhead([episode_id])['data'], episode_id)
            return Episode(episode['panel'], playhead)
        return None
