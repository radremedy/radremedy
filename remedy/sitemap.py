"""
sitemap.py

Generates a robots.txt and corresponing sitemap
"""
from sqlalchemy.orm import load_only

from radremedy import db
from rad.models import News, Resource

from datetime import datetime
import os
import xml.etree.ElementTree as ET


def add_url(
        urlset,
        base_url,
        url_path,
        last_updated=None,
        priority=None,
        frequency=None):
    """
    Adds a new URL to the set.

    Args:
        urlset: The root urlset element to add to.
        base_url: The base path for all URLs, with no trailing slash.
        url_path: The path to the URL, including a leading slash.
        last_updated: The last-updated date of the URL. Optional.
        priority: The priority of the URL, from 0.0 to 1.0. Optional.
        frequency: The frequency of updates. Optional.
    """

    # Build a new URL element
    url_elem = ET.SubElement(urlset, 'url')

    # Add the location (required)
    ET.SubElement(url_elem, 'loc').text = base_url + url_path

    # Add last updated (optional)
    if last_updated:
        # Strip out the time component if needed
        if isinstance(last_updated, datetime):
            last_updated = last_updated.date()

        ET.SubElement(url_elem, 'lastmod').text = last_updated.isoformat()

    # Add priority (optional)
    if priority:
        ET.SubElement(url_elem, 'priority').text = '{:.2f}'.format(priority)

    # Add frequency string (optional)
    if frequency:
        ET.SubElement(url_elem, 'changefreq').text = frequency


def create_sitemap(application):
    """
    Creates a robots.txt and sitemap file.
    """
    with application.app_context():

        base = application.config.get('BASE_URL', 'https://radremedy.org')

        dest_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'robots')

        print 'Outputting to ' + dest_folder

        # Create the folder if it doesn't exist
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        map = ET.Element('urlset')
        map.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        # Add the base URL
        add_url(map, base, '/', priority=1.0, frequency='weekly')

        # Add important base information pages
        add_url(map, base, '/about/', priority=0.9)
        add_url(map, base, '/projects/', priority=0.9)
        add_url(map, base, '/get-involved/', priority=0.9)
        add_url(map, base, '/donate/', priority=0.9)

        # Add slightly less-important pages
        add_url(map, base, '/about-the-beta/', priority=0.8)
        add_url(map, base, '/terms-of-service/', priority=0.8)
        add_url(map, base, '/privacy-policy/', priority=0.8)
        add_url(map, base, '/disclaimer/', priority=0.8)
        add_url(map, base, '/contact/', priority=0.8)

        # Add news listing
        add_url(map, base, '/news/', priority=0.9, frequency='monthly')

        # Add individual news pages
        news_articles = db.session.query(News). \
            filter(News.visible == True). \
            options(load_only('id', 'date_created')). \
            all()

        for article in news_articles:
            add_url(
                map,
                base,
                '/news/' + str(article.id) + '/',
                last_updated=article.date_created,
                priority=0.7)

        # Add resources
        resources = db.session.query(Resource). \
            filter(Resource.visible == True). \
            filter(Resource.is_approved == True). \
            options(load_only('id', 'last_updated')). \
            all()

        for res in resources:
            add_url(
                map,
                base,
                '/resource/' + str(res.id) + '/',
                last_updated=res.last_updated,
                priority=0.4)

        # Generate the XML element and save to the folder
        tree = ET.ElementTree(map)
        tree.write(
            os.path.join(dest_folder, 'sitemap.xml'),
            xml_declaration=True,
            encoding='utf-8')

        # Start building the robots.txt file
        robots_lines = [
            'User-agent: *',
            'Sitemap: ' + base + '/sitemap.xml',
            'Disallow: /admin/',
            'Disallow: /login/',
            'Disallow: /signup/',
            'Disallow: /request-reset/',
            'Disallow: /reset-password/',
            'Disallow: /submit-provider/',
            'Disallow: /review/'
        ]

        # Open up the file, write each line above, and close.
        with open(os.path.join(dest_folder, 'robots.txt'), 'w') as robots_file:

            for line in robots_lines:
                robots_file.write(line + '\n')
