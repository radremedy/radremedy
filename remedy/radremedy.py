"""
radremedy.py
"""
from flask import Flask, render_template
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from models import db


app = Flask(__name__)
app.config.from_object('config')


db.init_app(app)
migrate = Migrate(app, db, directory='./migrations')
manager = Manager(app)
manager.add_command('db', MigrateCommand)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
	return render_template('login.html')

if __name__ == '__main__':
    manager.run()
