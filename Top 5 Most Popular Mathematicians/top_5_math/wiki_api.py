#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    wiki_api.py

    Created on Mon Jan  7 20:57:47 2019

    @author: Andr

    MediaWiki Action API
    Search for a text or title

"""

from top_5_math.logging import log_error
from requests import get
from requests.exceptions import RequestException
from contextlib import closing

URL = "https://en.wikipedia.org/w/api.php"

def search_title(searchpage):
    
    PARAMS = {
            'action':"query",
            'list':"search",
            'srsearch': searchpage,
            'format':"json"
            }

    try:
        with closing(get(url=URL, params=PARAMS)) as response:
            json_data = response.json()
        
    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(URL, str(e)))
        return None
    
    return json_data