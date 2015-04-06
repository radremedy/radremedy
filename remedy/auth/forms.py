"""
forms.py

Contains forms related to authentication, which includes logging in,
requesting a password reset, resetting a password, and changing a password.
"""
import re

from flask.ext.login import current_user
from flask_wtf import Form

from wtforms import PasswordField, StringField, SubmitField, ValidationError
from wtforms.validators import Optional, DataRequired, EqualTo, Length, Regexp, Email

from remedy.rad.models import User

class BaseAuthForm(Form):
    """
    A base class for authentication forms.
    Avoids having to write the same fields across forms. 

    The submit text can be changed by subclassing and overriding the
    _submit_text instance variable.

    Fields on the form:
        username
        password
    """

    _submit_text = 'Submit'

    username = StringField('Username', validators=[
        DataRequired(), Length(1, message='Username has to be at least 1 character'),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Username must have only letters, numbers, dots or underscores')
    ])

    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(8, message='Password must be longer than 8 letters.'),
        Regexp('^((?!password).)*$', flags=re.IGNORECASE, message='Password cannot contain "password"')
    ])

    submit = SubmitField(_submit_text)


class SignUpForm(BaseAuthForm):
    """
    A form used during sign up.

    Fields on the form:
        username
        email
        password
        password2
        display_name
    """

    _submit_text = 'Sign Up!'

    email = StringField('Email', validators=[
        DataRequired(), 
        Email(), 
        Length(1, 70)
    ])

    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),  
        EqualTo('password', message='Passwords must match.')
    ])

    display_name = StringField('Name', validators=[
        Optional(),
        Length(2, 100)
    ])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class LoginForm(BaseAuthForm):
    """
    A form to login after signing up.

    Fields on the form:
        username
        password
    """
    _submit_text = 'Login'


class RequestPasswordResetForm(Form):
    """
    A form to request a password reset.

    Fields on the form:
        email
    """

    email = StringField('Email', validators=[
        DataRequired(), 
        Email(), 
        Length(1, 70)
    ])

    submit = SubmitField('Request Reset')


class PasswordResetForm(Form):
    """
    A form to reset a password. Also inherited by the PasswordChangeForm,
    which is intended for use by authenticated users.

    Fields on the form:
        password
        password2
    """

    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(8, message='Password must be longer than 8 letters.'),
        Regexp('^((?!password).)*$', flags=re.IGNORECASE, message='Password cannot contain "password"')
    ])

    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),  
        EqualTo('password', message='Passwords must match.')
    ])    

    submit = SubmitField('Change Password')


class PasswordChangeForm(PasswordResetForm):
    """
    A form to change a password.

    Fields on the form:
        currentpassword
        password
        password2
    """

    currentpassword = PasswordField('Current Password', validators=[
        DataRequired(),
        Length(8, message='Current Password must be longer than 8 letters.')
    ])

    def validate_currentpassword(self, field):
        """
        Validates that the provided current password is correct.
        """
        if not current_user.verify_password(field.data):
            raise ValidationError('The current password you have provided is incorrect.')
