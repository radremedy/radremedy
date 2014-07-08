from rad.models import *
from flask.ext.restless import *

app_instance = None

# Preprocessor for POST methods on Resource api requests
# Can be used for authenitcation 
def pre_post(**kw):
	raise ProcessingException(description="Not Authorized", code=401)

def post_get_single(result=None, **kw):
	#if the resuld does not exist or is not marked as visable, raise a not found exception 
	if(result is None or not result['visable']) :
		raise ProcessingException(description="Record not found", code=404)

def init_api_manager(app, db) :
    api_manager = APIManager(app, flask_sqlalchemy_db=db)
    api_manager.create_api(Resource, 
    						methods=['GET', 'POST'], 
    						#exclude_columns=['visable'], 
    						preprocessors={
    							'POST': [pre_post]
    						}, 
    						postprocessors={
    							'GET_SINGLE': [post_get_single] 
    						}
    					)
    return api_manager
