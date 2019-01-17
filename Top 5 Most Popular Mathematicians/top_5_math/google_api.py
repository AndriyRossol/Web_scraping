#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    google_search.py

    Created on Mon Jan  7 22:15:47 2019

    @author: Andr

    Google API
    Search for a wikipedia article

"""

from googleapiclient.discovery import build

def search_wikipedia_article(query, cse_id, api_key):
    
    service = build("customsearch", "v1", developerKey=api_key)

    return service.cse().list(
            q=query, 
            cx=cse_id, 
            siteSearch='en.wikipedia.org',
            ).execute()
