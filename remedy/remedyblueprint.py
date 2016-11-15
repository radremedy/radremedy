"""
remedyblueprint.py

Contains the basic routes for the application and
helper methods employed by those routes.
"""
from datetime import datetime, timedelta

from flask import Blueprint, Response, render_template, redirect, url_for, \
    request, abort, flash, send_from_directory
from flask.json import dumps
from flask.ext.login import login_required, current_user
from werkzeug.contrib.cache import SimpleCache
from werkzeug.datastructures import MultiDict
from functools import wraps

from sqlalchemy import or_

from flask.ext.sqlalchemy import Pagination

from .remedy_utils import get_ip, get_field_args, get_nl2br, get_phoneintl, \
    flash_errors, get_grouped_flashed_messages
from .email_utils import send_resource_error
from rad.models import News, Resource, Review, Category, Population, \
    ResourceReviewScore, CategoryGroup, db
from rad.forms import ContactForm, UserSubmitProviderForm, ReviewForm, \
    UserSettingsForm
import rad.resourceservice
import rad.reviewservice
import rad.searchutils

from operator import attrgetter

from jinja2 import evalcontextfilter, Markup

import os

PER_PAGE = 20

# Set up a basic in-memory cache
cache = SimpleCache()


def get_json_response(data):
    """
    Returns the JSON-formatted version of the provided data.
    This is a compatibility workaround until we get onto
    flask v0.11, in which case we can use jsonify.

    Args:
        data: The data to return as JSON.

    Returns
        A response containing the appropriate JSON.
    """
    # TODO: Remove this once we're on flask v0.11
    # as we can just use jsonify then. We need to
    # use this to return simple arrays in the mean time.
    return Response(
        dumps(data),
        status=200,
        mimetype='application/json')


def url_for_other_page(page, anchor=None):
    """
    Generates a URL for the same page, with the only difference
    being that a new "page" query string value is updated
    with the provided page number.

    Args:
        page: The new page number to use.
        anchor: The anchor to use in the URL. Optional.

    Returns:
        The URL for the current page with a new page number.
    """
    args = dict(request.view_args.items() + request.args.to_dict().items())
    args['page'] = page

    # Handle anchors if specified
    if anchor is not None:
        args['_anchor'] = anchor

    return url_for(request.endpoint, **args)


def get_sorted_options(optionlist):
    """
    Gets sorted options (ID/name tuples) from the provided list,
    sorting by name.

    Args:
        optionlist: The options to sort and convert. Assumes
            the existence of "id" and "name" properties.

    Returns:
        A sorted list of ID/name tuples from the provided option list.
    """
    return [(o.id, o.name) for o in sorted(optionlist, key=attrgetter('name'))]


def make_grouping(flatlist):
    """
    Gets a grouped list of items from the provided flat list.
    Each item will be grouped by its "grouping" property (as identified by
    "grouping_id") and then sorted by name.

    Items without a group will go in at the top. After that,
    the groups will be sorted by "grouporder" and then by "name" and
    the items within them will be sorted by name.

    The returned result will start with ID/name tuples of any
    top-level items, and then follow with group tuples,
    which consist of a name and a list of the equivalent
    ID/name tuples within that group.

    Args:
        flatlist: The flat list of items to group.

    Returns:
        A grouped list of items.
    """

    # Set up our group dictionary and list of top items
    groups_dict = MultiDict()
    top_items = []

    # Classify each item appropriately
    for item in flatlist:
        if item.grouping_id is None:
            top_items.append(item)
        else:
            groups_dict.add(item.grouping, item)

    # Kickstart our grouped result with the top-level options.
    grouped_result = get_sorted_options(top_items)

    # Get the groups in the MultiDict - first sorted by name (innermost)
    # and finally by grouporder (outermost)
    sorted_groups = sorted(
        sorted(groups_dict.keys(), key=attrgetter('name')),
        key=attrgetter('grouporder'))

    for grouping in sorted_groups:
        # Convert the group to a tuple - the first item
        # is the group name and the second is the equivalent
        # options in that group.
        grouped_result.append((
            grouping.name,
            get_sorted_options(groups_dict.getlist(grouping))))

    return grouped_result


