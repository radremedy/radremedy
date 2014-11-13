#!/usr/bin/env python
"""
radremedy.py

Main web application file. Contains initial setup of database, API, and other components.
Also contains the setup of the routes.
"""
from flask import Flask, url_for, request, abort
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.login import current_user

from rad.models import db


def create_app(config):

    app = Flask(__name__)
    app.config.from_object(config)

    from remedyblueprint import remedy, url_for_other_page
    app.register_blueprint(remedy)

    from admin import admin
    admin.init_app(app)

    from auth.user_auth import auth, login_manager
    app.register_blueprint(auth)
    login_manager.init_app(app)

    # searching configurations
    app.jinja_env.trim_blocks = True
    # Register the paging helper method with Jinja2
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page
    app.jinja_env.globals['logged_in'] = lambda : not current_user.is_anonymous()

    db.init_app(app)

    from flask_wtf.csrf import CsrfProtect
    CsrfProtect(app)

    Migrate(app, db, directory=app.config['MIGRATIONS_DIR'])

    manager = Manager(app)
    manager.add_command('db', MigrateCommand)

    # turning API off for now
    # from api_manager import init_api_manager
    # api_manager = init_api_manager(app, db)
    # map(lambda m: api_manager.create_api(m), models)
    
    return app, manager
