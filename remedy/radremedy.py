#!/usr/bin/env python
"""
radremedy.py

Main web application file. Contains initial setup of database, API, and other components.
Also contains the setup of the routes.
"""
from flask import Flask, render_template, redirect, url_for, request, abort
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from rad.models import db, Resource, Category, Review, User

from pagination import Pagination
import rad.resourceservice
import rad.searchutils
# API Manager disabled for now.
# from api_manager import init_api_manager

app = Flask(__name__)
app.config.from_object('config')

db.init_app(app)
migrate = Migrate(app, db, directory='./rad/migrations')
manager = Manager(app)
manager.add_command('db', MigrateCommand)

# API Manager disabled for now.
# api_manager = init_api_manager(app, db)
# api_manager.create_api(Resource)

# Define the maximum number of items to return in a page
PER_PAGE = 15

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

# Register the paging helper method with Jinja2
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

@app.route('/')
def index():
    return render_template('index.html', 
        recently_added=latest_added(20),
        recent_discussion=latest_reviews(20))


@app.route('/resource/')
def redirect_home():
    return redirect(url_for('index'))


@app.route('/resource/<resource_id>/')
def resource(resource_id):
    return render_template('provider.html', provider=resource_with_id(resource_id))


@app.route('/find-provider/', defaults={'page': 1})
@app.route('/find-provider/page/<int:page>')
def resource_search(page):
    # Start building out the search parameters.
    # At a minimum, we want to ensure that we only show visible resources.
    search_params = dict(visible=True)

    # Search string
    rad.searchutils.add_string(search_params, 'search', request.args.get('search'))

    # ID - minimum value of 1
    rad.searchutils.add_int(search_params, 'id', request.args.get('id'), min_value=1)

    # Distance - minimum value of 1, maximum value of 500 (miles)
    rad.searchutils.add_float(search_params, 'dist', request.args.get('dist'), min_value=1, max_value=500)

    # Latitude/longitude - no min/max values
    rad.searchutils.add_float(search_params, 'lat', request.args.get('lat'))
    rad.searchutils.add_float(search_params, 'long', request.args.get('long'))

    # All right - time to search!
    providers = rad.resourceservice.search(db, search_params=search_params)

    # Set up our pagination and render out the template.
    count, paged_providers = get_paged_data(providers, page)
    pagination = Pagination(page, PER_PAGE, count)

    return render_template('find-provider.html',
        pagination=pagination,
        providers=paged_providers
    )


@app.route('/login/')
def login():
    return render_template('login.html')


@app.route('/signup/')
def sign_up():
    return render_template('create-account.html')


@app.route('/settings/')
def settings():
    # TODO: stub
    stub = {'user': {'username': 'Doctor Who',
                     'email': 'doctorwho@gmail.com',
                     'gender_identity': 'unknown',
                     'preferred_pronouns': 'Dr.',
                     'password': '?????Should we really show a password??????'}}

    return render_template('settings.html', **stub)


@manager.shell
def make_shell_context():
    """
    This function is used with the ./radremedy.py shell
    command. It imports some variables into the shell
    to make testing stuff out easier.

    Imports: The application, database, and some of it's
    models(Resource, Review, User and Category).

    This avoids having to run:
    from radremedy import <stuff>
    in every startup of the shell.

    """
    return dict(app=app, db=db, Resource=Resource,
                Review=Review, User=User, Category=Category)


if __name__ == '__main__':
    with app.app_context():
        manager.run()
