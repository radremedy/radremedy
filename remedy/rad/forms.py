from flask_wtf import Form
from .models import Resource
from wtforms import TextField, TextAreaField, SubmitField, validators, ValidationError, \
   HiddenField, SelectField


class ContactForm(Form):
    """
    A form for submitting a correction to a resource.
    """
    message = TextAreaField("Comments", [validators.Required("Comments are required.")])

    submit = SubmitField("Send")


class ReviewForm(Form):
    """
    A form for validating reviews.
    """
    rating = SelectField('Rating', default='3', choices=[
        ('5', '5 - I had a very good experience'),
        ('4', '4 - I had a good experience'),
        ('3', '3 - I had a neutral experience'),
        ('2', '2 - I had a bad experience'),
        ('1', '1 - I had a very bad experience')
    ], validators=[validators.DataRequired()])

    # this is the text field with more details
    description = TextAreaField('My Experience', validators=[
        validators.DataRequired(), 
        validators.Length(1, 2000)])

    # the Resource been reviewed, this field is hidden
    # because we set in the templates, the user
    # doesn't actually have to select this
    provider = HiddenField(validators=[validators.DataRequired()])

    def validate_provider(self, field):
        """
        We want to make sure the provider
        been exists in our database. Even
        though we set this field ourselves,
        people can try to post with automated
        scripts.

        """
        if Resource.query.get(field.data) is None:
            raise ValidationError('No provider found.')
