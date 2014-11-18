import os
import os.path as op

import re

from bs4 import BeautifulSoup

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

CATEGORY_CLASS_NAME = "rad-category"

RESOURCE_CLASS_NAME = "rad-resource"

def process_pdf(in_path, out_path):
    page_numbers=set()

    # Get source/destination file handles
    in_file = file(in_path, 'rb')
    out_file = file(out_path, 'w')

    # Set up the resource manager, device, and interpreter
    res_mgr = PDFResourceManager()
    device = HTMLConverter(res_mgr, out_file, codec='utf-8', laparams=LAParams(), imagewriter=None)
    interpreter = PDFPageInterpreter(res_mgr, device)

    for page in PDFPage.get_pages(in_file, page_numbers, 
            maxpages=0, password="", 
            caching=True, check_extractable=True):
        interpreter.process_page(page)

    # Close all the file handles
    in_file.close()
    device.close()
    out_file.close()
    return

def clean_html(html_path, config):
    # Read in the HTML
    html_file = open(html_path, 'r')
    soup = BeautifulSoup(html_file.read())
    html_file.close()

    # Tag all category names
    tag_items(soup, 
        CATEGORY_CLASS_NAME, 
        config['category_elem'], 
        config['category_style'], 
        config['category_container'])

    # Tag all resources
    tag_items(soup, 
        RESOURCE_CLASS_NAME, 
        config['resource_elem'], 
        config['resource_style'], 
        config['resource_container'])

    # Get only the text content of all categories
    for category_elem in soup.find_all(class_=CATEGORY_CLASS_NAME):
        category_elem.string = category_elem.get_text()

    # Remove all style tags
    for elem in soup.find_all():
        del elem['style']

    # Spit the HTML back out
    html_file = open(html_path, 'w')
    html_file.write(soup.prettify().encode('utf8'))
    html_file.close()
    return

def tag_items(bs, tagclass, elemname, style, container):
    """
    Tags items with the appropriate CSS class.

    Args:
        bs: The BeautifulSoup object to operate on.
        tagclass: The class to use for any tagged items.
        elemname: The name of the element to tag.
        style: The style to match against for each tag.
        container: The container for the item (as an element name) which,
            if provided, will be tagged instead of the element.
    """
    if elemname and style:
        for elem in bs.find_all(elemname, style=re.compile(style, re.IGNORECASE)):
            if container and elem.find_parent(container):
                elem.find_parent(container)['class'] = tagclass
                elem.unwrap()
            else:
                elem['class'] = tagclass    

in_dir = 'C:\\Users\\Anonymous\\Dropbox\\RAD\\Coding & Site Building\\Back End Databasing\\1 Need Scraped\\'
out_dir = op.dirname(op.realpath(__file__))

pdf_files = [
    {
        "filename": 'SouthEast-Southern Equality.pdf',
        "category_container": "div",
        "category_elem": "span",
        "category_style": re.escape("font-family: UXOXEO+MyriadPro-Bold; font-size:22px"),
        "resource_container": "div",
        "resource_elem": "span",
        "resource_style": re.escape("font-family: UXOXEO+MyriadPro-Bold; font-size:19px")
    }
]

for pdf_file in pdf_files:
    print "Processing " + pdf_file['filename']

    # Calculate the in and out paths
    in_path = op.join(in_dir, pdf_file['filename'])
    out_path = op.join(out_dir, op.splitext(op.basename(in_path))[0] + '.html')

    process_pdf(in_path, out_path)
    clean_html(out_path, pdf_file)
