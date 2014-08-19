"""
config.py

Looks for the RAD_PRODUCTION variable and creates path to database 
"""
import os

_basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'rad/rad.db')
    MIGRATIONS_DIR = './remedy/rad/migrations'
    SECRET_KEY = 'Our little secret'


class DevelopmentConfig(BaseConfig):
    pass


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'rad/rad.db')
