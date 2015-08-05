"""

resourceservice.py 

This module contains functionality for interacting with resource models in
the database.

"""

from sqlalchemy import *
from models import Resource, Category, Population, resourcecategory, resourcepopulation
import geoutils

def search(database, search_params=None, limit=0, order_by='last_updated desc'):
    """
    Searches for one or more resources in the database using the specified parameters.

    Args:
        database: The current database context.
        limit: The maximum number of results to return.
        search_params: The dictionary of searching parameters to use.
        order_by: The ordering to use.

    Returns:
        A list of all resources matching the specified filtering criteria.
    """

    # Make sure we have at least some searching parameters, or failing that,
    # at least some sort of limit
    if (search_params is None or len(search_params) == 0) and limit <= 0:
        return None

    # Set up our base query
    query = database.session.query(Resource)

    # Store if we have location searching, which we'll use in our sorting
    has_location = False

    # Make sure we have some searching parameters!
    if search_params is not None and len(search_params) > 0:

        # "id" parameter - search against specific resource ID
        if 'id' in search_params:
            query = query.filter(Resource.id == search_params['id'])

        if 'visible' in search_params:
            query = query.filter(Resource.visible == search_params['visible'])

        # "search" parameter - text search against name/description/categories
        if 'search' in search_params and not search_params['search'].isspace():
            search_like_str = '%' + search_params['search'] + '%'
            query = query.filter(or_(Resource.name.like(search_like_str), 
                Resource.description.like(search_like_str),
                Resource.organization.like(search_like_str),
                Resource.category_text.like(search_like_str)))

        # Category filtering - ensure at least one has been provided
        if 'categories' in search_params and len(search_params['categories']) > 0:
            query = query.filter(Resource.categories.any(
                Category.id.in_(search_params['categories'])))

        # Population filtering - ensure at least one has been provided
        if 'populations' in search_params and len(search_params['populations']) > 0:
            query = query.filter(Resource.populations.any(
                Population.id.in_(search_params['populations'])))

        # Location parameters ("lat", "long", "dist") - proximity filtering
        if 'dist' in search_params and \
            search_params['dist'] > 0 and \
            'lat' in search_params and \
            'long' in search_params:

            # Convert our overall distance value to kilometers
            dist_km = geoutils.miles2km(search_params['dist'])

            # Calculate our bounding box
            minLat, minLong, maxLat, maxLong = geoutils.boundingBox(search_params['lat'],
                search_params['long'], dist_km)

            # Now apply filtering against that bounding box
            query = query.filter(Resource.latitude >= minLat, Resource.latitude <= maxLat)
            query = query.filter(Resource.longitude >= minLong, Resource.longitude <= maxLong)

            # Indicate we have location searching
            has_location = True

    # Apply ordering. If we have location searching sort by distance.
    # We determine this by summing up the absolute value of the
    # differences between the resource and search latitudes/longitudes.
    # The absolute value prevents differences with opposing signs
    # from cancelling each other out.
    # Otherwise, sort by whatever's provided.
    if has_location:
        query = query.order_by(
            func.abs(Resource.latitude - search_params['lat']) +
            func.abs(Resource.longitude - search_params['long']))
    elif order_by is not None and not order_by.isspace():
        query = query.order_by(order_by)

    # Apply limiting
    if limit > 0:
        query = query.limit(limit)

    return query.all()

def save(database, resource):
    """
    Creates or modifies a resource.

    Args:
        database: The current database context.
        resource: The resource to save.

    Returns:
        A Boolean indicating if the operation succeeded.  If a pre-existing
        resource is being updated (as indicated by its ID) but it no longer
        exists in the database, the save will fail.
    """
    # TODO
    pass

def delete(database, resource_id):
    """
    Deletes a resource.

    Args:
        database: The current database context.
        resource_id: The ID of the resource to delete.

    Returns:
        A Boolean indicating if the operation succeeded.
    """     
    # TODO
    pass
