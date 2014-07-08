from rad.models import *
from flask.ext.restless import *

# Preprocessor for POST methods on Resource api requests
# Can be used for authenitcation 
def pre_post(**kw):
	raise ProcessingException(description="Not Authorized", code=401)

#if the resuld does not exist or is not marked as visable, raise a not found exception 
def post_get_single(result=None, **kw):
	if(result is None or not result['visable']) :
		raise ProcessingException(description="Record not found", code=404)
	else :
		del result['visable'] #remove the visable entry because it will always be true

#if a given record in the list isn't visable, remove just that record
def post_get_many(result=None, search_params=None, **kw):
	entries = result['objects']
	for entry in list(entries) :
		if not entry['visable']:
			entries.remove(entry)
		else :
			del entry['visable'] #remove the visable entry because it will always be true

	result['objects'] = entries

def init_api_manager(app, db) :
    api_manager = APIManager(app, flask_sqlalchemy_db=db)
    api_manager.create_api(Resource, 
    						methods=['GET', 'POST'], 
    						#exclude_columns=['visable'], 
    						preprocessors={
    							'POST': [pre_post]
    						}, 
    						postprocessors={
    							'GET_SINGLE': [post_get_single],  
    							'GET_MANY': [post_get_many]
    						}
    					)
    return api_manager
