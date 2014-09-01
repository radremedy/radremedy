from flask import redirect
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from remedy.rad.models import Resource, User, Category, Review, db


class ResourceView(ModelView):


    column_list = ('name', 'street', 'city', 'state',
                   'country', 'zipcode', 'email', 'phone',
                   'fax', 'url', 'description', 'source',
                   'fulladdress', 'date_created', 'last_updated',
                   'category')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(ResourceView, self).__init__(Resource, session, **kwargs)


admin = Admin(name='RAD Remedy')
admin.add_view(ResourceView(db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Category, db.session))
admin.add_view(ModelView(Review, db.session))