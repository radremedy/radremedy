from flask_wtf import Form
from wtforms import PasswordField, StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, Email
from rad.models import User


class BaseAuthForm(Form):

    _submit_text = 'Submit'

    username = StringField('Username', validators=[
        DataRequired(), Length(1, message='Username has to be at least 1 character'),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Username must have only letters, numbers, dots or underscores')
    ])

    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(8, message='Password must be longer than 8 letters.')
    ])

    submit = SubmitField(_submit_text)


class SignUpForm(BaseAuthForm):

    _submit_text = 'Sign Up!'

    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(1, 70)
    ])

    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),  EqualTo('password', message='Passwords must match.')
    ])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class LoginForm(BaseAuthForm):
    _submit_text = 'Login'
