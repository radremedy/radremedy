"""
scraper.py

Scraper template used throughout the application.

"""
from radrecord2 import RadRecord


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
        Initialization function 

        Args:
            self: self explaitory 
            source: The data source. Most of the time this will be
                the site's name.d
        """
        self.source = source

    @staticmethod
    def valid(data):
        """
        It makes sure that all data returned by the scrapers
        is valid. Making it safer and easier to save
        them into the database.

        In order for the data to be valid, it must follow our
        data format:
        https://github.com/radremedy/radremedy/wiki/RAD-Record-Format

        We assert this by returning a list of RadRecord instances.

        Args: 
            data: data to be checked 

        Returns: 
            A boolean indicated whether or not the data is valid 
        """
        # TODO: this might be iterating too much, might be better
        # to check while appending data instead of at the end
        for d in data:
            if d is not None and not issubclass(d.__class__, RadRecord):
                return False
        else:
            return True

    def scrape(self):
        """
        Method that should return the data collected from the
        source. 

        Returns: 
            the data collected, and it should be valid

        Raises: 
            NotImplemented: this method is not yet implemented 
        """
        raise NotImplemented('%s does not seem to know how to scrape' % self.__class__)

    def _validated_scrape(self):
        """
        Runs the scraper and validates the data,
        throwing an exception if it isn't valid.

        Returns: 
            the data in RAD-Record Format 

        Raises: 
            TypeError: the data is not in RAD-Record Format
        """
        data = self.scrape()

        if Scraper.valid(data):
            return data
        else:
            raise TypeError('All scrapers should return the right data type')

    def run(self):
        """
        Run the scraper and collect the data. Please do not override.

        Returns: 
            the data collected by the scraper 
        """
        return self._validated_scrape()

