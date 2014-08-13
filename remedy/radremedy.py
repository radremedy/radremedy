#!/usr/bin/env python
"""
radremedy.py

Main web application file. Contains initial setup of database, API, and other components.
Also contains the setup of the routes.
"""
from flask import Flask, url_for, request, abort
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from rad.models import db, Resource


def create_app(config, models=()):

    from remedyblueprint import remedy, url_for_other_page

    app = Flask(__name__)
    app.config.from_object(config)

    app.register_blueprint(remedy)

    # searching configurations
    app.jinja_env.trim_blocks = True
    # Register the paging helper method with Jinja2
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page

    db.init_app(app)

    Migrate(app, db, directory=app.config['MIGRATIONS_DIR'])

    manager = Manager(app)
    manager.add_command('db', MigrateCommand)

    # turning API off for now
    # from api_manager import init_api_manager
    # api_manager = init_api_manager(app, db)
    # map(lambda m: api_manager.create_api(m), models)

    return app, manager

if __name__ == '__main__':
    app, manager = create_app('config.BaseConfig', (Resource, ))

    with app.app_context():
        manager.run()
