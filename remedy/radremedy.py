"""
radremedy.py
"""
from flask import Flask, render_template

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from api_manager import init_api_manager
from rad.db.models import db


app = Flask(__name__)
app.config.from_object('config')


db.init_app(app)
migrate = Migrate(app, db, directory='./rad/db/migrations')
manager = Manager(app)
manager.add_command('db', MigrateCommand)

api_manager = init_api_manager(app, db) 

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/find-provider')
def provider():
    return render_template('find-provider.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/signup')
def sign_up():
    return render_template('create-account.html')


@app.route('/settings')
def settings():
    # TODO: stub
    stub = {'user': {'username': 'Doctor Who',
                     'email': 'doctorwho@gmail.com',
                     'gender_identity': 'unknown',
                     'preferred_pronouns': 'Dr.',
                     'password': '?????Should we really show a password??????'}}
    return render_template('settings.html', **stub)

if __name__ == '__main__':
    manager.run()
