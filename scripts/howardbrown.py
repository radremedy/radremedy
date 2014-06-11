#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Consume Howard Brown resource sites, export namedtuples.

"""
import bs4
import requests
from collections import namedtuple
import re
from unidecode import unidecode

do_by_hand = """
http://www.howardbrown.org/hb_services.asp?id=2475
""".strip().split()

LinkTuple = namedtuple('link', ('category', 'link_text', 'link_target', 'description', 'source'))

def cleanse(txt):
    txt = txt.replace(u'Â',u'')
    return unidecode(txt).replace('\r\n', '\n')

def get_soup(url):
    response = requests.get(url)
    content = response.content
    soup = bs4.BeautifulSoup(content)
    return soup
  
def split(soup, splitter):
    following = str(soup)
    last_splitter_found = None
    for splitter_found in soup.find_all(splitter):
        (preceding, following) = following.split(str(splitter_found), 1)
        if last_splitter_found:
            yield (last_splitter_found, preceding)
        last_splitter_found = splitter_found
    yield (last_splitter_found, following)
        
           
def is_a_pseudo_header(element):
    if element.name != 'a':
        return False
    if element.parent.name in ('b', 'strong') or \
       element.parent.parent.name in ('b', 'strong'):
        return True
    if element.find(['b', 'strong']):
        return True
    return False
   
starts_with_end_tag = re.compile(r'^(\s*<\s*/.*?>)+') 

def broken_by_bold(url):
    soup = get_soup(url).find('td', id='content')
    for (link, txt_following) in split(soup, is_a_pseudo_header):
        category = link.find_previous('font', color=re.compile('#00000'))
        category = (category and category.text) or ''
        if len(category.split()) > 10:
            category = ''
        if link.text and '://' in link['href']:
            # BeautifulSoup will not parse if starts with end tag
            txt_following = starts_with_end_tag.sub('', txt_following)
            soup_following = bs4.BeautifulSoup(txt_following)
            tup = LinkTuple(category, cleanse(link.text), link['href'], 
                            cleanse("\n".join(soup_following.stripped_strings)),
                            url)
            yield tup
    
            
targets = {
    "http://www.howardbrown.org/hb_services.asp?id=2722": broken_by_bold,
    "http://www.howardbrown.org/hb_services.asp?id=2706": broken_by_bold,
    "http://www.howardbrown.org/hb_services.asp?id=2723": broken_by_bold,
    "http://www.howardbrown.org/hb_services.asp?id=2725": broken_by_bold,
    "http://www.howardbrown.org/hb_services.asp?id=2715": broken_by_bold
    }

      
def data(): 
    for (target, func) in targets.items():
        for row in func(target):
            yield row
            
if __name__ == '__main__':
    for row in data():
        print(row)
   
    
