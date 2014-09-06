from flask import redirect
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from remedy.rad.models import Resource, User, Category, Review, db


class ResourceView(ModelView):

    column_list = ('name', 'address', 'email', 'phone',
                   'fax', 'url', 'description', 'source',
                   'date_created', 'last_updated')

    column_searchable_list = ('name', )

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(ResourceView, self).__init__(Resource, session, **kwargs)


admin = Admin(name='RAD Remedy')
admin.add_view(ResourceView(db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Category, db.session))
admin.add_view(ModelView(Review, db.session))