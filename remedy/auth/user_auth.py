"""
user_auth.py

This blueprint handles user authentication, everything
from sign up to log out. We use flask-login.

"""
from datetime import date, datetime, timedelta
from uuid import uuid4

from flask import render_template, Blueprint, redirect, url_for, request, current_app, session, flash
from flask.ext.login import LoginManager, login_user, login_required, logout_user, current_user

import bcrypt

from remedy.remedyblueprint import flash_errors
from remedy.email_utils import send_confirm_account, send_password_reset
from remedy.rad.models import User, db
from .forms import SignUpForm, LoginForm, RequestPasswordResetForm, PasswordResetForm, PasswordChangeForm

auth = Blueprint('auth', __name__)
login_manager = LoginManager()
login_manager.login_view = 'auth.sign_in'

@login_manager.user_loader
def get_user(uid):
    """
    Gets the user by their ID, as required by flask-login.

    Args:
        uid: The user ID, which will be treated as an int.

    Returns:
        The specified user, or None if not found.
    """
    return User.query.get(int(uid))


def index_redirect():
    """
    Returns a redirection action to the main index page.

    Returns:
        The redirection action.
    """
    return redirect(url_for('remedy.index'))


def login_redirect():
    """
    Returns a redirection action to the login page.

    Returns:
        The redirection action.
    """
    return redirect(url_for('auth.sign_in'))


@auth.route('/signup/', methods=['GET', 'POST'])
def sign_up():
    """
    Handles user signup.

    Associated template: create-account.html
    Associated form: SignUpForm
    """
    form = SignUpForm()

    # Kick the current user back to the index
    # if they're already logged in
    if current_user.is_authenticated():
        return index_redirect()

    if request.method == 'GET':
        return render_template('create-account.html', form=form)

    else:

        if form.validate_on_submit():

            # Create the user.
            u = User(form.username.data, form.email.data, form.password.data)

            # Copy over display name and generate a code.
            u.display_name = form.display_name.data
            u.email_code = str(uuid4())
            u.email_activated = False

            # Save the user and send a confirmation email.
            db.session.add(u)
            db.session.commit()

            send_confirm_account(u)

            # Display the success page
            return render_template('create-account-success.html')

        else:
            flash_errors(form)
            return render_template('create-account.html', form=form), 400


@auth.route('/login/', methods=['GET', 'POST'])
def sign_in():
    """
    Handles user sign-in.

    Associated template: login.html
    Associated form: LoginForm
    """
    form = LoginForm()

    # Kick the current user back to the index
    # if they're already logged in
    if current_user.is_authenticated():
        return index_redirect()

    if request.method == 'GET':
        return render_template('login.html', form=form)
    else:
        if form.validate_on_submit():

            # Look up the user
            user = User.query.filter_by(username=form.username.data).first()

            # Make sure the user exists and the password is correct.
            if user is None or not user.verify_password(form.password.data):
                flash("Invalid username or password.")
                return render_template('login.html', form=form), 401

            # Lock out inactive users.
            if not user.active:
                flash("Your account is currently inactive.")
                return render_template('login.html', form=form), 401

            # Lock out users who haven't confirmed their account
            if not user.email_activated:
                flash("Your account must first be confirmed. Please check your email (" + \
                    user.email + ") for the confirmation link.")
                return render_template('login.html', form=form), 401               

            # We're good.
            login_user(user, True)
            return index_redirect()

        else:
            flash_errors(form)
            return render_template('login.html', form=form), 400


@auth.route('/logout/', methods=['POST'])
@login_required
def log_out():
    """
    Handles user logouts.
    """
    logout_user()
    return index_redirect()


@auth.route('/confirm-account/<code>')
def confirm_account(code):
    """
    Confirms an account.

    Args:
        code: The activation code, sent through email.

    Returns:
        The appropriate redirection to the main page, if successful,
        or to the login form, if unsuccessful.
    """
    # Kick the current user back to the index
    # if they're already logged in
    if current_user.is_authenticated():
        return index_redirect()

    # Normalize our code
    code = code.strip().lower()

    if not code:
        flash('An activation code was not provided.')
        return login_redirect()

    # Find the user based on the code and if they haven't activated yet
    activate_user = db.session.query(User). \
        filter(User.email_code == code). \
        filter(User.email_activated == False). \
        first()

    # Make sure we have a user.
    if activate_user is None:
        flash('The provided confirmation code is invalid.')
        return login_redirect()

    # Mark the account as activated
    activate_user.email_activated = True
    activate_user.email_code = None
    db.session.commit()

    # If the user's active, log them in - otherwise, flash a message
    # that indicates their account is inactive
    if activate_user.active:
        login_user(activate_user, True)
        flash('Your account was successfully confirmed!')
        return index_redirect()
    else:
        flash('Your account was successfully confirmed, but your account has been deactivated.')
        return login_redirect()


