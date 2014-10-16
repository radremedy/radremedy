"""
admin.py

Contains functionality for providing administrative interfaces
to items in the system.
"""
from flask import redirect, flash
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from sqlalchemy import or_, func

from flask_wtf import Form
from wtforms import PasswordField, validators, ValidationError

import bcrypt

from remedy.rad.models import Resource, User, Category, Review, db


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
    column_list = ('name', 'organization', 'address', 'source')

    # Disable model creation/deletion
    can_create = False
    can_delete = False

    def get_query(self):
        """
        Returns the query for the model type.

        Returns:
            The query for the model type.
        """
        query = self.session.query(self.model)
        return self.prepare_geocode_query(query)

    def get_count_query(self):
        """
        Returns the count query for the model type.

        Returns:
            The count query for the model type.
        """
        query = self.session.query(func.count('*')).select_from(self.model)
        return self.prepare_geocode_query(query)

    def prepare_geocode_query(self, query):
        """
        Prepares the provided query by ensuring that
        all relevant geocoding-related filters have been applied.

        Args:
            query: The query to update.

        Returns:
            The updated query.
        """
        # Ensure an address is defined
        query = query.filter(self.model.address != None)
        query = query.filter(self.model.address != '')

        # Ensure at least one geocoding field is missing
        query = query.filter(or_(self.model.latitude == None,
            self.model.longitude == None))

        return query

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