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

import sys
import logging
from logging.handlers import RotatingFileHandler

from rad.models import db


def create_app(config):
    """
    Creates a Flask application based on the provided configuration object.

    Args:
        config: The configuration object.
    """
    app = Flask(__name__)
    app.config.from_object(config)

    from remedyblueprint import remedy, url_for_other_page, server_error
    app.register_blueprint(remedy)

    # Register a custom error handler for production scenarios
    if app.debug is not True:
        app.error_handler_spec[None][500] = server_error
        app.error_handler_spec[None][Exception] = server_error

    from admin import admin
    admin.init_app(app)

    from auth.user_auth import auth, login_manager
    app.register_blueprint(auth)
    login_manager.init_app(app)

    # searching configurations
    app.jinja_env.trim_blocks = True

    # Register the paging helper method with Jinja2
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page
    app.jinja_env.globals['logged_in'] = lambda: current_user.is_authenticated

    db.init_app(app)

    from flask_wtf.csrf import CsrfProtect
    CsrfProtect(app)

    Migrate(app, db, directory=app.config['MIGRATIONS_DIR'])

    manager = Manager(app)
    manager.add_command('db', MigrateCommand)

    # Enable logging for production environments
    if app.debug is not True:
        logging.basicConfig(stream=sys.stderr)

        file_handler = RotatingFileHandler(
            'python.log',
            maxBytes=1024 * 1024 * 100,
            backupCount=20)
        file_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    # Configure proxies for WSGI
    if app.wsgi_app is not None:
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

    # turning API off for now
    # from api_manager import init_api_manager
    # api_manager = init_api_manager(app, db)
    # map(lambda m: api_manager.create_api(m), models)

    return app, manager
