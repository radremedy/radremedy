from flask import Blueprint, render_template, redirect, url_for, request, abort
from rad.models import Resource, Review, db
from pagination import Pagination
import rad.resourceservice
import rad.searchutils

PER_PAGE = 15


def get_paged_data(data, page, page_size=PER_PAGE):
    """
    Filters down a list of data to a specific page and returns
    the total count and the paged subset.  If there is no data
    provided, and a page other than the first is specified, the
    request will abort with 404 Not Found.

    Args:
        data: The data to filter down to a paged subset.
        page: The page number to use, starting with 1. If a value
            less than 1 is provided, the request will abort
            with 400 Bad Request.
        page_size: The page size to use, defaulted to PER_PAGE.

    Returns
        The total number of items in the list and the paged
        subset, in that order.
    """
    # Sanity check for page number
    if page < 1:
        abort(400)

    # Now make sure we're not paging too far
    if not data and page != 1:
        abort(404)

    start_index = (page-1)*page_size

    return len(data), data[start_index:start_index + page_size]


def url_for_other_page(page):
    """
    Generates a URL for the same page, with the only difference
    being that a new "page" query string value is updated
    with the provided page number.

    Args:
        page: The new page number to use.

    Returns:
        The URL for the current page with a new page number.
    """
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def latest_added(n):
    """
    Returns the latest n resources added to the database.

    Args:
        n: The number of resources to return.

    Returns:
        A list of resources from the database.
    """
    return rad.resourceservice.search(db, limit=n,
        search_params=dict(visible=True),
        order_by='date_created desc')


def latest_reviews(n):
    """
    Returns the latest n reviews added to the database.

    Args:
        n: The number of reviews to return.

    Returns:
        A list of reviews from the database.
    """
    # TODO: Update with review service
    return Review.query.order_by(Review.date_created.desc()).limit(n).all()


def resource_with_id(id):
    """
    Returns a resource from the database or aborts with a
    404 Not Found if it was not found.

    Args:
        id: The ID of the resource to retrieve.

    Returns:
        The specified resource.
    """
    result = rad.resourceservice.search(db, limit=1, search_params=dict(id=id))

    if result:
        return result[0]
    else:
        abort(404)

remedy = Blueprint('remedy', __name__)


@remedy.route('/')
def index():
    return render_template('index.html', 
        recently_added=latest_added(20),
        recent_discussion=latest_reviews(20))


@remedy.route('/resource/')
def redirect_home():
    return redirect(url_for('.index'))


@remedy.route('/resource/<resource_id>/')
def resource(resource_id):
    return render_template('provider.html', provider=resource_with_id(resource_id))


@remedy.route('/find-provider/', defaults={'page': 1})
@remedy.route('/find-provider/page/<int:page>')
def resource_search(page):
    # Start building out the search parameters.
    # At a minimum, we want to ensure that we only show visible resources.
    search_params = dict(visible=True)

    # Search string
    rad.searchutils.add_string(search_params, 'search', request.args.get('search'))

    # ID - minimum value of 1
    rad.searchutils.add_int(search_params, 'id', request.args.get('id'), min_value=1)

    # Address string - just used for display
    rad.searchutils.add_string(search_params, 'addr', request.args.get('addr'))

    # Distance - minimum value of 1, maximum value of 500 (miles)
    rad.searchutils.add_float(search_params, 'dist', request.args.get('dist'), min_value=1, max_value=500)

    # Latitude/longitude - no min/max values
    rad.searchutils.add_float(search_params, 'lat', request.args.get('lat'))
    rad.searchutils.add_float(search_params, 'long', request.args.get('long'))

    # Normalize our location-based searching params -
    # if dist/lat/long is missing, make sure they're all cleared
    if 'addr' not in search_params or \
        'dist' not in search_params or \
        'lat' not in search_params or \
        'long' not in search_params:
        search_params.pop('addr', None)
        search_params.pop('dist', None)
        search_params.pop('lat', None)
        search_params.pop('long', None)

    # All right - time to search!
    providers = rad.resourceservice.search(db, search_params=search_params)

    # Set up our pagination and render out the template.
    count, paged_providers = get_paged_data(providers, page)
    pagination = Pagination(page, PER_PAGE, count)

    return render_template('find-provider.html',
        pagination=pagination,
        providers=paged_providers,
        search_params=search_params
    )


@remedy.route('/login/')
def login():
    return render_template('login.html')


@remedy.route('/signup/')
def sign_up():
    return render_template('create-account.html')


@remedy.route('/settings/')
def settings():
    # TODO: stub
    stub = {'user': {'username': 'Doctor Who',
                     'email': 'doctorwho@gmail.com',
                     'gender_identity': 'unknown',
                     'preferred_pronouns': 'Dr.',
                     'password': '?????Should we really show a password??????'}}

    return render_template('settings.html', **stub)
