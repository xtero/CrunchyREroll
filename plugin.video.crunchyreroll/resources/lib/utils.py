# -*- coding: utf-8 -*-
# ${LICENSE_HEADER}

import os
import re
from datetime import datetime
import xbmc
import xbmcvfs
import xbmcaddon
import requests
import urlquick

ADDON_ID = "plugin.video.crunchyreroll"
# The idea is to be able mock it for future tests
CRUNCHYROLL_API_URL = "https://beta-api.crunchyroll.com"
CRUNCHYROLL_STATIC_URL = "https://static.crunchyroll.com"
CRUNCHYROLL_PLAY_URL = "https://cr-play-service.prd.crunchyrollsvc.com"
CRUNCHYROLL_LICENSE_URL = "https://cr-license-proxy.prd.crunchyrollsvc.com/v1/license/widevine"
CRUNCHYROLL_UA = "Crunchyroll/3.55.3 Android/14 okhttp/4.12.0"

CACHE_PATH = "special://temp/crunchyroll_cache_subtitles/"


def get_basic_auth():
    url = xbmcaddon.Addon(ADDON_ID).getSetting("auth_url")
    resp = urlquick.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data


def iso_639_1_to_iso_639_2(code):
    locales = {
        "en-US": "eng",
        "en-GB": "eng",
        "es-419": "spa",
        "es-ES": "spa",
        "pt-BR": "por",
        "pt-PT": "por",
        "fr-FR": "fre",
        "de-DE": "ger",
        "ar-SA": "ara",
        "it-IT": "ita",
        "ru-RU": "rus",
        "ta-IN": "tam",
        "hi-IN": "hin",
        "id-ID": "ind",
        "ms-MY": "may",
        "th-TH": "tha",
        "vi-VN": "vie",
        "ja-JP": "jpn"
    }

    return locales.get(code, "unk")


def local_from_id(locale_id):
    locales = [
        "en-US",
        "en-GB",
        "es-419",
        "es-ES",
        "pt-BR",
        "pt-PT",
        "fr-FR",
        "de-DE",
        "ar-SA",
        "it-IT",
        "ru-RU",
        "ta-IN",
        "hi-IN",
        "id-ID"
        "ms-MY",
        "th-TH",
        "vi-VN",
        "ja-JP"
    ]

    if locale_id < len(locales):
        return locales[locale_id]

    return "en-US"


def lookup_playhead(playheads, content_id):
    for playhead in playheads:
        if playhead['content_id'] == content_id:
            return playhead

    return {"playhead": 0, "content_id": content_id, "fully_watched": False}


def lookup_episode(episodes, episode_id):
    for episode in episodes:
        if episode['id'] == episode_id:
            return episode
    return None


def lookup_episode_number(episode):
    number = episode["episode_metadata"].get("episode", "1")
    if number == "":
        number = "1"
    return number


def number_to_int(number):
    if not re.search('^([0-9]*[.])?[0-9]*$', number):
        number = "1"
    return int(float(number))


def lookup_stream(episode, prefered_audio):
    stream_id = None
    actual_audio = None
    if "versions" in episode['episode_metadata'] and episode['episode_metadata']['versions']:
        if prefered_audio == "original":
            for version in episode['episode_metadata']['versions']:
                if version['original']:
                    stream_id = version['guid']
                    actual_audio = version['audio_locale']
        else:
            # If we find prefered_audio, it's return this value
            for version in episode['episode_metadata']['versions']:
                if version['audio_locale'] == prefered_audio:
                    stream_id = version['guid']
                    actual_audio = prefered_audio
            # Else, we provide original version
            if stream_id is None:
                for version in episode['episode_metadata']['versions']:
                    if version['original']:
                        stream_id = version['guid']
                        actual_audio = version['audio_locale']
    else:
        stream_id = episode['id']
        actual_audio = episode['episode_metadata']['audio_locale']
    ret = {"stream_id": stream_id, "actual_audio": actual_audio}
    return ret


def download_subtitle(url, output):
    with open(output, "w", encoding="utf8") as fh:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        response.encoding = "UTF-8"
        fh.write(response.text)
        fh.close()


def get_subtitles(episode_id, subtitles):
    cache_folder = xbmcvfs.translatePath(CACHE_PATH)
    if not xbmcvfs.exists(cache_folder):
        xbmcvfs.mkdirs(cache_folder)

    return_subtitles = []
    for sub in list(subtitles.values()):
        lang = sub['language'].split('-')[0]
        # We keep sub['language'] in the name as we might have for the same lang many different language
        filename = f"{episode_id}.{sub['language']}.{lang}.{sub['format']}"
        file_path = xbmcvfs.translatePath(f"{cache_folder}{filename}")

        if not xbmcvfs.exists(file_path):
            download_subtitle(sub['url'], file_path)
        else:
            now = datetime.timestamp(datetime.now())
            seven_days = 7 * 86400
            if xbmcvfs.Stat(file_path).st_ctime() > (now + seven_days):
                os.remove(xbmc.validatePath(file_path))
                download_subtitle(sub['url'], file_path)

        return_subtitles.append(file_path)
    return return_subtitles


def sub_locale_from_id(locale_id):
    locales = [
        "eng",
        "eng",
        "spa",
        "spa",
        "por",
        "por",
        "fre",
        "ger",
        "ara",
        "ita",
        "rus",
        "tam",
        "hin",
        "ind",
        "may",
        "tha",
        "vie",
        "jpn"
    ]
    if locale_id < len(locales):
        return locales[locale_id]

    return "eng"


def get_cache_path():
    return CACHE_PATH
