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

    new_record, record = get_or_create(database.session, Resource, name=rad_record.name)

    record.last_updated = datetime.utcnow()

    if new_record:
        record.date_created = datetime.utcnow()

    if new_record or not lazy:
        record.street = rad_record.street
        record.city = rad_record.city
        record.state = rad_record.state
        record.country = rad_record.country
        record.zipcode = rad_record.zipcode
        record.email = rad_record.email
        record.phone = rad_record.phone
        record.fax = rad_record.fax
        record.url = rad_record.url
        record.description = rad_record.description
        record.source = rad_record.source
        record.visable = rad_record.visible

        new_category, category_record = add_get_or_create(database, Category,
                                                          name=rad_record.category_name)

        record.category = category_record

        database.session.add(record)

    return new_record, record

