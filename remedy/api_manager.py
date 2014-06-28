from rad.models import *
from flask.ext.restless import APIManager

def init_api_manager(app, db) :
    api_manager = APIManager(app, flask_sqlalchemy_db=db)
    api_manager.create_api(Resource, methods=['GET', 'POST'])
    return api_manager
