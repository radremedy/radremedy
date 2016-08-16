"""
pagination.py

Defines a basic pagination structure that can be used when displaying
a list of search results.

Based on http://flask.pocoo.org/snippets/44/
"""

from math import ceil


class Pagination(object):
    """
    A basic pagination structure.
    """
    def __init__(self, page, per_page, total):
        """
        Sets up the pagination structure.

        Args:
            page: The current page number, starting at 1.
            per_page: The number of items allowed per page.
            total: The total number of items being paged.
        """
        self.page = page
        self.per_page = per_page
        self.total = total

    @property
    def pages(self):
        """
        Gets the total number of pages.
        """
        return int(ceil(self.total / float(self.per_page)))

    @property
    def has_prev(self):
        """
        Determines if there is a previous page available.
        """
        return self.page > 1

    @property
    def has_next(self):
        """
        Determines if there is a next page available.
        """
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=3, right_edge=2):
        """
        Generates page numbers to display.

        Args:
            left_edge: The number of first pages (1, 2, ...) to show.
            left_current: The number of pages to show
                to the left of the current page.
            right_current: The number of pages to show
                to the right of the current page.
            right_edge: The number of last pages (.., 99, 100) to show.

        Returns:
            An iterator for the page numbers to display.
        """
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
                    (num > self.page - left_current - 1 and
                        num < self.page + right_current) or \
                    num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
