"""
forms.py

Contains general-purpose forms, such as those for contacting
the RAD team about resource corrections, reviewing resources,
and changing user settings.
"""

from flask.ext.login import current_user
from flask_wtf import Form

from wtforms import StringField, TextField, TextAreaField, SubmitField, ValidationError, HiddenField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, Email

from .models import Resource, User

class ContactForm(Form):
    """
    A form for submitting a correction to a resource.

    Fields on the form:
        message
    """
    message = TextAreaField("Comments", validators=[
        DataRequired("Comments are required.")
    ])

    submit = SubmitField("Send")


class ReviewForm(Form):
    """
    A form for submitting resource reviews.

    Fields on the form:
        rating
        description
    """
    rating = SelectField('Rating', default='3', choices=[
        ('5', '5 - I had a very good experience'),
        ('4', '4 - I had a good experience'),
        ('3', '3 - I had a neutral experience'),
        ('2', '2 - I had a bad experience'),
        ('1', '1 - I had a very bad experience')
    ], validators=[
        DataRequired()
    ])

    # this is the text field with more details
    description = TextAreaField('My Experience', validators=[
        DataRequired(), 
        Length(1, 2000)
    ])

    # the Resource been reviewed, this field is hidden
    # because we set in the templates, the user
    # doesn't actually have to select this
    provider = HiddenField(validators=[
        DataRequired()
    ])

    submit = SubmitField('Submit Review')

    def validate_provider(self, field):
        """
        Validates that the provider exists in the database.
        """
        if Resource.query.get(field.data) is None:
            raise ValidationError('No provider found.')


class UserSettingsForm(Form):
    """
    A form for submitting resource reviews.

    Fields on the form:
        email
        display_name
    """
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(), 
        Length(1, 70)
    ])

    display_name = StringField('Displayed Name', validators=[
        DataRequired(), 
        Length(2, 100)
    ])

    submit = SubmitField('Save')

    def validate_email(self, field):
        """
        Validates that the provided email is unique.
        """
        existing_user = User.query. \
            filter(User.email == field.data). \
            filter(User.id != current_user.id). \
            first()

        if existing_user:
            raise ValidationError('A user already exists in the database with that email.')
