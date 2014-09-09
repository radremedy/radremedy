from flask import redirect
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from remedy.rad.models import Resource, User, Category, Review, db


class ResourceView(ModelView):
    """
    An administrative view for working with resources.
    """
    column_list = ('name', 'address', 
        'email', 'phone', 'url', 
        'source', 'last_updated')

    column_searchable_list = ('name', )

    form_excluded_columns = ('date_created', 'last_updated', 
        'category_text', 'reviews')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(ResourceView, self).__init__(Resource, session, **kwargs)


class UserView(ModelView):
    """
    An administrative view for working with users.
    """
    column_list = ('username', 'email', 
        'admin', 'active', 'date_created')

    column_searchable_list = ('username', 'email', )

    form_excluded_columns = ('password', 'date_created', 'reviews',
        'default_location', 'default_latitude', 'default_longitude')

    # TODO: Figure out a way to reset passwords

    def __init__(self, session, **kwargs):
        super(UserView, self).__init__(User, session, **kwargs)    



class CategoryView(ModelView):
    """
    An administrative view for working with categories.
    """
    column_list = ('name', 'description', 
        'visible', 'date_created')

    column_searchable_list = ('name', 'description', )

    form_excluded_columns = ('resources', 'date_created')

    def __init__(self, session, **kwargs):
        super(CategoryView, self).__init__(Category, session, **kwargs)    


admin = Admin(name='RAD Remedy')
admin.add_view(ResourceView(db.session))
admin.add_view(UserView(db.session))
admin.add_view(CategoryView(db.session))
admin.add_view(ModelView(Review, db.session))