"""
db_fun.py 

This module contains helper functions for database entry creation. 
"""

from models import Resource, Category
from datetime import datetime


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return False, instance
    else:
        instance = model(**kwargs)
        return True, instance


def add_get_or_create(database, model, **kwargs):
    new_record, record = get_or_create(database.session, model, **kwargs)
    database.session.add(record)

    return new_record, record


def get_or_create_resource(database, rad_record, lazy=True):
    """
    Checks to see if a record already exists in the database. If not, the new record is added. 

    Args: 
        database: copy of the database in the current contect 
        rad_record: the record to be added. Must be in the RAD record format
        lazy: if false, forces record to be added, even if it is a duplicate. Defaults to true
    """

    new_record, record = get_or_create(database.session, Resource, name=rad_record.name.strip())

    record.last_updated = datetime.utcnow()

    if new_record:
        record.date_created = datetime.utcnow()

    if new_record or not lazy:

        # See if we have just a normal address field - if not,
        # manually construct one by joining all available
        # fields with commas
        if hasattr(rad_record, 'address') and \
            rad_record.address is not None and \
            not rad_record.address.isspace():

            record.address = rad_record.address.strip()
        else:
            record.address = ", ".join(a for a in [rad_record.street,
                                    rad_record.city, rad_record.state,
                                    rad_record.zipcode, rad_record.country]
                                    if a is not None and not
                                    a.isspace())

        # Copy over all the other fields verbatim
        record.organization = rad_record.organization
        record.description = rad_record.description

        record.email = rad_record.email
        record.phone = rad_record.phone
        record.fax = rad_record.fax
        record.url = rad_record.url

        record.source = rad_record.source
        record.visible = rad_record.visible

        # Do we have a list of category names?
        # Failing that, do we have a single category name?
        if hasattr(rad_record, 'category_names') and \
            rad_record.category_names is not None and \
            len(rad_record.category_names) > 0:

            for category_name in rad_record.category_names:

                # Try to look up the name of the provided category,
                # get/create as necessary and add the record
                new_category, category_record = add_get_or_create(database, Category,
                                                              name=category_name.strip())

                record.categories.append(category_record)               

        elif hasattr(rad_record, 'category_name') and \
            rad_record.category_name is not None and \
            not rad_record.category_name.isspace():

            # Try to look up the name of the provided category,
            # get/create as necessary and add the record
            new_category, category_record = add_get_or_create(database, Category,
                                                              name=rad_record.category_name.strip())

            record.categories.append(category_record)

        database.session.add(record)

    return new_record, record

