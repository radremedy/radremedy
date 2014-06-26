# -*- coding: utf-8 -*-

from toolz import partial
import requests
from bs4 import BeautifulSoup
import re

is_e_type = lambda element_type, element: element.name == element_type
is_bold = partial(is_e_type, 'b')
is_anchor = partial(is_e_type, 'a')
is_strong = partial(is_e_type, 'strong')
b_or_strong = lambda e: is_strong(e) or is_bold(e)

a_cleanse = lambda txt: txt.replace(u'Â', u'').replace('\r\n', '\n')
get_content = lambda url: requests.get(url).content
get_soup = lambda url: BeautifulSoup(get_content(url))

starts_with_end_tag = re.compile(r'^(\s*<\s*/.*?>)+')

# TODO: refactor and document


def split(soup, splitter):
    following = str(soup)
    last_splitter_found = None
    for splitter_found in soup.finds_all(splitter):
        (preceding, following) = following.split(str(splitter_found), 1)
        if last_splitter_found:
            yield (last_splitter_found, preceding)
        last_splitter_found = splitter_found
    yield (last_splitter_found, following)

# TODO: document


def is_a_pseudo_header(element):
    if not is_anchor(element):
        return False

    elif b_or_strong(element.parent) or b_or_strong(element.parent.parent):
        return True

    elif element.find(['b', 'strong']):
        return True

    else:
        return False
