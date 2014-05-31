#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from collections import namedtuple
from ddlgenerator.ddlgenerator import Table

LinkTuple = namedtuple('link', ('category', 'subcategory', 'link_text', 'link_target', 'description', 
                                'phone', 'address', 'email', 'source'))

email_patt = re.compile(r'@.*?\.(org|com|edu|info|biz|us|ca)\b', re.IGNORECASE)
url_patt = re.compile(r'\.(org|com|edu|info|biz|us|ca)\b', re.DOTALL)
def parse_url(block):
    lines = block.splitlines()
    for (line_no, line) in enumerate(lines):
        if url_patt.search(line):
            name = '\n'.join(lines[:line_no])
            url = line
            try:
                lines = lines[line_no+1:]
                if lines[0].endswith('html'):
                    url = '%s%s' % (url, lines.pop(0))
            except IndexError:
                pass
            return '\n'.join(lines), name, url
    return block, None, None

def parse_regex(block, regex):
    lines = block.splitlines()
    for (line_no, line) in enumerate(lines):
        if regex.search(line):
            result = lines.pop(line_no)
            return '\n'.join(lines), result
    return block, None
        
phone_patt = re.compile(r'\(\d\d\d\)\s*\d\d\d(\-|\.)\d\d\d\d')
address_patt = re.compile(r'\b(st|ave|street|avenue|lane|ct|way|place|box|rt|rd|square|blvd|boulevard|plaza)\b', 
                          re.IGNORECASE)
state_patt = re.compile(r'\bGA\b')

def _content(file_name):
    with open(file_name) as infile:
        content = infile.read()
    content = content.replace('', '')
    content = content.decode('utf8')
    return content
       
blocksplitter = re.compile(r'\n\s*\n')

def nyc_data(): 
    file_name = 'NYC-Metro-TGNC-Resources_Updated-9_12_2013.txt'
    content = _content(file_name)

    current_heading = ''
    current_subheading = ''
    for block in blocksplitter.split(content):
        lines = block.strip().splitlines()
        nlines = len(lines)
        if nlines == 1:
            if block.startswith('- '):
                current_heading = block.strip('-').strip().title() 
                current_subheading = ''
            else:
                current_subheading = block.strip().title()
            continue
        
        (block, name, url) = parse_url(block)
        (block, phone) = parse_regex(block, phone_patt)
        (block, address) = parse_regex(block, address_patt)
        description = block
        
        tup = LinkTuple(category=current_heading, subcategory=current_subheading,
                        link_text=name, link_target=url,
                        description=description, phone=phone, address=address, email=None,
                        source=file_name)
        yield tup
     
def ga_data(): 
    file_name = 'GA_Resource_List.txt'
    content = _content(file_name)

    current_heading = ''
    current_subheading = ''
    for block in blocksplitter.split(content):
        lines = block.strip().splitlines()
        nlines = len(lines)
        if nlines == 1:
            if block.startswith('- '):
                current_heading = block.strip('-').strip().title() 
                current_subheading = ''
            else:
                current_subheading = block.strip().title()
            continue
        
        (block, email) = parse_regex(block, email_patt)
        (block, url) = parse_regex(block, url_patt)
        (block, phone) = parse_regex(block, phone_patt)
        (block, address) = parse_regex(block, address_patt)
        (block, state) = parse_regex(block, state_patt)
        if state:
            address = '%s\n%s' % (address, state)
        name = block.splitlines()[0]
        description = '\n'.join(block.splitlines()[1:])
        
        tup = LinkTuple(category=current_heading, subcategory=current_subheading,
                        link_text=name, link_target=url,
                        description=description, phone=phone, address=address, email=email,
                        source=file_name)
        yield tup
        
if __name__ == '__main__':
    tbl = Table(nyc_data(), table_name='nyc', force_pk=True, varying_length_text=True)
    print(tbl.sql(inserts=True,drops=True,dialect='postgresql').encode('utf8'))
    tbl = Table(ga_data(), table_name='ga', force_pk=True, varying_length_text=True)
    print(tbl.sql(inserts=True,drops=True,dialect='postgresql').encode('utf8'))
       