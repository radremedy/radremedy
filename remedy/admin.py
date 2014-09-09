from flask import redirect, flash
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from flask_wtf import Form
from wtforms import PasswordField, validators, ValidationError

import bcrypt

from remedy.rad.models import Resource, User, Category, Review, db


class ResourceView(ModelView):
    """
    An administrative view for working with resources.
    """
    column_list = ('name', 'address', 
        'email', 'phone', 'url', 
        'source', 'last_updated')

    column_searchable_list = ('name',)

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

    column_searchable_list = ('username', 'email',)

    form_excluded_columns = ('password', 'date_created', 'reviews',
        'default_location', 'default_latitude', 'default_longitude')

    def scaffold_form(self):
        form_class = super(UserView, self).scaffold_form()

        form_class.new_password = PasswordField('New Password',
            [validators.EqualTo('new_password_confirm', message='New passwords must match')])
        form_class.new_password_confirm = PasswordField('Confirm New Password')

        return form_class

    def update_model(self, form, model):
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

    column_searchable_list = ('name', 'description',)

    form_excluded_columns = ('resources', 'date_created')

    def __init__(self, session, **kwargs):
        super(CategoryView, self).__init__(Category, session, **kwargs)    


class ReviewView(ModelView):
    """
    An administrative view for working with resource reviews.
    """
    column_select_related_list = (Review.resource, Review.user)

    # TODO: Add resource/user names
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
admin.add_view(ResourceView(db.session))
admin.add_view(UserView(db.session))
admin.add_view(CategoryView(db.session))
admin.add_view(ReviewView(db.session))