@auth.route('/request-reset/', methods=['GET', 'POST'])
def request_password_reset():
    """
    Requests a password reset.

    Associated template: request-password-reset.html
    Associated form: RequestPasswordResetForm
    """
    form = RequestPasswordResetForm()

    # Kick the current user back to the index
    # if they're already logged in
    if current_user.is_authenticated():
        return index_redirect()

    if request.method == 'GET':
        return render_template('request-password-reset.html', form=form)
    else:
        if form.validate_on_submit():

            # Look up the user.
            user = User.query.filter_by(username=form.username.data).first()

            # Make sure the user exists.
            if user is None:
                flash('Invalid username.')
                return render_template('request-password-reset.html', form=form), 401

            # Make sure the user's email has been activated.
            if user.email_activated == False:
                flash('You must first activate your account. Check your email for the confirmation link.')
                return login_redirect(), 401

            # Generate a code and update the reset date.
            user.email_code = str(uuid4())
            user.reset_pass_date = datetime.utcnow()

            # Save the user and send a confirmation email.
            db.session.commit()
            send_password_reset(user)

            # Flash a message and redirect the user to the 
            flash('Your password reset was successfully requested. Check your email for the link.')
            return login_redirect()

        else:
            flash_errors(form)
            return render_template('request-password-reset.html', form=form), 400


@auth.route('/reset-password/<code>', methods=['GET', 'POST'])
def reset_password(code):
    """
    Resets a password.

    Associated template: password-reset.html
    Associated form: PasswordResetForm

    Args:
        code: The activation code, sent through email.    
    """
    form = PasswordResetForm()

    # Kick the current user back to the index
    # if they're already logged in
    if current_user.is_authenticated():
        return index_redirect()

    # Normalize our code
    code = code.strip().lower()

    if not code:
        flash('A password reset code was not provided.')
        return login_redirect()

    # Find the user based on the code and if they're already activated
    reset_user  = db.session.query(User). \
        filter(User.email_code == code). \
        filter(User.email_activated == True). \
        first()

    # Make sure we have a user.
    if reset_user is None:
        flash('The provided reset code is invalid.')
        return login_redirect()

    # Only allow codes to be used for 48 hours
    min_reset_date = datetime.utcnow() - timedelta(days=2)

    if reset_user.reset_pass_date is None or \
        reset_user.reset_pass_date < min_reset_date:
        flash('The reset code is invalid or has expired. You must request a new code.')
        return redirect(url_for('auth.request_password_reset'))

    if request.method == 'GET':
        return render_template('password-reset.html', form=form, code=code)
    else:
        if form.validate_on_submit():

            # Set the new password
            reset_user.password = bcrypt.hashpw(form.password.data, bcrypt.gensalt())

            # Clear the email code and reset date
            reset_user.email_code = None
            reset_user.reset_pass_date = None

            # Save the user and log them in.
            db.session.commit()
            login_user(reset_user, True)

            # Flash a message and redirect the user to the index
            flash('Your password has been successfully reset!')
            return index_redirect()

        else:
            flash_errors(form)
            return render_template('password-reset.html', form=form, code=code), 400


@auth.route('/change-password/', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Changes a password.

    Associated template: change-password.html
    Associated form: PasswordChangeForm   
    """
    form = PasswordChangeForm()

    if request.method == 'GET':
        return render_template('change-password.html', form=form)
    else:
        if form.validate_on_submit():

            if not current_user.verify_password(form.currentpassword.data):
                flash('The current password you have provided is incorrect.')
                return render_template('change-password.html', form=form), 400

            # Set the new password
            current_user.password = bcrypt.hashpw(form.password.data, bcrypt.gensalt())

            # Save the user and log them in.
            db.session.commit()

            # Flash a message and redirect the user to the settings page
            flash('Your password has been successfully changed!')
            return redirect(url_for('remedy.settings'))

        else:
            flash_errors(form)
            return render_template('change-password.html', form=form), 400    
