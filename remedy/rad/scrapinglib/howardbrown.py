#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Consume Howard Brown resource sites, export namedtuples.

"""
import requests
import re
from bs4 import BeautifulSoup
from toolz import concat, partial

# a template for a page on Howard Brown waiting for a number
# from a category
HOWARD_BROWN = "http://www.howardbrown.org/hb_services.asp?id=%d"

HOWARD_BROWN_URLS = [HOWARD_BROWN % 2722,
                     HOWARD_BROWN % 2706,
                     HOWARD_BROWN % 2723,
                     HOWARD_BROWN % 2725,
                     HOWARD_BROWN % 2715,
                     HOWARD_BROWN % 2475]

starts_with_end_tag = re.compile(r'^(\s*<\s*/.*?>)+') 

is_e_type = lambda element_type, element: element.name == element_type
is_bold = partial(is_e_type, 'b')
is_anchor = partial(is_e_type, 'a')
is_strong = partial(is_e_type, 'strong')
b_or_strong = lambda e: is_strong(e) or is_bold(e)

cleanse = lambda txt: txt.replace(u'Â',u'').replace('\r\n', '\n')
get_content = lambda url: requests.get(url).content
get_soup = lambda url: BeautifulSoup(get_content(url))


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
    if not is_anchor(element):
        return False

    elif b_or_strong(element.parent) or b_or_strong(element.parent.parent):
        return True

    elif element.find(['b', 'strong']):
        return True

    else:
        return False
   

def broken_by_bold(url):
    soup = get_soup(url).find('td', id='content')
    black = re.compile('#00000')
    data = []

    for (link, txt_following) in split(soup, is_a_pseudo_header):
        category = link.find_previous('font', color=black)
        category = (category and category.text) or ''

        if len(category.split()) > 10:
            category = ''

        if link.text and '://' in link['href']:
            # BeautifulSoup will not parse if starts with end tag
            txt_following = starts_with_end_tag.sub('', txt_following)
            soup_following = BeautifulSoup(txt_following)

            tup = (category, cleanse(link.text), link['href'],
                   cleanse("\n".join(soup_following.stripped_strings)),
                   url)

            data.append(tup)

    return data


def scrape(targets):
    """
    This method walks every href in the targets list
    and gets it's data from the Howard brown website.

    The targets should be links to categories in the format
    http://www.howardbrown.org/hb_services.asp?id=<number>
    where number is a unsigned integer to the id of the
    category you want to scrape.

    The targets are turned into a set of unique values.

    The records returned are formatted as follow:
    ('category', 'link_text', 'link_target', 'description', 'source')

    So the final data looks like this:
    [('category', 'link_text', 'link_target', 'description', 'source'),
     ('category', 'link_text', 'link_target', 'description', 'source'),
     ...
     ('category', 'link_text', 'link_target', 'description', 'source')]

    :param targets: Links to pages you want to scrape.
    :return: A list of records.
    """
    return list(concat(map(broken_by_bold, set(targets))))
