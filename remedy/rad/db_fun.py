"""
db_fun.py 

This module contains helper functions for database entry creation. 
"""

from models import Resource, Category, Population
from datetime import datetime


def get_or_create(session, model, **kwargs):
    """
    Determines if a given record already exists in the database.

    Args:
        session: The database session.
        model: The model for the record.
        **kwargs: The properties to set on the model. The first
            specified property will be used to determine if
            the model already exists.

    Returns:
        Two values. The first value is a boolean
        indicating if this item is a new record. The second
        value will be the created/retrieved model.
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return False, instance
    else:
        instance = model(**kwargs)
        return True, instance


def add_get_or_create(session, model, **kwargs):
    """
    Gets or creates an record based on if it already exists.
    If it does not already exist, it will be created.

    Args:
        session: The database session.
        model: The model to get or create.
        **kwargs: The properties to set on the model. The first
            specified property will be used to determine if
            the model already exists.

    Returns:
        Two values. The first value is a boolean
        indicating if this item is a new record. The second
        value will be the created/retrieved model.
    """
    new_record, record = get_or_create(session, model, **kwargs)

    if new_record:
        session.add(record)

    return new_record, record


def try_add_categories(session, record, category_names, create_categories=True):
    """
    Attempts to add the list of provided categories to the resource.

    Args: 
        session: The current database context. 
        record: The resource to update.
        category_names: The list of category names to add.
        create_categories: If true, will create categories if they don't already exist.
            If false, will skip over listed categories that don't already exist. 
            Defaults to true.
    """
    for category_name in category_names:
        normalized_name = category_name.strip()

        # Are we allowing categories to be created?
        if create_categories:
            # Try to look up the name of the provided category,
            # get/create as necessary
            new_category, category_record = add_get_or_create(session, 
                Category,
                name=normalized_name)
        else:
            # Only look up the category - return None
            # if we don't have one
            category_record = session.query(Category). \
                filter(Category.name == normalized_name). \
                first()

        # Make sure we got something back and we're not double-adding
        if category_record and not category_record in record.categories:
            record.categories.append(category_record)    


def try_add_populations(session, record, population_tags):
    """
    Attempts to add the list of provided populations to the resource.

    Args: 
        session: The current database context. 
        record: The resource to update.
        population_tags: The list of population names to add.
    """
    for population_name in population_tags:
        normalized_name = population_name.strip()

        # FUTURE: Support adding populations on the fly
        # Look up the population - return None
        # if we don't have one
        population_record = session.query(Population). \
            filter(Population.name == normalized_name). \
            first()

        # Make sure we got something back and we're not double-adding
        if population_record and not population_record in record.populations:
            record.populations.append(population_record)


def get_or_create_resource(session, rad_record, lazy=True, create_categories=True):
    """
    Checks to see if a resource already exists in the database
    and adds it if it does not exist (or is forced to by use of
    the lazy argument).

    Args: 
        session: The current database session. 
        rad_record: The RadRecord to be added.
        lazy: If false, forces the record to be added even if it is a duplicate. 
            Defaults to true.
        create_categories: If true, will create categories if they don't already exist.
            If false, will skip over listed categories that don't already exist. 
            Defaults to true.

    Returns:
        Two values. The first value is a boolean
        indicating if a new record was created. The second
        value will be the created/updated model.
    """
    # Just create a new record always if we're lazy-loading. This avoids
    # weirdness in which we're partially updating an item.
    if lazy:
        new_record = True
        record = Resource(name=rad_record.name.strip())
        session.add(record)
    else:
        new_record, record = get_or_create(session, Resource, name=rad_record.name.strip())

    record.last_updated = datetime.utcnow()

    if new_record:
        record.date_created = datetime.utcnow()

    if new_record or not lazy:

        # See if we have just a normal address field - if not,
        # manually construct one by joining all available
        # fields with commas
        new_address = ''
        if hasattr(rad_record, 'address') and \
            rad_record.address is not None and \
            rad_record.address != '' and \
            not rad_record.address.isspace():

            new_address = rad_record.address.strip()
        else:
            new_address = ", ".join(a.strip() for a in [rad_record.street,
                                    rad_record.city, rad_record.state,
                                    rad_record.zipcode, rad_record.country]
                                    if a is not None and a != '' and not a.isspace())

        # Address issue 131 - if we're updating an existing
        # record, and are changing the address (using a lowercase comparison),
        # invalidate the existing geocoding information.
        if not new_record and \
            record.address is not None and \
            record.address.lower() != new_address.lower():
            record.latitude = None
            record.longitude = None
            record.location = None

        # Now set the new address
        if new_address != '' and not new_address.isspace():
            record.address = new_address
        else:
            record.address = None

        # Try to parse out the date_verified field if it's provided
        if rad_record.date_verified is not None and \
            len(rad_record.date_verified) > 0 and \
            not rad_record.date_verified.isspace():
            # Try to parse it out using 'YYYY-MM-DD'
            try:
                record.date_verified = datetime.strptime(rad_record.date_verified, 
                    '%Y-%m-%d').date()
            except ValueError:
                # Parsing error, clear it out
                record.date_verified = None
        else:
            # Not provided - clear it out
            record.date_verified = None

        # Copy over all the other fields verbatim
        record.organization = rad_record.organization
        record.description = rad_record.description

        record.email = rad_record.email
        record.phone = rad_record.phone
        record.fax = rad_record.fax
        record.url = rad_record.url
        record.hours = rad_record.hours
        record.hospital_affiliation = rad_record.hospital_affiliation

        record.source = rad_record.source
        record.npi = rad_record.npi
        record.notes = rad_record.notes

        record.is_icath = rad_record.is_icath
        record.is_wpath = rad_record.is_wpath
        record.is_accessible = rad_record.wheelchair_accessible
        record.has_sliding_scale = rad_record.sliding_scale
        
        record.visible = rad_record.visible

        # Do we have a list of category names?
        # Failing that, do we have a single category name?
        if hasattr(rad_record, 'category_names') and \
            rad_record.category_names is not None and \
            len(rad_record.category_names) > 0:

            # Use the list of category names
            try_add_categories(session, record, rad_record.category_names, create_categories)

        elif hasattr(rad_record, 'category_name') and \
            rad_record.category_name is not None and \
            not rad_record.category_name.isspace():

            # Use the single category name
            try_add_categories(session, record, [rad_record.category_name], create_categories)

        # Do we have a list of population tags?
        if hasattr(rad_record, 'population_tags') and \
            rad_record.population_tags is not None and \
            len(rad_record.population_tags) > 0:

            try_add_populations(session, record, rad_record.population_tags)

        session.add(record)

        # Flush the session because otherwise we won't pick up
        # duplicates with UNIQUE constraints (such as in category names) 
        # until we get an error trying to commit such duplicates
        # (which is bad)
        session.flush()

    return new_record, record

