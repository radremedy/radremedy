"""
api_manager.py 

This module contains functions that manage the RESTful API.
"""

from rad.models import *
from flask.ext.restless import *


def pre_post(**kw):
    """
    Will check to make sure if a user is authorized to edit the information on a resource (a POST method).
    Right now, it just returns a not authorized exception. 
    """
    raise ProcessingException(description="Not Authorized", code=401)


# if the result does not exist or is not marked as visible, raise a not found exception
def post_get_single(result=None, **kw):
    """Don't allow a single record marked as not visible to be viewed."""
    if (result is None or not result['visable']):
        raise ProcessingException(description="Record not found", code=404)
    else:
        del result['visable']  # remove the visible entry because it will always be true


# if a given record in the list isn't visible, remove just that record
def post_get_many(result=None, search_params=None, **kw):
    """When listing multiple entries, don't allow non-visible entries to be seen."""
    entries = result['objects']
    for entry in list(entries):
        if not entry['visable']:
            entries.remove(entry)
        else:
            del entry['visable']  # remove the visible entry because it will always be true

    result['objects'] = entries


def init_api_manager(app, db):
    """
    This method starts the api manager and properly initializes all pre- and post- preprocessors

    Args: 
        app: the current running context 
        db: the database used in the current context 
    """
    api_manager = APIManager(app, flask_sqlalchemy_db=db)
    api_manager.create_api(Resource,
                           methods=['GET', 'POST'],  # exclude_columns=['visable'],
                           preprocessors={
                           'POST': [pre_post]
                           },
                           postprocessors={
                           'GET_SINGLE': [post_get_single],
                           'GET_MANY': [post_get_many]
                           }
    )
    return api_manager
