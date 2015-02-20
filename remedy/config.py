"""
config.py

Contains configuration information used throughout the application.
"""
import os

_basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    """
    The base configuration used by both development
    and production configurations.
    """

    """
    Indicates if debugging is enabled for the application.
    """
    DEBUG = True

    """
    The URI of the database.
    """
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'rad/rad.db')

    """
    The path to the directory containing database migrations.
    """
    MIGRATIONS_DIR = './remedy/rad/migrations'

    """
    The secret key.
    """
    SECRET_KEY = 'Our little secret'

    """
    The base URL to the website.
    """
    BASE_URL = 'http://radremedy.org'

    """
    The username of the account used to send email.

    Retrieved through the RAD_EMAIL_USERNAME environment variable.
    """
    EMAIL_USERNAME = str(os.environ.get('RAD_EMAIL_USERNAME'))

    """
    The full address of the account used to send email,
    and to which error reports will be submitted.

    Retrieved through the RAD_EMAIL_ADDRESS environment variable.
    """
    EMAIL_ADDRESS = str(os.environ.get('RAD_EMAIL_ADDRESS'))

    """
    The display name to include with emails. Optional.
    """
    EMAIL_DISPLAY_NAME = 'RAD Remedy'

    """
    The password of the account used to send email.

    Retrieved through the RAD_EMAIL_PASSWORD environment variable.
    """
    EMAIL_PASSWORD = str(os.environ.get('RAD_EMAIL_PASSWORD'))

    """
    The address of the server used to send email.
    A port can be included.

    Retrieved through the RAD_EMAIL_SERVER environment variable.
    """
    EMAIL_SERVER = str(os.environ.get('RAD_EMAIL_SERVER'))


class DevelopmentConfig(BaseConfig):
    """
    The configuration used for development environments.
    """
    BASE_URL = 'http://localhost:5000'


class ProductionConfig(BaseConfig):
    """
    The configuration used for the production environment.
    """
    DEBUG = False

    # Require a secret key.
    if str(os.environ.get('RAD_SECRET_KEY')):
        SECRET_KEY = str(os.environ.get('RAD_SECRET_KEY'))
    else:
        raise RuntimeError('The RAD_SECRET_KEY environment variable is not configured.')

    # Allow overriding the base URL
    if str(os.environ.get('RAD_BASE_URL')):
        BASE_URL = str(os.environ.get('RAD_BASE_URL'))

    SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://{0}:{1}@{2}/{3}?charset=utf8&use_unicode=0'. \
        format(os.environ.get('RDS_USERNAME'),
           os.environ.get('RDS_PASSWORD'),
           os.environ.get('RDS_HOSTNAME'),
           os.environ.get('RDS_DB_NAME'))
