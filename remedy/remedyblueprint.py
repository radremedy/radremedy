"""
remedyblueprint.py

Contains the basic routes for the application and
helper methods employed by those routes.
"""

from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask.ext.login import login_required, current_user
from functools import wraps

from pagination import Pagination

from .email_utils import send_resource_error
from rad.models import Resource, Review, Category, db
from rad.forms import ContactForm, ReviewForm, UserSettingsForm
import rad.resourceservice
import rad.reviewservice
import rad.searchutils

import os 

PER_PAGE = 15


def flash_errors(form):
    """
    Flashes errors for the provided form.

    Args:
        form: The form for which errors will be displayed.
    """
    for field, errors in form.errors.items():
        for error in errors:
            flash("%s field - %s" % (
                getattr(form, field).label.text,
                error
            ))


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
    # Get reviews that aren't superseded,
    # and ensure that only visible reviews are included
    reviews = db.session.query(Review). \
        join(Review.resource). \
        filter(Review.is_old_review == False). \
        filter(Review.visible == True). \
        filter(Resource.visible == True). \
        order_by(Review.date_created.desc())

    return reviews.limit(n).all()


def active_categories():
    """
    Returns all active categories in the database.

    Returns:
        A list of categories from the database.
    """
    return Category.query.filter(Category.visible == True).order_by(Category.name).all()


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


def resource_redirect(id):
    """
    Returns a redirection action to the specified resource.

    Args:
        id: The ID of the resource to redirect to.

    Returns:
        The redirection action.
    """
    return redirect(url_for('remedy.resource', resource_id=id))


