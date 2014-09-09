from flask import redirect
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from remedy.rad.models import Resource, User, Category, Review, db


class ResourceView(ModelView):

    column_list = ('name', 'address', 
        'email', 'phone', 'url', 
        'source', 'last_updated')

    column_searchable_list = ('name', )

    form_excluded_columns = ('date_created', 'last_updated', 
        'category_text', 'reviews')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(ResourceView, self).__init__(Resource, session, **kwargs)


admin = Admin(name='RAD Remedy')
admin.add_view(ResourceView(db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Category, db.session))
admin.add_view(ModelView(Review, db.session))