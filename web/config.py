import os
_basedir = os.path.abspath(os.path.dirname(__file__))

if 'RAD_PRODUCTION' in os.environ:
    DEBUG = False
else:
    DEBUG = True

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'app.db')