def under_construction(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return render_template('under-construction.html')
    return decorated_function

remedy = Blueprint('remedy', __name__)


@remedy.route('/')
def index():
    """
    Displays the front page.

    Returns:
        A templated front page (via index.html).
        This template is provided with the following variables:
            recently_added: The most recently-added visible
                resources.
            recent_discussion: The most recently-added visible
                reviews.
            categories: A list of all active categories.
    """
    return render_template('index.html', 
        recently_added=latest_added(3),
        recent_discussion=latest_reviews(20),
        categories=active_categories())


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
            reviews: The top-level reviews for this resource.
                Visible old reviews will be stored as an
                old_reviews_filtered field on each review.
            has_existing_review: A boolean indicating if the
                current user has already left a review for
                this resource.
            form: A ReviewForm instance for submitting a
                new review.
    """
    resource = resource_with_id(resource_id)
    reviews = resource.reviews. \
        filter(Review.is_old_review==False). \
        filter(Review.visible == True). \
        all()

    has_existing_review = False

    for rev in reviews:
        # Filter down old to only the visible ones,
        # and add appropriate sorting
        rev.old_reviews_filtered = rev.old_reviews. \
            filter(Review.visible==True). \
            order_by(Review.date_created.desc()) \
            .all()

        # If this belongs to the current user, indicate
        # that we have existing reviews on this item
        if current_user.is_authenticated() and rev.user.id == current_user.id:
            has_existing_review = True

    return render_template('provider.html', 
        provider=resource,
        reviews=reviews,
        has_existing_review = has_existing_review,
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
            categories: A list of all active categories.
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

    # Categories - this is a MultiDict so we need to use GetList
    rad.searchutils.add_int_set(search_params, 'categories', request.args.getlist('categories'))

    # All right - time to search!
    providers = rad.resourceservice.search(db, search_params=search_params)

    # Load up available categories
    categories = active_categories()

    # Set up our pagination and render out the template.
    count, paged_providers = get_paged_data(providers, page)
    pagination = Pagination(page, PER_PAGE, count)

    return render_template('find-provider.html',
        pagination=pagination,
        providers=paged_providers,
        search_params=search_params,
        categories=categories
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

        new_r = Review(form.rating.data, form.description.data,
                   Resource.query.get(form.provider.data), 
                   user=current_user)

        db.session.add(new_r)

        # Flush the session so we get an ID
        db.session.flush()

        # See if we have other existing reviews
        existing_reviews = Review.query. \
            filter(Review.id != new_r.id). \
            filter(Review.resource_id == new_r.resource_id). \
            filter(Review.user_id == new_r.user_id). \
            all()

        # If we do, mark all those old reviews as old
        if len(existing_reviews) > 0:
            for old_review in existing_reviews:
                old_review.is_old_review = True
                old_review.new_review_id = new_r.id

        db.session.commit()

        flash('Review submitted!')

        return resource_redirect(new_r.resource_id)
    else:
        flash_errors(form)

        # Try to see if we can get the resource ID and at least
        # go back to the form
        try:
            resource_id = int(form.provider.data)
            return resource_redirect(resource_id)
        except:
            return redirect('/')


@remedy.route('/delete-review/<review_id>', methods=['GET','POST'])
@login_required
def delete_review(review_id):
    """
    Handles the deletion of new reviews.

    Args:
        review_id: The ID of the review to delete.

    Returns:
        When accessed via GET, a form to confirm deletion (via find-provider.html). 
        This template is provided with the following variables:
            review: The review being deleted.
        When accessed via POST, a redirection action to the associated resource
        after the review has been deleted.
    """
    review = Review.query.filter(Review.id == review_id).first()

    # Make sure we got one
    if review is None:
        abort(404)

    # Make sure we're an admin or the person who actually submitted it
    if not current_user.admin and current_user.id != review.user_id:
        flash('You do not have permission to delete this review.')
        return resource_redirect(review.resource_id)

    if request.method == 'GET':
        # Return the view for deleting reviews
        return render_template('delete-review.html',
            review = review)
    else:
        rad.reviewservice.delete(db.session, review)
        flash('Review deleted.')
        return resource_redirect(review.resource_id)


@remedy.route('/settings/', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Gets the settings for the current user.
    On a GET request it displays the user's information and a form for
        changing profile options.
    On a POST request, it submits the form, after checking for errors.

    Returns:
        The user's settings (via settings.html).
        This template is provided with the following variables:
            form: The WTForm to use for changing profile options.
    """
    # Prefill with existing user settings
    form = UserSettingsForm(request.form, current_user)

    if request.method == 'GET':
        return render_template('settings.html',
            form = form)
    else:
        if form.validate_on_submit():

            # Update the user's settings
            current_user.email = form.email.data
            current_user.display_name = form.display_name.data

            current_user.default_location = form.default_location.data
            current_user.default_latitude = form.default_latitude.data
            current_user.default_longitude = form.default_longitude.data

            db.session.commit()

            flash('Your profile has been updated!')

        else:
            # Flash any errors
            flash_errors(form)

        return render_template('settings.html',
            form = form)


@remedy.route('/about/')
def about():
    return render_template('about.html')

@remedy.route('/get-involved/')
def get_involved():
    return render_template('get-involved.html')

@remedy.route('/how-to-use/')
@under_construction
def how_to_use():
    pass 

@remedy.route('/contact/')
def contact():
    return render_template('contact.html') 

@remedy.route('/projects/')
def projects():
    return render_template('projects.html')

@remedy.route('/donate/')
def donate():
    return render_template('donate.html') 


@remedy.route('/submit-error/<resource_id>/', methods=['GET', 'POST'])
def submit_error(resource_id) :
    """
    Gets error submission form for a given resource.
    On a GET request it displays the form. 
    On a POST request, it submits the form, after checking for errors. 

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
 
    if request.method == 'POST':
        if form.validate() == False:
            flash('Message field is required.')
            return render_template('error.html', resource=resource, form=form)
        else:
            send_resource_error(resource, form.message.data)
            return render_template('error-submitted.html')

    elif request.method == 'GET':
        return render_template('error.html', resource=resource, form=form)


