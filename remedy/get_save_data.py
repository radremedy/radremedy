"""
get_save_data.py

Collects all the scrapers that follow the Scraper class.
After running a scrape, the data is saved to the database.

"""

from scrapers.howardbrown import HowardBrownScraper
from rad.db_fun import get_or_create
from radremedy import app, db, Resource

# the list of scrapers that we want to run
# in the future there might be more,
# right now it's just Howard Brown
SCRAPERS = (HowardBrownScraper(), )


def run_these(scrapers, db, model):
    """
    Calls the run method in all the scrapers
    and saves the data collected into
    the database

    :param scrapers: A list of Scraper subclasses
    :param db: A database to save the data on
    :param model: A database model to save the data on
    """
    # TODO: this method is a little funky, fixme

    for scraper in scrapers:

        for data_row in scraper.run():
            # TODO: why is the data row sometimes returning {}
            if data_row is not None and data_row != {}:
                new_record, record = get_or_create(db.session, model, **data_row)
                db.session.add(record)

    db.session.commit()


if __name__ == '__main__':
    db.init_app(app)

    with app.app_context():
        run_these(SCRAPERS, db, Resource)