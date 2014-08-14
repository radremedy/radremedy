"""
bootstrap.py 

Imports data from database files and from the scrapers. 
"""
from rad.db_fun import add_get_or_create, get_or_create_resource
from rad.models import Category
from radremedy import create_app, db
from get_save_data import run as run_scrapers
from data_importer.data_importer import seconds, open_dict_csv, open_csv, minus_key, data_dir
from radrecord import rad_record


if __name__ == '__main__':
    """
    First, this function runs the data importers and adds them to the database.
    Then, it runs the scrapers and does the same. 
    """

    application, _ = create_app('config.BaseConfig')

    with application.app_context():

        # create all the different categories for the providers
        # we do this separately for clarity but we don't have to
        # they would automatically be created when importing
        # the rest of the data
        categories = seconds(open_csv(data_dir('rad_resource.csv')))

        # we commit on every record because they have to be unique
        map(lambda c: add_get_or_create(db, Category, name=c) and db.session.commit(),
            categories)

        # load all the resources' data, but we drop the id
        # column because our database will assign them on its own
        raw_resources = map(lambda row: minus_key(row, 'id'),
                            open_dict_csv(data_dir('rad_resource.csv')))

        # then we save every record
        map(lambda row: get_or_create_resource(db, rad_record(**row)),
            raw_resources)

        db.session.commit()

        # run all the scrapers
        run_scrapers()
