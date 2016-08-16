"""
resourceservice.py

This module contains functionality for interacting with resource models in
the database.
"""

from sqlalchemy import *
from models import Resource, Category, Population, ResourceReviewScore
import geoutils


def search(
        search_params=None,
        limit=0,
        page_size=0,
        page_number=0):
    """
    Searches for one or more resources in the database
    using the specified parameters.

    Args:
        database: The current database context.
        search_params: The dictionary of searching parameters to use.
        limit: The maximum number of results to return.
        page_size: The size of each page when using paged queries.
        page_number: The 1-indexed page number when using paged queries.

    Returns:
        A list of all resources matching the specified filtering criteria.
        If the page_size is specified, will wrap the results in a
        Pagination object.
    """

    # Make sure we have at least some searching parameters, or failing that,
    # at least some sort of limit
    if (search_params is None or len(search_params) == 0) and limit <= 0:
        return None

    # Determine we have location searching, which we'll use in our sorting/
    # filtering as appropriate
    has_location = False

    if 'dist' in search_params \
            and search_params['dist'] > 0 \
            and 'lat' in search_params \
            and'long' in search_params:
        has_location = True

    # Set up our base query
    query = Resource.query. \
        outerjoin(Resource.overall_aggregate)

    # Make sure we have some searching parameters!
    if search_params is not None and len(search_params) > 0:

        # "id" parameter - search against specific resource ID
        if 'id' in search_params:
            query = query.filter(
                Resource.id == search_params['id'])

        # "visible" parameter - treat as a flag
        if 'visible' in search_params:
            query = query.filter(
                Resource.visible == search_params['visible'])

        # "is_approved" parameter - treat as a flag
        if 'is_approved' in search_params:
            query = query.filter(
                Resource.is_approved == search_params['is_approved'])

        # "icath" parameter - treat as a flag
        if 'icath' in search_params:
            query = query.filter(
                Resource.is_icath == search_params['icath'])

        # "wpath" parameter - treat as a flag
        if 'wpath' in search_params:
            query = query.filter(
                Resource.is_wpath == search_params['wpath'])

        # "wheelchair_accessible" parameter - treat as a flag
        if 'wheelchair_accessible' in search_params:
            query = query.filter(
                Resource.is_accessible ==
                search_params['wheelchair_accessible'])

        # "sliding_scale" parameter - treat as a flag
        if 'sliding_scale' in search_params:
            query = query.filter(
                Resource.has_sliding_scale ==
                search_params['sliding_scale'])

        # "search" parameter - text search against
        # name/description/keywords fields
        if 'search' in search_params and \
                not search_params['search'].isspace():

            search_like_str = '%' + search_params['search'] + '%'
            query = query.filter(or_(
                Resource.name.like(search_like_str),
                Resource.description.like(search_like_str),
                Resource.organization.like(search_like_str),
                Resource.category_text.like(search_like_str)))

        # Category filtering - ensure at least one has been provided
        if 'categories' in search_params and \
                len(search_params['categories']) > 0:
            query = query.filter(Resource.categories.any(
                Category.id.in_(search_params['categories'])))

        # Population filtering - ensure at least one has been provided
        if 'populations' in search_params and \
                len(search_params['populations']) > 0:
            query = query.filter(Resource.populations.any(
                Population.id.in_(search_params['populations'])))

        # Location parameters ("lat", "long", "dist") - proximity filtering
        if has_location:

            # Convert our overall distance value to kilometers
            dist_km = geoutils.miles2km(search_params['dist'])

            # Calculate our bounding box
            minLat, minLong, maxLat, maxLong = geoutils.boundingBox(
                search_params['lat'],
                search_params['long'],
                dist_km)

            # Now apply filtering against that bounding box
            query = query.filter(
                Resource.latitude >= minLat, Resource.latitude <= maxLat)
            query = query.filter(
                Resource.longitude >= minLong, Resource.longitude <= maxLong)

    # Apply ordering. Distance is handled near the end so that
    # we can assume that it's either not specified or explicitly
    # specified as distance at that point.
    order_by = search_params.get('order_by')

    if order_by == 'name':
        query = query.order_by(Resource.name)
    elif order_by == 'modified':
        query = query.order_by(Resource.last_updated.desc())
    elif order_by == 'created':
        query = query.order_by(Resource.date_created.desc())
    elif order_by == 'rating':
        query = query.order_by(
            ResourceReviewScore.rating_avg.desc(),
            ResourceReviewScore.num_ratings.desc(),
            ResourceReviewScore.last_reviewed.desc(),
            Resource.last_updated.desc())
    elif has_location:
        # We determine this by summing up the absolute value of the
        # differences between the resource and search latitudes/longitudes.
        # The absolute value prevents differences with opposing signs
        # from cancelling each other out.
        query = query.order_by(
            func.abs(Resource.latitude - search_params['lat']) +
            func.abs(Resource.longitude - search_params['long']))
    else:
        # Fall back to last-modified descending
        query = query.order_by(Resource.last_updated.desc())

    # Apply limiting
    if limit > 0:
        query = query.limit(limit)

    if page_size > 0:
        return query.paginate(page_number, per_page=page_size)
    else:
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