def active_categories():
    """
    Returns all active categories in the database.

    Returns:
        A list of categories from the database.
    """
    return Category.query.filter(Category.visible == True). \
        order_by(Category.name).all()


def group_active_categories(categories):
    """
    Converts the provided category list into
    groupings suitable for use in a form.

    Args:
        categories: The flat list of categories.

    Returns:
        A grouped list of categories. See make_grouping
        for more information about the specific format.
    """
    return make_grouping(categories)


def active_populations():
    """
    Returns all active populations in the database.

    Returns:
        A list of populations from the database.
    """
    return Population.query.filter(Population.visible == True). \
        order_by(Population.name).all()


def group_active_populations(populations):
    """
    Converts the provided population list into
    groupings suitable for use in a form.

    Args:
        populations: The flat list of populations.

    Returns:
        A grouped list of populations. See make_grouping
        for more information about the specific format.
    """
    return make_grouping(populations)


def resource_with_id(id):
    """
    Returns a resource from the database or aborts with a
    404 Not Found if it was not found.

    Args:
        id: The ID of the resource to retrieve.

    Returns:
        The specified resource.
    """
    result = rad.resourceservice.search(
        limit=1,
        search_params={
            'id': id,
            'visible': True,
            'is_approved': True
        })

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


@remedy.context_processor
def context_override():
    """
    Overrides the behavior of url_for to include cache-busting
    timestamps for static files. Also registers the custom
    get_field_args and get_grouped_flashed_messages functions.

    Based on http://flask.pocoo.org/snippets/40/
    """
    return {
        "url_for": dated_url_for,
        "get_field_args": get_field_args,
        "get_grouped_flashed_messages": get_grouped_flashed_messages
    }


def dated_url_for(endpoint, **values):
    """
    Overrides the url_for behavior to include a
    timestamped "q" parameter to prevent caching of
    static resources.

    Based on http://flask.pocoo.org/snippets/40/

    Returns:
        The URL for the specified file at the indicated endpoint.
    """
    # Only do this for static files
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            # Get the full path to the file and look up the last-modified
            # time.
            file_path = os.path.join(remedy.root_path, 'static', filename)
            values['q'] = int(os.stat(file_path).st_mtime)

    return url_for(endpoint, **values)


@remedy.app_errorhandler(404)
def page_not_found(err):
    """
    Displays a 404 error page.

    Args:
        err: The encountered error.

    Returns:
        A templated 404 page (via 404.html).
    """
    return render_template('404.html'), 404


def server_error(err):
    """
    Displays a 500 server error page.

    Args:
        err: The encountered error.

    Returns:
        A templated 500 page (via 500.html).
        This template is provided with the following variables:
            current_user: The currently-logged in user.
            error_info: The encountered error.
    """
    return render_template(
        '500.html',
        current_user=current_user,
        error_info=err), 500


@remedy.app_template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value, make_urls=True):
    """
    Splits the provided string into paragraph tags based on the
    line breaks within it and returns the escaped result.

    Args:
        eval_ctx: The context used for filter evaluation.
        value: The string to process.
        make_urls: If True, will attempt to convert any URLs
            in the string to full links.

    Returns:
        The processed, escaped string.
    """
    result = get_nl2br(value, make_urls=make_urls)

    # Auto-escape if specified.
    if eval_ctx.autoescape:
        result = Markup(result)

    return result


@remedy.app_template_filter()
@evalcontextfilter
def phoneintl(eval_ctx, value):
    """
    Normalizes the provided phone number to a suitable
    international format.

    Args:
        eval_ctx: The context used for filter evaluation.
        value: The string to process.

    Returns:
        The processed phone number.
    """
    result = get_phoneintl(value)

    if eval_ctx.autoescape:
        result = Markup(result)

    return result


