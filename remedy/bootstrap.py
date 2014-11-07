"""
bootstrap.py 

Imports data from database files and from the scrapers. 
"""
from radremedy import db
from rad.db_fun import get_or_create_resource
from get_save_data import run as run_scrapers
from data_importer.data_importer import get_radrecords, data_dir

import sys

def strap(application):
    """
    First, this function runs the data importers and adds them to the database.
    Then, it runs the scrapers and does the same. 
    """

    with application.app_context():

        # Try a sample join to make sure that our
        # data_dir is good and add a helpful error message
        # when it's not.
        try:
            data_dir('rad_resource.csv')
        except:
            sys.exit('The source data directory is missing or invalid. ' \
                'This is typically due to a missing RAD_DATA_BASE environment variable.')

        # Load all the resources' data as RadRecords.
        radrecords = get_radrecords(data_dir('rad_resource.csv'))

        # Now save every record
        map(lambda record: get_or_create_resource(db, record),
            radrecords)

        db.session.commit()

        # run all the scrapers
        run_scrapers(application)
