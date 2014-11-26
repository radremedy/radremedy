"""
extract_pdfs.py

Contains a utility for extracting content out of PDFs by
converting them to HTML and scraping the result.

Args:
    The base path to the folder containing PDFs.

Sample usage:
    python extract_pdfs.py "C:\Users\RAD\Dropbox\RAD\Coding & Site Building\Back End Databasing\1 Need Scraped"
"""
import sys
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
    """
    Processes a PDF and extracts its contents to HTML.

    Args:
        in_path: The full path to the source PDF file.
        out_path: The full path to the destination HTML file.
    """
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
    """
    Cleans/tags the HTML file at the specified path.

    Args:
        html_path: The full path to the HTML file.
        config: The configuration options for the HTML file.
    """

    # Read in the HTML
    html_file = open(html_path, 'r')
    soup = BeautifulSoup(html_file.read())
    html_file.close()

    # Add horizontal rules between each page
    for page_anchor in soup.find_all('a', attrs={'name': True}):
        page_anchor.replace_with(soup.new_tag("hr"))

    # Tag all category names
    tag_items(soup, 
        CATEGORY_CLASS_NAME, 
        config.get('category_elem'), 
        config.get('category_style'), 
        config.get('category_container'),
        None)

    # Tag all resources
    tag_items(soup, 
        RESOURCE_CLASS_NAME, 
        config['resource_elem'], 
        config['resource_style'], 
        config.get('resource_container'),
        config.get('resource_container_style'))

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

def tag_items(bs, tagclass, elemname, style, container, container_style):
    """
    Tags items with the appropriate CSS class.

    Args:
        bs: The BeautifulSoup object to operate on.
        tagclass: The class to use for any tagged items.
        elemname: The name of the element to tag.
        style: The style to match against for each tag.
        container: The container for the item (as an element name) which,
            if provided, will be tagged instead of the element.
        container_style: The style to match against for the container.
    """
    if elemname and style:
        for elem in bs.find_all(elemname, style=re.compile(style, re.IGNORECASE)):
            elem_container = None

            # See if we need a container
            if container:
                if container_style:
                    elem_container = elem.find_parent(container, 
                        style=re.compile(container_style, re.IGNORECASE))
                else:
                    elem_container = elem.find_parent(container)

            if elem_container:
                elem_container['class'] = tagclass
            else:
                elem['class'] = tagclass

"""
This is the main list of the different PDFs that should be extracted.

Each item in the list is a dictionary with the following keys:
    filename: The name of the file in the specified source directory.
    category_container: The name of the HTML element that contains a category element, if any.
    category_elem: The name of the HTML element that is used for categories.
    category_style: The styling used for each category.
    resource_container: The name of the HTML element that contains a resource, if any.
    resource_container_style: The styling used for each resource container, if any.
    resource_elem: The name of the HTML element that is used for resources.
    resource_style: The styling used for each resource.

To figure out the secret sauce for parsing each PDF, use the
pdf2txt.py script provided by PDFMiner (https://euske.github.io/pdfminer/index.html,
required for use in this script) and look at the raw HTML that's
spit out by the script. It's fairly ugly and verbose, but you should
be able to identify the styles that are used to identify different
categories and resources.
"""
pdf_files = [
    {
        "filename": 'SouthEast-Southern Equality.pdf',
        "category_container": "div",
        "category_elem": "span",
        "category_style": re.escape("font-family: UXOXEO+MyriadPro-Bold; font-size:22px"),
        "resource_container": "div",
        "resource_elem": "span",
        "resource_style": re.escape("font-family: UXOXEO+MyriadPro-Bold; font-size:19px")
    },
    {
        "filename": 'PA-MAZZONI.pdf',
        "category_container": "div",
        "category_elem": "span",
        "category_style": re.escape("font-family: ArialMT; font-size:23px"),
        # In this PDF, all resources are in a span with Arial in 15 pixel font
        "resource_container": "span",
        "resource_container_style": re.escape("font-family: ArialMT; font-size:15px"),
        "resource_elem": "span",
        "resource_style": re.escape("font-family: Arial-BoldMT; font-size:15px")
    }    
]

# Get our base path
if len(sys.argv) < 2:
    print "Usage: python extract_pdfs.py <base PDF path>"
    exit(1)
else:
    in_dir = sys.argv[1]
    print "Using " + in_dir + " as source directory."

out_dir = op.dirname(op.realpath(__file__))

for pdf_file in pdf_files:
    print "Processing " + pdf_file['filename']

    # Calculate the in and out paths
    in_path = op.join(in_dir, pdf_file['filename'])
    out_path = op.join(out_dir, op.splitext(op.basename(in_path))[0] + '.html')

    process_pdf(in_path, out_path)
    clean_html(out_path, pdf_file)
