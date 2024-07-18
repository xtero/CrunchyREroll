# -*- coding: utf-8 -*-
# ${LICENSE_HEADER}

from ..modules import cloudscraper
from . import utils
import xbmcvfs
import pickle
import copyreg
import ssl

PICKLE=xbmcvfs.translatePath("special://temp/crunchyroll_scraper.pkl")

copyreg.pickle(ssl.SSLContext, lambda obj: (obj.__class__, (obj.protocol,)))

def get_or_create_scraper():
    if xbmcvfs.exists(PICKLE):
        with open(PICKLE, 'rb') as in_file:
            scraper = pickle.load(in_file)
            in_file.close()
        return scraper
    scraper = cloudscraper.create_scraper(debug=True,delay=10)
    # Make sure that we did a first query to main domain at least once
    basic_auth = utils.get_basic_auth()
    headers = {
        "User-Agent": basic_auth['user-agent']
    }
    scraper.get(utils.CRUNCHYROLL_API_URL,headers=headers)
    return scraper

def store_scraper(scraper):
    print(scraper)
    with open(PICKLE, 'wb') as out_file:
        pickle.dump(scraper, out_file)
        out_file.close()
