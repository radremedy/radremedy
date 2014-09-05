from flask_wtf import Form
from wtforms import TextField, TextAreaField, SubmitField, validators, ValidationError

class ContactForm(Form):
    name = TextField("Your Name")
    email = TextField("Your Email", [validators.Optional(), validators.Email("Please enter a valid email address.")])
    message = TextAreaField("Message", [validators.Required("Message field is required.")])
    submit = SubmitField("Send")