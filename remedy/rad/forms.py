from flask_wtf import Form
from .models import Resource
from wtforms import TextField, TextAreaField, SubmitField, validators, ValidationError, \
   HiddenField, SelectField


class ContactForm(Form):
    name = TextField("Your Name")
    email = TextField("Your Email", [validators.Optional(), validators.Email("Please enter a valid email address.")])
    message = TextAreaField("Message", [validators.Required("Message field is required.")])

    submit = SubmitField("Send")


class ReviewForm(Form):
    """
    A form for validating reviews.
    """
    # this is the little drop down input
    # a user might select from

    rating = SelectField('I had a', choices=[
        (1, 'good'),
        (0, 'neutral'),
        (-1, 'bad')

    ], validators=[validators.DataRequired()])

    # this is the text field with more details
    description = TextAreaField(validators=[validators.DataRequired(), validators.Length(1, 180)])

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
