from flask import Blueprint, render_template, redirect, url_for
from rad.models import Resource, Review


def latest_added(n):
    """
    The latest n resources added to the database.

    :param n: number of Resources to return
    :return: A list of Resources from the database
    """
    return Resource.query.order_by(Resource.date_created.desc()).limit(n).all()


def latest_reviews(n):
    """
    The latest n reviews added to the database.

    :param n: number of Reviews to return
    :return: A list of Reviews from the database
    """
    return Review.query.order_by(Review.date_created.desc()).limit(n).all()


def resource_with_id(i):
    """
    Get a resource by it's id from the database.
    :param i: id number
    :return: A Resource
    """
    return Resource.query.get(i)

remedy = Blueprint('remedy', __name__)


@remedy.route('/')
def index():
    return render_template('index.html', recently_added=latest_added(20),
                           recent_discussion=latest_reviews(20))


@remedy.route('/resource/')
def redirect_home():
    return redirect(url_for('.index'))


@remedy.route('/resource/<resource_id>/')
def resource(resource_id):
    return render_template('provider.html', provider=resource_with_id(resource_id))


@remedy.route('/find-provider/')
def provider():
    return render_template('find-provider.html')


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
