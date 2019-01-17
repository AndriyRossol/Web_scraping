#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    mathematicians.py
    
    Created on Sun Jan  6 21:40:27 2019

    @author: Andr
    
    Script shows top 5 mathematicians by popularity.
    It uses site fabpedigree.com to get list of mathematicians,
    Wikipedia search API to identify a wikipedia page of a mathematician
    and xtools.wmflabs.org to get number of page's views in the last 60 days.
    
"""

from top_5_math.logging import log_error
import wiki_api
import google_api

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

import json
import csv
import sys

ARTICLEINFO           = 'articleinfo'
MATH_MEN_URL          = 'http://www.fabpedigree.com/james/mathmen.htm'
PAGE_API_ROOT_URL     = 'https://xtools.wmflabs.org/api/page'
WIKIPEDIA_ROOT_URL    = 'en.wikipedia.org/{}'

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None
    
def get_article_info(url):
    """
    Get result of call to XTools's Page API
    """
    
    target_url = '/'.join([PAGE_API_ROOT_URL, ARTICLEINFO, url])  
    
    try:
        with closing(get(target_url, stream=True)) as resp:
            return resp.content

    except RequestException as e:
        log_error('Error during Page API call to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)
  
def get_names():
    """
    Import fix list into dictionary
    """
    with open('name_fix_list.csv', mode='r') as f:
        reader = csv.reader(f)
        fix_dict = {rows[0]:rows[1] for rows in reader}    

    """
    Download the page where the list of mathematicians is found
    and returns a list of strings, one per mathematician
    """
    math_men_response = simple_get(MATH_MEN_URL)
    if math_men_response is not None:
        html = BeautifulSoup(math_men_response, 'html.parser')
        names = set()
        for li in html.select('li'):
            for name in li.text.split('\n'):
                if len(name) > 0:
                    if name.strip() in fix_dict:
                        names.add(fix_dict[name.strip()])
                    else:
                        names.add(name.strip())
        return list(names)


    
    # Raise an exception if we failed to get any data from the url
    raise Exception('Error retrieving contents at {}'.format(MATH_MEN_URL))
    
def get_hits_on_name(name):
    """
    Accepts a `name` of a mathematician and returns the number
    of hits that mathematician's Wikipedia page received in the 
    last 60 days, as an `int`
    """

    # URL_WIKIPEDIA_ROOT is a template string that is used to build a URL.
    articleinfo = get_article_info(WIKIPEDIA_ROOT_URL.format(name))

    if articleinfo is not None:
        
        data = json.loads(articleinfo)

        # if article not found search for alternative name in wikipedia         
        if 'error' in data:
            response = wiki_api.search_title(name)
            if response['query']['searchinfo']['totalhits'] > 0:
                name = response['query']['search'][0]['title']
                articleinfo = get_article_info(WIKIPEDIA_ROOT_URL.format(name))
                data = json.loads(articleinfo)
            else:
                data = {'error'}      

            # if not found by wikipedia, search wikipedia article in google   
            if 'error' in data:
                response = google_api.search_wikipedia_article(name, sys.argv[1], sys.argv[2])
                articleinfo = get_article_info(
                        WIKIPEDIA_ROOT_URL.format(
                                response['items'][0]['formattedUrl'].split('/')[-1]
                                )
                        )
                data = json.loads(articleinfo)
            
        pageviews = data['pageviews']

        try:
            # Convert to integer
            return int(pageviews)
        except:
            log_error("couldn't parse {} as an `int`".format(pageviews))

    log_error('No pageviews found for {}'.format(name))
    return None

if __name__ == '__main__':
    print('Getting the list of names....')
    names = get_names()
    print('... done.\n')

    results = []

    print('Getting stats for each name....')

    for name in names:
        try:
            hits = get_hits_on_name(name)
            print(name + ': ' + str(hits))
            if hits is None:
                hits = -1
            results.append((hits, name))
        except:
            results.append((-1, name))
            log_error('error encountered while processing '
                      '{}, skipping'.format(name))

    print('... done.\n')

    results.sort()
    results.reverse()

    if len(results) > 5:
        top_marks = results[:5]
    else:
        top_marks = results

    print('\nThe most popular mathematicians are:\n')
    for (mark, mathematician) in top_marks:
        print('{} with {} pageviews'.format(mathematician, mark))

    no_results = len([res for res in results if res[0] == -1])
    print('\nBut we did not find results for '
          '{} mathematicians on the list'.format(no_results))