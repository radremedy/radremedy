"""
userview.py

Contains administrative views for working with users.
"""
from admin_helpers import *

import re
import bcrypt

from flask import flash
from flask.ext.admin.actions import action
from flask.ext.admin.contrib.sqla import ModelView
from wtforms import StringField, DecimalField, PasswordField, validators

from remedy.rad.models import User


class UserView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with users.
    """
    # Allow detail view
    can_view_details = True

    column_details_exclude_list = ('default_latitude', 'default_longitude', 
        'password', 'reset_pass_date', 'email_code')

    column_list = ('username', 'display_name', 'email', 
        'admin', 'active', 'email_activated', 'date_created')

    column_default_sort = 'username'

    column_searchable_list = ('username', 'email', 'display_name',)

    column_filters = ('admin', 'active', 'email_activated',)

    form_excluded_columns = ('password', 'date_created', 'reviews', 
        'email_activated', 'reset_pass_date', 'email_code', 'submittedresources')

    create_template = 'admin/user_create.html'

    edit_template = 'admin/user_edit.html'

    def scaffold_form(self):
        """
        Sets up the user form to ensure that password fields
        are present and that the default latitude/longitude
        fields are treated as optional.
        """
        form_class = super(UserView, self).scaffold_form()

        form_class.username = StringField('Username', validators=[
            validators.DataRequired(), 
            validators.Length(1, message='Username has to be at least 1 character'),
            validators.Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Username must have only letters, numbers, dots or underscores')
        ])

        form_class.email = StringField('Email', validators=[
            validators.DataRequired(), 
            validators.Email(), 
            validators.Length(1, 70)
        ])

        form_class.display_name = StringField('Display Name', validators=[
            validators.DataRequired(), 
            validators.Length(2, 100)
        ])

        form_class.new_password = PasswordField('New Password', validators=[
            validators.EqualTo('new_password_confirm', message='New passwords must match'),
            validators.Regexp('^((?!password).)*$', flags=re.IGNORECASE, 
                message='Password cannot contain "password"')
        ])

        form_class.new_password_confirm = PasswordField('Confirm New Password')

        # Override the latitude/longitude fields to be optional
        form_class.default_latitude = DecimalField(validators=[validators.Optional()])
        form_class.default_longitude = DecimalField(validators=[validators.Optional()])

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
                    if len(newpass) < 8:
                        raise ValueError('Password must be longer than 8 letters.')
                    else:
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

            # Don't require email activation when
            # creating through Admin.
            model.email_activated = True

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

    @action('toggleactive', 
        'Toggle Active', 
        'Are you sure you wish to toggle active status for the selected users?')
    def action_toggleactive(self, ids):
        """
        Attempts to toggle active status for each of the specified users.

        Args:
            ids: The list of user IDs, indicating which users
                should have their active status toggled.
        """
        # Load all users by the set of IDs
        target_users = self.get_query().filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_users) > 0:

            for user in target_users:
                # Build a helpful message string to use for messages.
                user_str =  'user #' + str(user.id) + ' (' + user.username + ')'
                active_status = ''
                try:
                    if not user.active:
                        user.active = True
                        active_status = ' as active'
                    else:
                        user.active = False
                        active_status = ' as inactive'
                except Exception as ex:
                    results.append('Error changing ' + user_str + ': ' + str(ex))
                else:
                    results.append('Marked ' + user_str + active_status + '.')

            # Save our changes.
            self.session.commit()

        else:
            results.append('No users were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    def __init__(self, session, **kwargs):
        super(UserView, self).__init__(User, session, **kwargs)    

