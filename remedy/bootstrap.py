import os
from toolz import partial
from rad.db_fun import add_get_or_create, get_or_create_resource
from radremedy import app, db, Category, Resource
from get_save_data import run as run_scrapers
from data_importer.data_importer import seconds, open_dict_csv, open_csv

# TODO: document runtime config
BASE_DATA_DIR = os.environ['RAD_DATA_BASE']
data_dir = partial(os.path.join, BASE_DATA_DIR)


def minus_key(d, k):
    d.pop(k)
    return d

if __name__ == '__main__':

    db.init_app(app)

    with app.app_context():

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
        map(lambda row: get_or_create_resource(db, **row),
            raw_resources)

        db.session.commit()

        # run all the scrapers
        run_scrapers()