@remedy.route('/favicon.ico')
def favicon():
    """
    Returns the favicon.

    Returns:
        The favicon at static/img/favicon.ico with
        the appropriate MIME type.
    """
    return send_from_directory(
        os.path.join(remedy.root_path, 'static', 'img'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon')


@remedy.route('/robots.txt')
def robots_txt():
    """
    Returns the robots.txt file, if it exists.

    Returns:
        The robots file at robots/robots.txt with
        the appropriate MIME type.
    """
    robot_path = os.path.join(remedy.root_path, 'robots', 'robots.txt')

    if not os.path.exists(robot_path):
        abort(404)

    return send_from_directory(
        os.path.join(remedy.root_path, 'robots'),
        'robots.txt',
        mimetype='text/plain')


@remedy.route('/sitemap.xml')
def sitemap_xml():
    """
    Returns the sitemap.xml file, if it exists.

    Returns:
        The sitemap file at robots/sitemap.xml with
        the appropriate MIME type.
    """
    sitemap_path = os.path.join(remedy.root_path, 'robots', 'sitemap.xml')

    if not os.path.exists(sitemap_path):
        abort(404)

    return send_from_directory(
        os.path.join(remedy.root_path, 'robots'),
        'sitemap.xml',
        mimetype='application/xml')


@remedy.route('/')
def index():
    """
    Displays the front page.

    Returns:
        A templated front page (via index.html).
        This template is provided with the following variables:
            latest_news: Up to 3 of the most recent news posts
                made within the last month.
    """
    created_cutoff = datetime.utcnow() - timedelta(days=30)

    latest_news = db.session.query(News). \
        filter(News.visible == True). \
        filter(News.date_created >= created_cutoff). \
        order_by(News.date_created.desc()). \
        limit(3). \
        all()

    return render_template(
        'index.html',
        latest_news=latest_news)


@remedy.route('/news/', defaults={'page': 1})
@remedy.route('/news/page/<int:page>')
def news(page):
    """
    Displays a page of news posts.

    Args:
        page: The current page number. Defaults to 1.

    Returns:
        A templated set of search results (via news.html). This
        template is provided with the following variables:
            pagination: The paging information to use.
            news: The page of news posts to display.
    """
    # Use the Flask-SQLA pagination structure to handle this for us.
    # This will also handle if we've gone too far from a paging perspective.
    sqlpage = News.query. \
        filter(News.visible == True). \
        order_by(News.date_created.desc()). \
        paginate(page, per_page=10)

    return render_template(
        'news.html',
        news=sqlpage.items,
        pagination=sqlpage)


@remedy.route('/news/<int:news_id>/')
def news_item(news_id):
    """
    Displays a single news post.

    Args:
        news_id: The ID of the news post to show.

    Returns:
        A templated resource information page (via news-item.html).
        This template is provided with the following variables:
            news: The news post to display.
    """
    news_post = db.session.query(News). \
        filter(News.id == news_id). \
        filter(News.visible == True). \
        first()

    if news_post is None:
        abort(404)

    return render_template('news-item.html', news=news_post)


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
            overall_aggregate: The overall rating aggregates for the resource.
            identity_aggregates: The identity-specific aggregates for the
                resource, filtered down to the current user's active
                identities. Sorted first by the number of overall ratings
                (descending) then by the last-reviewed date (descending)
                and finally name (ascending). Not visible for logged-out users.
            user_review_date: The date/time the current user has last
                visibly reviewed the provider.
            user_review_pending: A boolean indicating if the current user's
                last review is not included in the aggregates.
    """
    # Get the resource and all visible top-level reviews
    resource = resource_with_id(resource_id)

    reviews = resource.reviews. \
        filter(Review.is_old_review == False). \
        filter(Review.visible == True). \
        all()

    # Store the date of an existing review by the user,
    # as well as if their latest review has been included
    # in the aggregates so far.
    user_review_date = None
    user_review_pending = False

    # Ensure the filtered set of old reviews is
    # available on each review we're displaying
    for rev in reviews:

        # See if the current user (if any) has reviewed this provider,
        # and if so, store the created date of that
        if current_user.is_authenticated and rev.user_id == current_user.id:
            user_review_date = rev.date_created

        # Filter down old to only the visible ones,
        # and add appropriate sorting
        rev.old_reviews_filtered = rev.old_reviews. \
            filter(Review.visible == True). \
            order_by(Review.date_created.desc()) \
            .all()

    # Get aggregate ratings if we have any reviews.
    aggregate_ratings = []
    overall_aggregate = None

    if len(reviews) > 0:
        # First see if the user's logged in
        if current_user.is_authenticated:
            # Get scores for their identities as well as the summary.
            # This also ensures foreign-key consistency in case a population
            # is deleted after aggregates have been calculated.
            user_pop_ids = [
                p.id
                for p in current_user.populations
                if p.visible
            ]
            user_pop_ids.append(0)

            aggregate_ratings = resource.aggregateratings \
                .filter(ResourceReviewScore.population_id.in_(user_pop_ids)) \
                .all()
        else:
            # Not logged in - only get summary
            aggregate_ratings = resource.aggregateratings \
                .filter(ResourceReviewScore.population_id == 0) \
                .all()

        # Find the top-level aggregate
        overall_aggregate = next(
            (r for r in aggregate_ratings if r.population_id == 0),
            None)

    # See if the user's latest review isn't included in the results.
    # This will be the case if we don't have any overall aggregate yet
    # or if that aggregate's latest date is earlier than the user's.
    if user_review_date is not None:
        if overall_aggregate is None:
            user_review_pending = True
        elif overall_aggregate.last_reviewed < user_review_date:
            user_review_pending = True

    # Filter down the list of identity-specific aggregates based on visibility.
    # For logged-out users, we can assume there will be none.
    identity_aggregates = []

    if current_user.is_authenticated:
        identity_aggregates = [
            r
            for r in aggregate_ratings
            if is_aggregate_visible(r, user_review_date)
        ]

        # Sort first by our innermost sort criteria - identity name.
        identity_aggregates.sort(key=attrgetter('population.name'))

        # Then sort by the last-reviewed date, in reverse
        # (so that latest show up at the top)
        identity_aggregates.sort(
            key=attrgetter('last_reviewed'),
            reverse=True)

        # Then sort by our outermost sort criteria - the number of reviews,
        # in reverse (so that highest show up at the top)
        identity_aggregates.sort(
            key=attrgetter('num_ratings'),
            reverse=True)

    return render_template(
        'provider.html',
        provider=resource,
        reviews=reviews,
        overall_aggregate=overall_aggregate,
        identity_aggregates=identity_aggregates,
        user_review_date=user_review_date,
        user_review_pending=user_review_pending)


def is_aggregate_visible(agg_rating, user_review_date):
    """
    Determines if an aggregate rating for a specific identity
    should be displayed to the current user.

    Args:
        agg_rating: The aggregate rating in question.
        user_review_date: The date the user last (visibly)
            reviewed the resource.

    Returns:
        A boolean indicating if the aggregate rating should be displayed.
    """
    # Filter out the overall aggregate.
    if agg_rating.population_id == 0:
        return False

    # If we have more than one rating, it's visible.
    if agg_rating.num_ratings > 1:
        return True

    # If the user hasn't reviewed the resource, it's visible.
    if user_review_date is None:
        return True

    # Similarly, if the user's review hasn't been incorporated,
    # it's visible.
    # Since we just checked for None above we can assume they've
    # reviewed it at some point.
    if user_review_date > agg_rating.last_reviewed:
        return True

    # Fall-through case. Basically, we're not showing the aggregate in the
    # event that the user is the sole reviewer of the resource -
    # verifying that is really more of a process of elimination
    # based on the conditions above.
    return False


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
        categories: The IDs of the categories to filter on.
        populations: The IDs of the populations to filter on.
        icath: The ICATH status (in the form of a 1/0 value) to filter on.
        wpath: The WPATH status (in the form of a 1/0 value) to filter on.
        wheelchair_accessible: The accessibility status
            (in the form of a 1/0 value) to filter on.
        sliding_scale: The sliding scale status
            (in the form of a 1/0 value) to filter on.
        dist: The distance, in miles, to use for proximity-based searching.
        lat: The latitude to use for proximity-based searching.
        long: The longitude to use for proximity-based searching.
        page: The current page number. Defaults to 1.
        autofill: If set, will attempt to automatically fill the
            proximity-based search fields with the current user's default
            location, defaulting to a distance of 25.

    Returns:
        A templated set of search results (via find-provider.html). This
        template is provided with the following variables:
            pagination: The paging information to use.
            providers: The page of providers to display.
            search_params: The dictionary of normalized searching options.
            has_params: A boolean indicating if any user-defined options
            were provided.
            grouped_categories: The grouped set of all active categories.
            grouped_populations: The grouped set of all active populations.
    """

    # Start building out the search parameters.
    # At a minimum, we want to ensure that we only show
    # visible/approved resources.
    search_params = {
        'visible': True,
        'is_approved': True
    }

    # Handle our ordering
    if request.args.get('order_by'):
        sort_options = (
            'name',
            'created',
            'modified',
            'distance',
            'rating'
        )

        # Validate it's something we allow
        if request.args.get('order_by') in sort_options:
            search_params['order_by'] = request.args.get('order_by')

    # Store the number of search parameters after baking in our filtering
    default_params_count = len(search_params)

    # If we're auto-filling, and the user is logged in, fill in their
    # location information
    try:
        if request.args.get('autofill', default=0, type=int) and \
                current_user.is_authenticated:

            rad.searchutils.add_string(
                search_params,
                'addr',
                current_user.default_location)

            rad.searchutils.add_float(
                search_params,
                'lat',
                current_user.default_latitude)

            rad.searchutils.add_float(
                search_params,
                'long',
                current_user.default_longitude)

            search_params['dist'] = 25
    except Exception:
        pass

    # Search string
    rad.searchutils.add_string(
        search_params,
        'search',
        request.args.get('search'))

    # ICATH
    rad.searchutils.add_bool(
        search_params,
        'icath',
        request.args.get('icath'))

    # WPATH
    rad.searchutils.add_bool(
        search_params,
        'wpath',
        request.args.get('wpath'))

    # ADA/Wheelchair Accessible
    rad.searchutils.add_bool(
        search_params,
        'wheelchair_accessible',
        request.args.get('wheelchair_accessible'))

    # Sliding Scale
    rad.searchutils.add_bool(
        search_params,
        'sliding_scale',
        request.args.get('sliding_scale'))

    # ID - minimum value of 1
    rad.searchutils.add_int(
        search_params,
        'id',
        request.args.get('id'),
        min_value=1)

    # Address string - just used for display
    rad.searchutils.add_string(
        search_params,
        'addr',
        request.args.get('addr'))

    # Distance - minimum value of -1 (anywhere),
    # maximum value of 500 (miles)
    rad.searchutils.add_float(
        search_params,
        'dist',
        request.args.get('dist'),
        min_value=-1,
        max_value=500)

    # Latitude/longitude - no min/max values
    rad.searchutils.add_float(
        search_params,
        'lat',
        request.args.get('lat'))

    rad.searchutils.add_float(
        search_params,
        'long',
        request.args.get('long'))

    # See if we have a valid location
    if 'addr' not in search_params or \
            'dist' not in search_params or \
            search_params['dist'] <= 0 or \
            'lat' not in search_params or \
            'long' not in search_params:
        valid_location = False
    else:
        valid_location = True

    # Normalize our location-based searching params -
    # if dist/lat/long is missing, make sure address/lat/long is cleared
    # (but not dist, since we want to preserve "Anywhere" selections)
    if not valid_location:
        search_params.pop('addr', None)
        search_params.pop('lat', None)
        search_params.pop('long', None)

        # If we have 'dist' in searching parameters, increment
        # the number of default parameters so that distance,
        # by itself, doesn't count as a parameter
        if 'dist' in search_params:
            default_params_count = default_params_count + 1

    # Issue #229 - If we don't have any distance specified,
    # default to 25 miles so that we'll have a default distance
    # in the event that they subsequently fill in an address
    if 'dist' not in search_params:
        search_params['dist'] = 25

        # Increment the number of default parameters used
        default_params_count = default_params_count + 1

    # Categories - this is a MultiDict so we need to use GetList
    rad.searchutils.add_int_set(
        search_params,
        'categories',
        request.args.getlist('categories'))

    # Populations - same as categories
    rad.searchutils.add_int_set(
        search_params,
        'populations',
        request.args.getlist('populations'))

    # Add a default ordering if not specified
    if 'order_by' not in search_params:
        if valid_location:
            search_params['order_by'] = 'distance'
        else:
            search_params['order_by'] = 'modified'

        # Ensure it's marked as a default param
        default_params_count = default_params_count + 1

    # All right - time to search! (if we have anything to search on)
    if len(search_params) > default_params_count:
        provider_page = rad.resourceservice.search(
            search_params=search_params,
            page_number=page,
            page_size=PER_PAGE)
    else:
        # Create a dummy page
        provider_page = Pagination(None, 1, PER_PAGE, 0, [])

    # Load up available categories
    categories = active_categories()

    # Load up available populations
    populations = active_populations()

    return render_template(
        'find-provider.html',
        pagination=provider_page,
        providers=provider_page.items,
        search_params=search_params,
        has_params=(len(search_params) > default_params_count),
        grouped_categories=group_active_categories(categories),
        grouped_populations=group_active_populations(populations)
    )


@remedy.route('/search-suggest/<text>')
def autocomplete(text):
    """
    Gets autocomplete suggestions for search text options.

    Args:
        text: The search text to use.

    Returns:
        A JSON array containing suggested searching strings.
    """
    if text is None:
        return get_json_response([])

    text = str(text).strip()

    if len(text) == 0:
        return get_json_response([])

    text = '%' + text + '%'

    # Search for visible categories matching the name/description
    categories = Category.query. \
        filter(Category.visible == True). \
        filter(or_(
            Category.name.like(text),
            Category.description.like(text))). \
        outerjoin(CategoryGroup, Category.grouping). \
        order_by(
            CategoryGroup.grouporder,
            CategoryGroup.name,
            Category.name). \
        limit(8). \
        all()

    # Get the names, converted to JSON, and return those
    category_json = [cat.name for cat in categories]
    return get_json_response(category_json)


@remedy.route('/submit-provider/', methods=['GET', 'POST'])
@login_required
def submit_provider():
    """
    Submits a new provider (with a corresponding user review)
    into the database for review.

    On a GET request it displays a form for submitting/reviewing a provider.
    On a POST request, it submits the form, after checking for errors.

    Returns:
        A page to submit a provider/review (via add-provider.html).
        This template is provided with the following variables:
            form: The WTForm to use for provider/review submission.
    """
    # Get active categories and populations
    category_choices = active_categories()
    population_choices = active_populations()

    form = UserSubmitProviderForm(
        request.form,
        None,
        group_active_categories(category_choices),
        group_active_populations(population_choices))

    if request.method == 'GET':
        return render_template(
            'add-provider.html',
            form=form)
    else:
        if form.validate_on_submit():
            # Get the new resource
            resource = get_new_resource(
                form,
                category_choices,
                population_choices)

            # Add the resource and flush the DB to get the new resource ID
            db.session.add(resource)
            db.session.flush()

            # Get the corresponding review
            review = get_new_review(form, resource)

            # Add the review and commit changes
            db.session.add(review)
            db.session.commit()

            # Flash a message and send them to the home page
            flash(
                'Thank you for submitting a provider! ' +
                'A RAD team member will review your submission and approve ' +
                'it if it meets RAD\'s submission criteria.',
                'success')
            return redirect_home()
        else:
            # Flash any errors
            flash_errors(form)

            return render_template(
                'add-provider.html',
                form=form)


@remedy.route('/review/<resource_id>/', methods=['GET', 'POST'])
@login_required
def new_review(resource_id):
    """
    Allows users to submit a new review.

    Args:
        resource_id: The ID of the resource to review.

    Returns:
        When accessed via GET, a form for submitting reviews
        (via add-review.html).
        This template is provided with the following variables:
            provider: The specific provider being reviewd.
            has_existing_review: A boolean indicating if the
                current user has already left a review for
                this resource.
            form: A ReviewForm instance for submitting a
                new review.
        When accessed via POST, a redirection action to the associated
        resource after the review has been successfully submitted.
    """
    # Get the form
    form = ReviewForm(request.form)

    # Get the associated resource
    resource = resource_with_id(resource_id)

    # See if we have other existing reviews left by this user
    existing_reviews = resource.reviews. \
        filter(Review.user_id == current_user.id). \
        all()

    if len(existing_reviews) > 0:
        has_existing_review = True
    else:
        has_existing_review = False

    # Only bother trying to handle the form if we have a submission
    if request.method == 'POST':
        # See if the form's valid
        if form.validate_on_submit():

            # Set up the new review
            new_r = get_new_review(form, resource)

            # Add the review and flush the DB to get the new review ID
            db.session.add(new_r)
            db.session.flush()

            # If we have other existing reviews, mark them as old
            if len(existing_reviews) > 0:
                for old_review in existing_reviews:
                    old_review.is_old_review = True
                    old_review.new_review_id = new_r.id

            db.session.commit()

            # Redirect the user to the resource
            flash('Review submitted!', 'success')

            return resource_redirect(new_r.resource_id)
        else:
            # Not valid - flash errors
            flash_errors(form)

    # We'll hit this if the form is invalid or we're
    # doing a simple GET.
    return render_template(
        'add-review.html',
        provider=resource,
        has_existing_review=has_existing_review,
        form=form)


@remedy.route('/delete-review/<review_id>', methods=['GET', 'POST'])
@login_required
def delete_review(review_id):
    """
    Handles the deletion of new reviews.

    Args:
        review_id: The ID of the review to delete.

    Returns:
        When accessed via GET, a form to confirm deletion
            (via find-provider.html).
        This template is provided with the following variables:
            review: The review being deleted.
        When accessed via POST, a redirection action to the
        associated resource after the review has been deleted.
    """
    review = Review.query.filter(Review.id == review_id).first()

    # Make sure we got one
    if review is None:
        abort(404)

    # Make sure we're an admin or the person who actually submitted it
    if not current_user.admin and current_user.id != review.user_id:
        flash('You do not have permission to delete this review.', 'error')
        return resource_redirect(review.resource_id)

    if request.method == 'GET':
        # Return the view for deleting reviews
        return render_template(
            'delete-review.html',
            review=review)
    else:
        rad.reviewservice.delete(db.session, review)
        flash('Review deleted.', 'success')
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
    # Prefill with existing user settings and get active populations
    population_choices = active_populations()

    form = UserSettingsForm(
        request.form,
        current_user,
        group_active_populations(population_choices))

    if request.method == 'GET':
        return render_template(
            'settings.html',
            form=form)
    else:
        if form.validate_on_submit():

            # Update the user's settings
            current_user.email = form.email.data
            current_user.display_name = form.display_name.data

            current_user.default_location = form.default_location.data
            current_user.default_latitude = form.default_latitude.data
            current_user.default_longitude = form.default_longitude.data

            # Process population IDs
            pop_ids = set(form.populations.data)

            for cur_pop in current_user.populations:
                # Remove any existing populations not in the set
                # and discard already-existing ones from the set
                if cur_pop.id not in pop_ids:
                    current_user.populations.remove(cur_pop)
                else:
                    pop_ids.discard(cur_pop.id)

            # Now iterate over any new populations
            for new_pop_id in pop_ids:
                # Find it in our population choices
                new_pop = find_by_id(population_choices, new_pop_id)

                # Make sure we found it and that the current user doesn't
                # already have it
                if new_pop and \
                        find_by_id(
                            current_user.populations,
                            new_pop_id
                        ) is None:
                    current_user.populations.append(new_pop)

            db.session.commit()

            flash('Your profile has been updated!', 'success')

        else:
            # Flash any errors
            flash_errors(form)

        return render_template(
            'settings.html',
            form=form)


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


@remedy.route('/about-the-beta/')
def about_the_beta():
    return render_template('about-the-beta.html')


@remedy.route('/disclaimer/')
def disclaimer():
    return render_template('disclaimer.html')


@remedy.route('/user-agreement/')
def user_agreement():
    return render_template('user-agreement.html')


@remedy.route('/privacy-policy/')
def privacy_policy():
    return render_template('privacy-policy.html')


@remedy.route('/terms-of-service/')
def terms_of_service():
    return render_template('terms-of-service.html')


@remedy.route('/submit-error/<resource_id>/', methods=['GET', 'POST'])
@login_required
def submit_error(resource_id):
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
            form: The WTForms ContactForm instance to use.
    """
    form = ContactForm()
    resource = resource_with_id(resource_id)

    if request.method == 'POST':
        if form.validate() == False:
            flash_errors(form)

            return render_template(
                'error.html',
                resource=resource,
                form=form)
        else:
            send_resource_error(resource, form.message.data)
            return render_template('error-submitted.html')

    elif request.method == 'GET':
        return render_template(
            'error.html',
            resource=resource,
            form=form)


def get_new_resource(form, category_choices, population_choices):
    """
    Gets a new resource based on the submitted form.
    Assumes submission from the current user.

    Args:
        form: The WTForms Form instance to use.
            Should incorporate the ProviderFieldsMixin mixin.
        category_choices: The list of active categories
            available for selection.
        population_choices: The list of active populations
            available for selection.

    Returns:
        An instantiated/inflated Resource instance.
    """
    new_res = Resource()

    # Set all standard fields
    new_res.name = form.provider_name.data
    new_res.organization = form.organization_name.data
    new_res.description = form.description.data

    new_res.address = form.address.data
    new_res.phone = form.phone_number.data
    new_res.fax = form.fax_number.data

    new_res.email = form.email.data
    new_res.url = form.website.data

    new_res.hours = form.office_hours.data
    new_res.hospital_affiliation = form.hospital_affiliation.data

    new_res.is_icath = form.is_icath.data
    new_res.is_wpath = form.is_wpath.data
    new_res.is_accessible = form.is_accessible.data
    new_res.has_sliding_scale = form.has_sliding_scale.data

    new_res.npi = form.npi.data
    new_res.notes = form.other_notes.data

    # Handle categories
    cat_ids = set(form.categories.data)

    for new_cat_id in cat_ids:
        # Find it in our category choices
        new_cat = find_by_id(category_choices, new_cat_id)

        # Make sure we found it
        if new_cat:
            new_res.categories.append(new_cat)

    # Handle populations
    pop_ids = set(form.populations.data)

    for new_pop_id in pop_ids:
        # Find it in our population choices
        new_pop = find_by_id(population_choices, new_pop_id)

        # Make sure we found it
        if new_pop:
            new_res.populations.append(new_pop)

    # Set approval/submission information
    new_res.is_approved = False
    new_res.submitted_date = datetime.utcnow()
    new_res.submitted_ip = get_ip()
    new_res.submitted_user_id = current_user.id
    new_res.source = u'user - ' + current_user.username

    return new_res


def get_new_review(form, resource):
    """
    Gets a new review based on the submitted form and specified resource.
    Assumes submission from the current user.

    Args:
        form: The WTForms Form instance to use.
            Should incorporate the ReviewFieldsMixin mixin.
        resource: The associated resource.

    Returns:
        An instantiated/inflated Review instance.
    """
    # Set up the new review
    new_r = Review(
        int(form.rating.data),
        form.review_comments.data,
        resource,
        user=current_user)

    # Set the IP
    new_r.ip = get_ip()

    # Add optional intake/staff ratings
    if int(form.intake_rating.data) > 0:
        new_r.intake_rating = int(form.intake_rating.data)
    else:
        new_r.intake_rating = None

    if int(form.staff_rating.data) > 0:
        new_r.staff_rating = int(form.staff_rating.data)
    else:
        new_r.staff_rating = None

    return new_r


def find_by_id(choices, id):
    """
    Finds an item in the provided list of choices by its ID,
    returning None if it was not found.

    Args:
        choices: The iterable of choices to search.
        id: The ID of the choice to find.

    Returns:
        The specified choice, or None if it was not found.
    """
    return next((c for c in choices if c.id == id), None)
