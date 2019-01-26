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
              'scenario_info':'сценарий',
              'article_info':'статья',
              'study_info':'учебник',
              'sketch_info':'очерк',
              'review_info':'рецензия',
              'collection_info':'сборник',
              'essay_info':'эссе',
              'comix_info':'комикс',
              'excerpt_info':'отрывок'
              }


def clean_html(content):
    """
    Clean of > and < characters in a tags.
    Replace them by &lt; and &rt; sequences.
    Preserve <img> tags.
    """
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
    

def get_pseudo_list(author, href_author):
    """
    Generate list of possible pseudo labesl to be able to filter out 
    works issued under original author name in case of processing his pseudo name.
    """
    pseudo_list = []

    pseudo = ''
    pseudo_alphabet = ''
    pseudo_index = author.find('псевдоним')
    if pseudo_index > -1:
        pseudo_alphabet = author[:pseudo_index - 3]
        if pseudo_alphabet == href_author:
            return author, []
        pseudo = ' '.join(reversed(pseudo_alphabet.replace(',', '').split()))
        if pseudo == pseudo_alphabet:
            p_list = pseudo_alphabet.split('.')
            pseudo = ''
            pseudo_alphabet = ''
            for p in p_list:
                if p:
                    pseudo_alphabet = ' '.join([pseudo_alphabet, p + '.'])
            pseudo_alphabet = pseudo_alphabet.strip()
            pseudo = ' '.join(reversed(pseudo_alphabet.replace(',', '').split()))
        pseudo_wo_spaces = pseudo.replace(' ', '')
        pseudo_alphabet_wo_spaces = pseudo_alphabet.replace(' ', '')
        pseudo_list = ['под псевдонимом ' + pseudo,
                       'под псевдонимом ' + pseudo_wo_spaces,
                       'под псевдонимом ' + pseudo_alphabet, 
                       'под псевдонимом ' + pseudo_alphabet_wo_spaces,
                       'п.п. ' + pseudo,
                       'п.п. ' + pseudo_wo_spaces,
                       'п.п. ' + pseudo_alphabet, 
                       'п.п. ' + pseudo_alphabet_wo_spaces,                       
                       'за подписью ' + pseudo,
                       'за подписью ' + pseudo_alphabet]
        
    return pseudo_alphabet, pseudo_list

    
def get_works(author_url, author, href_author, file):
    """
    Get all works for appropriate author.
    Filter works belong to original author if author pseudo name is processing 
    to avoid obsolete duplications in result file.
    """    
    pseudo_alphabet, pseudo_list = get_pseudo_list(author, href_author)
    
    works_response = get_content(FANTLAB_ROOT_URL + author_url)
    
    if works_response is not None:
        works_doc = lh.fromstring(works_response)

        try:

            for wt in WORK_TYPES:
                work_type = WORK_TYPES[wt]
                span_elements = works_doc.xpath("//tbody[@id='" + wt + "']/tr/td/div[@class='dots']/span")
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

                    pseudo_label = ''
                    pseudo_labels = span.xpath("font[@color='gray' and not(@title)]")
                    if pseudo_labels:
                        pseudo_label = pseudo_labels[0].text_content().strip().replace('"','')
                            
                    if len(titles) > 1:
                        print(len(titles))

                    if not(pseudo_list):
                        print('\t{}\t{}\t{}'.format(year, work_type, title))
                        file.write('{},{},{},{},{}\n'.format(author, year, work_type, title, orig_title))
                    elif any([pseudo_label.find(p) != -1 for p in pseudo_list]):
                        print('\t{}\t{}\t{}'.format(year, work_type, title))
                        file.write('{},{},{},{},{}\n'.format(pseudo_alphabet, year, work_type, title, orig_title))
          
        except (IndexError, ValueError, TypeError) as e:
            print('Error during getting the work : {1}'.format(str(e)))
            return None
                
               
def get_authors():
    """
    Download authors and their works to csv-file.
    """
    all_authors_response = get_content(FANTLAB_ROOT_URL + '/autorsall')
    
    if all_authors_response is not None:
        
        #Store the contents of the website under doc
        doc = lh.fromstring(all_authors_response)
        
        #Parse data that are stored between <tr>..</tr> of HTML
        tr_elements = doc.xpath("//tr[@class='v9b']")
        
        i = 0
        
        myfile = open('fantlab_result.txt', 'w', 'utf-8')
        
        #For each row, store each first element (cell 0) and an empty list
        for td in tr_elements:
            i+=1
            name = str(td[0].text_content())

            href_name = ''
            href_names = td[0].xpath("span/a[@href]")
            if href_names:
                href_name = str(href_names[0].text_content())

            if len(name) > 1:
                print('%d %s'%(i,name))

            for href_elements in td[0].iterlinks():
                get_works(href_elements[2], name, href_name, myfile)

        myfile.close()
        
        return None
    
    # Raise an exception if we failed to get any data from the url
    raise Exception('Error retrieving contents at {}'.format(FANTLAB_ROOT_URL))
    
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
