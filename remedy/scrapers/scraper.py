"""
scraper.py

What a scraper promises to be like in this application.

"""

class Scraper(object):
    """
    This class is a template or better said interface,
    all scrapers should inherit from this class.

    Currently it promises that all scrapers will have a source
    and a scrape method.

    This is going to be used to automate the scraping of multiple websites.

    So somewhere there will be some code that looks like this:

    for scraper in scrapers:
        data = scraper.run()
        db.save(data)
        print('Finished scraping %s' % scraper.source)

    The source is used to categorize records in the database.

    All subclasses should override the scrape method.
    *DO NOT OVERRIDE THE run METHOD*. The run method makes
    sure that the data returned is valid and might add things
    like logging and concurrency in the future.

    In the future it might provide some other functionality that might help
    other scrapers.

    """
    def __init__(self, source):
        """

        :param source: The data source. Most of the time this will be
        the site's name.d
        """
        self.source = source

    @staticmethod
    def valid(data):
        """
        It makes sure that all data returned by the scrapers
        is valid. Making it safer and easier to save
        them into the database.

        :return: is the data is valid?
        """
        return True

    def scrape(self):
        """
        Method that should return the data collected from the
        source.

        :return: the data collected, and it should be valid
        """
        raise NotImplemented('%s does not seem to know how to scrape' % self.__class__)

    def _validated_scrape(self):
        """
        Runs the scraper and validates the data,
        throwing a fit if it isn't valid.

        :return: the data
        """
        data = self.scrape()

        if Scraper.valid(data):
            return data
        else:
            return TypeError('All scrapers should return the right data type')

    def run(self):
        """
        Run the scraper and collect the data. Please do not override.

        :return: the data
        """
        return self._validated_scrape()

