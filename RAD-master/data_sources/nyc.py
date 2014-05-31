#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nothing to see here.  A one-off for coping with text dumped from a specific PDF.
"""

from unidecode import unidecode
import re

with open('NYC-Metro-TGNC-Resources_Updated-9_12_2013.txt') as infile:
    content = infile.read()

pagebreak = re.compile("""NYC-Metro Area Transgender and Gender Non-Conforming (TGNC) Community Resources\s*\d+\b"""
                       , re.DOTALL | re.MULTILINE)
too_many_spaces = re.compile(r"\S \S \S \S \S")
unspace = re.compile(r"\b(\S) (?=\S)\b")
spacey = re.compile("\b([ ]{2,})", re.DOTALL)
   
content = pagebreak.sub('', content)
fixed_content = []
for line in content.splitlines():
    if too_many_spaces.search(line):
        line = unspace.sub(r"\1", line)
    fixed_content.append(line)
content = "\n".join(fixed_content)
content = spacey.sub(" ", content)
content = unidecode(content)
content = content.replace('aC/', '').replace('%20', ' ')

print(content.encode("utf8"))



              