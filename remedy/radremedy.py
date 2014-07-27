#!/usr/bin/env python
"""
radremedy.py

Main web application file. Contains initial setup of database, API, and other components.
Also contains the setup of the routes.
"""
from flask import Flask, render_template, redirect, url_for
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from rad.models import db, Resource, Category, Review, User
from api_manager import init_api_manager

app = Flask(__name__)
app.config.from_object('config')

db.init_app(app)
migrate = Migrate(app, db, directory='./rad/migrations')
manager = Manager(app)
manager.add_command('db', MigrateCommand)

api_manager = init_api_manager(app, db)
api_manager.create_api(Resource)


def latest_added(n):
    """
    The latest n resources added to the database.

    :param n: number of Resources to return
    :return: A list of Resources from the database
    """
    return Resource.query.order_by(Resource.date_created.desc()).limit(n).all()


def latest_reviews(n):
    return Review.query.order_by(Review.date_created.desc()).limit(n).all()


def resource_with_id(i):
    """
    Get a resource by it's id from the database.
    :param i: id number
    :return: A Resource
    """
    return Resource.query.get(i)


@app.route('/')
def index():
    return render_template('index.html', recently_added=latest_added(20),
                           recent_discussion=latest_reviews(20))


@app.route('/resource/')
def redirect_home():
    return redirect(url_for('index'))


@app.route('/resource/<resource_id>/')
def resource(resource_id):
    return render_template('provider.html', provider=resource_with_id(resource_id))


@app.route('/find-provider/')
def provider():
    return render_template('find-provider.html')


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

if __name__ == '__main__':
    with app.app_context():
        manager.run()
