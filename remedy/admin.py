"""
admin.py

Contains functionality for providing administrative interfaces
to items in the system.
"""
from flask import redirect, flash
from flask.ext.admin import Admin
from flask.ext.admin.babel import lazy_gettext
from flask.ext.admin.model import filters
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.sqla.filters import BaseSQLAFilter

from flask_wtf import Form
from wtforms import PasswordField, validators, ValidationError

import bcrypt

from remedy.rad.models import Resource, User, Category, Review, db


class FilterNull(BaseSQLAFilter):
    """
    A custom SQLAlchemy filter for checking if
    a column is null.
    """
    def apply(self, query, value):
        return query.filter(self.column == None)
    
    def operation(self):
        return lazy_gettext('is null')


class FilterNotNullOrEmpty(BaseSQLAFilter):
    """
    A custom SQLAlchemy filter for checking if
    a column is not null or an empty string.
    """

    def apply(self, query, value):
        return query.filter(self.column != None).filter(self.column != '')
    
    def operation(self):
        return lazy_gettext('is not null or empty')


class ResourceView(ModelView):
    """
    An administrative view for working with resources.
    """
    column_list = ('name', 'organization', 
        'address', 'url', 
        'source', 'last_updated')

    column_default_sort = 'name'

    column_searchable_list = ('name',)

    form_excluded_columns = ('date_created', 'last_updated', 
        'category_text', 'reviews')

    # TODO: Figure out how to wire up Google Maps to this view

    def __init__(self, session, **kwargs):
        super(ResourceView, self).__init__(Resource, session, **kwargs)


class ResourceRequiringGeocodingView(ResourceView):
    """
    An administrative view for working with resources that need geocoding.
    """
    column_list = ('name', 'organization', 'address', 
        'source', 'last_updated')

    column_filters = [FilterNotNullOrEmpty(Resource.address, "Address"),
        FilterNull(Resource.latitude, "Latitude"),
        FilterNull(Resource.longitude, "Longitude")]

    # Disable model creation/deletion
    can_create = False
    can_delete = False

    def get_list(self, page, sort_column, sort_desc, search, filters):

        # HACK: Manually override filters internal to always
        # enforce latitude/longitude/address filtering
        self.__filters = [FilterNotNullOrEmpty(Resource.address, "Address"),
            FilterNull(Resource.latitude, "Latitude"),
            FilterNull(Resource.longitude, "Longitude")]

        # Turn the filters into an iterable set of tuples
        # of the form (index, element)
        return super(ResourceRequiringGeocodingView, self).get_list(page,
            sort_column,
            sort_desc,
            search,
            [(i, item) for i, item in enumerate(self.__filters)])

    def __init__(self, session, **kwargs):
        # Because we're invoking the ResourceView constructor,
        # we don't need to pass in the ResourceModel.
        super(ResourceRequiringGeocodingView, self).__init__(session, **kwargs)


class UserView(ModelView):
    """
    An administrative view for working with users.
    """
    column_list = ('username', 'email', 
        'admin', 'active', 'date_created')

    column_default_sort = 'username'

    column_searchable_list = ('username', 'email',)

    form_excluded_columns = ('password', 'date_created', 'reviews',
        'default_location', 'default_latitude', 'default_longitude')

    def scaffold_form(self):
        """
        Sets up the user form to ensure that password fields
        are present.
        """
        form_class = super(UserView, self).scaffold_form()

        form_class.new_password = PasswordField('New Password',
            [validators.EqualTo('new_password_confirm', message='New passwords must match')])
        form_class.new_password_confirm = PasswordField('Confirm New Password')

        return form_class

    def update_model(self, form, model):
        """
        Handles when a model is being updated to ensure that
        any password changes are properly handled.

        Args:
            form: The source form.
            model: The model being updated.
        """        
        try:
            form.populate_obj(model)

            # Are we specifying a new password?
            if len(model.new_password):
                newpass = model.new_password
                newpassconfirm = model.new_password_confirm

                # Make sure the passwords match
                if newpass == newpassconfirm:
                    model.password = bcrypt.hashpw(newpass, bcrypt.gensalt())
                else:
                    raise ValueError('Passwords must match.')

            self.session.commit()
            return True
        except Exception, ex:
            flash('Failed to edit user. ' + str(ex))
            return False

    def create_model(self, form):
        """
        Handles when a model has been created, to ensure that
        a password has been provided and that it has been properly
        hashed.

        Args:
            form: The source form.
        """
        try:
            model = self.model()
            form.populate_obj(model)

            # Require a password if this is a new record.
            if len(model.new_password):
                newpass = model.new_password
                newpassconfirm = model.new_password_confirm

                # Make sure the passwords match
                if len(newpass) and newpass == newpassconfirm:
                    model.password = bcrypt.hashpw(newpass, bcrypt.gensalt())
                elif newpass != newpassconfirm:
                    raise ValueError('Passwords must match.')
            else:
                raise ValueError('A password is required for new users.')

            self.session.add(model)
            self.session.flush()

            self.session.commit()
            return True
        except Exception, ex:
            flash('Failed to create user. ' + str(ex))
            return False

    def __init__(self, session, **kwargs):
        super(UserView, self).__init__(User, session, **kwargs)    


class CategoryView(ModelView):
    """
    An administrative view for working with categories.
    """
    column_list = ('name', 'description', 
        'visible', 'date_created')

    column_default_sort = 'name'

    column_searchable_list = ('name', 'description',)

    form_excluded_columns = ('resources', 'date_created')

    def __init__(self, session, **kwargs):
        super(CategoryView, self).__init__(Category, session, **kwargs)    


class ReviewView(ModelView):
    """
    An administrative view for working with resource reviews.
    """
    column_select_related_list = (Review.resource, Review.user)

    column_default_sort = 'date_created'

    column_list = ('rating', 'resource.name', 'user.username', 'visible', 'date_created')
    column_labels = {
        'rating': 'Rating', 
        'resource.name': 'Resource',
        'user.username': 'User',
        'visible': 'Visible', 
        'date_created': 'Date Created'
    }

    column_searchable_list = ('text',)

    form_excluded_columns = ('date_created')

    def __init__(self, session, **kwargs):
        super(ReviewView, self).__init__(Review, session, **kwargs)    


admin = Admin(name='RAD Remedy')
admin.add_view(ResourceView(db.session,
    category='Resource',
    name='All',
    endpoint='resourceview',))
admin.add_view(ResourceRequiringGeocodingView(db.session,
    category='Resource',
    name='Needing Geocoding', 
    endpoint='geocode-resourceview'))
admin.add_view(UserView(db.session))
admin.add_view(CategoryView(db.session))
admin.add_view(ReviewView(db.session))