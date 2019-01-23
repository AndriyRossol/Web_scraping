# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 23:34:17 2019

@author: Andr
"""

from codecs import open
from contextlib import closing
from requests import get
from requests.exceptions import RequestException

import lxml.html as lh
import pandas as pd
import re

FANTLAB_ROOT_URL='http://fantlab.ru'

WORK_TYPES  = {'novel_info':'роман', 
              'story_info':'повесть', 
              'shortstory_info':'рассказ', 
              'microstory_info':'микрорассказ',
              'poem_info':'поэзия',
              'tale_info':'сказка',
              'other_info':'другое',
              'documental_info':'документальное',
              'piece_info':'пьеса',
              'article_info':'статья',
              'study_info':'учебник',
              'sketch_info':'очерк',
              'review_info':'рецензия',
              'collection_info':'сборник',
              'essay_info':'эссе'
              }

def clean_html(content):
    a_regex = """<div[^>]*><span[^>]*>&nbsp;[\w\.\"\s=<>/]*<a[^>]*>([<][^<img].*?)</a>[\w\.\"\s=<>/]*&nbsp;</span></div>"""
    pattern = re.compile(a_regex)
    titles = re.findall(pattern, content)
    for t in titles:
        content = content.replace(t, t.replace('<', '&lt;').replace('>', '&gt;'))
    return content
    
def get_content(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return clean_html(resp.content.decode(resp.encoding))
            else:
                return get_content(url)

    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))
        return None
    
def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    try:
        if 'Content-Type' in resp.headers:
            content_type = resp.headers['Content-Type'].lower()
            return (resp.status_code == 200 
                    and content_type is not None 
                    and content_type.find('html') > -1)
        else:
            return False
    except KeyError as e:
        print('Error during checking the response : {1}'.format(str(e)))
        return None
       
def get_works(author_url, author, file):
    
    result = []
    
    works_response = get_content(FANTLAB_ROOT_URL + author_url)
    
    if works_response is not None:
        works_doc = lh.fromstring(works_response)

        try:

            for work_type in WORK_TYPES:
                wt = WORK_TYPES[work_type]
                span_elements = works_doc.xpath("//tbody[@id='" + work_type + "']/tr/td/div[@class='dots']/span")
                prev_year = ''
                for span in span_elements:

                    year = ''
                    years = span.xpath("font")
                    if years:
                        if years[0].text_content().isdigit():
                            year = years[0].text_content()
                            prev_year = year                            
                        else:
                            year = prev_year

                    orig_title = ''
                    orig_titles = span.xpath("a[@class='agray']")
                    if orig_titles:
                        orig_title = orig_titles[0].text_content().strip() 

                    title = ''
                    titles = span.xpath("a[not(@class) and not(@title)]")
                    if titles:
                        title = titles[0].text_content().strip()

                    if not title:
                        title = orig_title
                    if not orig_title:
                        orig_title = title

                            
                    if len(titles) > 1:
                        print(len(titles))

                    print('\t{}\t{}\t{}'.format(year, wt, title))
                    file.write('{},{},{},{},{}\n'.format(author, year, wt, title, orig_title))
          
        except (IndexError, ValueError, TypeError) as e:
            print('Error during getting the work : {1}'.format(str(e)))
            return None

                       

"""
       tbody_elements = works_doc.xpath("//tbody[@id='story_info']")    
       for tbody in tbody_elements:
           story_type = str(tbody[0].text_content())
           if len(story_type) > 1:
               print(story_type)
"""

               
def get_authors():
    """
    Download authors list into pandas Data Frame
    """
    all_authors_response = get_content(FANTLAB_ROOT_URL + '/autorsall')
    
    if all_authors_response is not None:
        
        #Store the contents of the website under doc
        doc = lh.fromstring(all_authors_response)
        
        #Parse data that are stored between <tr>..</tr> of HTML
        tr_elements = doc.xpath("//tr[@class='v9b']")
        
        #Create empty list
        col=[]
        i=0

        myfile = open('fantlab_result.txt', 'w', 'utf-8')
        
        #For each row, store each first element (cell 0) and an empty list
        for td in tr_elements:
            i+=1
            name = str(td[0].text_content())
            if len(name) > 1:
                print('%d %s'%(i,name))
                col.append((name,[]))

            for href_elements in td[0].iterlinks():
                get_works(href_elements[2], name, myfile)

        myfile.close()
        
        return None
    
    # Raise an exception if we failed to get any data from the url
    raise Exception('Error retrieving contents at {}'.format(ALL_FANTLAB_AUTHORS_URL))
    
if __name__ == '__main__':
    print('Getting the list of all authors from fantlab.ru....')
    names = get_authors()
    print('... done.\n')

    results = []

    results.sort()
    results.reverse()

    no_results = len([res for res in results if res[0] == -1])
    print('\nBut we did not find works for '
          '{} authors on the list'.format(no_results))
