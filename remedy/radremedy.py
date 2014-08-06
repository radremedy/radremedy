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


def create_app(config, models=()):

    app = Flask(__name__)
    app.config.from_object(config)

    from remedyblueprint import remedy
    app.register_blueprint(remedy)

    db.init_app(app)

    migrate = Migrate(app, db, directory=app.config['MIGRATIONS_DIR'])

    manager = Manager(app)
    manager.add_command('db', MigrateCommand)

    from api_manager import init_api_manager
    api_manager = init_api_manager(app, db)

    map(lambda m: api_manager.create_api(m), models)

    return app, manager

if __name__ == '__main__':
    app, manager = create_app('config.BaseConfig', (Resource, ))

    with app.app_context():
        manager.run()
