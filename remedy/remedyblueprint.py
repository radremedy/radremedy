"""
remedyblueprint.py

Contains the basic routes for the application and
helper methods employed by those routes.
"""

from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask.ext.login import login_required, current_user
from rad.models import Resource, Review, db
from pagination import Pagination
import rad.resourceservice
import rad.searchutils
from functools import wraps
from rad.forms import ContactForm, ReviewForm
import smtplib
import os 


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

def under_construction(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return render_template('under-construction.html')
    return decorated_function

remedy = Blueprint('remedy', __name__)


@remedy.route('/')
def index():
    return render_template('index.html', 
        recently_added=latest_added(3),
        recent_discussion=latest_reviews(20))


@remedy.route('/resource/')
def redirect_home():
    return redirect(url_for('.index'))


@remedy.route('/resource/<resource_id>/')
def resource(resource_id):
    """
    Gets information about a single resource.

    Args:
        resource_id: The ID of the resource to show.

    Returns:
        A templated resource information page (via provider.html).
        This template is provided with the following variables:
            provider: The specific provider to display.
    """

    return render_template('provider.html', provider=resource_with_id(resource_id),
                           form=ReviewForm())


@remedy.route('/find-provider/', defaults={'page': 1})
@remedy.route('/find-provider/page/<int:page>')
def resource_search(page):
    """
    Searches for resources that match the provided options
    and displays a page of search results.

    Args:
        search: The text to search on.
        id: The specific ID to filter on.
        addr: The text to display in the "Address" field.
            Not used for filtering.
        dist: The distance, in miles, to use for proximity-based searching.
        lat: The latitude to use for proximity-based searching.
        long: The longitude to use for proximity-based searching.
        page: The current page number. Defaults to 1.

    Returns:
        A templated set of search results (via find-provider.html). This
        template is provided with the following variables:
            pagination: The paging information to use.
            providers: The page of providers to display.
            search_params: The dictionary of normalized searching options.
    """

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


@remedy.route('/review', methods=['POST'])
@login_required
def new_review():
    """
    This function handles the creation of new reviews,
    if the review submitted is valid then we create
    a record in the database linking it to a Resource
    and a User.

    When something goes wrong in the validation the User
    is redirected to the home page. We should better
    discuss form UI stuff.

    If all is OK the user is redirected to the provider
    been reviewed.
    """

    form = ReviewForm()

    if form.validate_on_submit():

        r = Review(form.rating.data, form.description.data,
                   Resource.query.get(form.provider.data), user=current_user)

        db.session.add(r)
        db.session.commit()

        return redirect(url_for('remedy.resource', resource_id=form.provider.data))

    else:

        flash('Invalid review.')
        return redirect('/')


@remedy.route('/settings/')
@login_required
def settings():
    # TODO: stub

    return render_template('settings.html')


@remedy.route('/about/')
@under_construction
def about():
    pass

@remedy.route('/get-involved/')
@under_construction
def get_involved():
    pass 


@remedy.route('/submit-error/<resource_id>/', methods=['GET', 'POST'])
def submit_error(resource_id) :
    """
    Gets error submission form for a given resource. On a GET request it displays the form. 
    On a PUT request, it submits the form, after checking for errors. 

    Args:
        resource_id: The ID of the resource to report an error on.

    Returns:
        A form for reporting errors (via error.html).
        This template is provided with the following variables:
            resource: The specific resource to report an error on.
            form: the WTForm to use
    """
    form = ContactForm()
    resource = resource_with_id(resource_id)
    username = str(os.environ.get('RAD_EMAIL_USERNAME'))
    email = username + '@gmail.com'
    password = str(os.environ.get('RAD_EMAIL_PASSWORD'))
 
    if request.method == 'POST':
        if form.validate() == False:
            flash('Message field is required.')
            return render_template('error.html', resource=resource_with_id(resource_id), form=form)
        elif username is not None and password is not None:
            username = str(os.environ.get('RAD_EMAIL_USERNAME'))
            email = username + '@gmail.com'
            password = str(os.environ.get('RAD_EMAIL_PASSWORD'))

            if form.name.data == "" :
                form.name.data = "BLANK"
            if form.email.data == "" :
                form.email.data = "BLANK"

            msg = """
                From: %s <%s>
                Resource: %s <%s>
                %s
                """ % (form.name.data, form.email.data, resource.name,
                       "radremedy.org" + url_for('remedy.resource',
                                                 resource_id=resource_id), form.message.data)

            # The actual mail send
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(username,password)
            server.sendmail(email, email, msg)
            server.quit()

            return render_template('error-submitted.html')
        else :
            return render_template('error-submitted.html')

    elif request.method == 'GET':
        return render_template('error.html', resource=resource_with_id(resource_id), form=form)


