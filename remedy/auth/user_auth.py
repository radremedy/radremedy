"""
user_auth.py

This blueprint handles user authentication, everything
from sign up to log out. We use flask-login.

"""
from datetime import date, timedelta

from flask import render_template, Blueprint, redirect, url_for, request, current_app, session, flash
from flask.ext.login import LoginManager, login_user, login_required, logout_user, current_user
from remedy.rad.models import User, db
from .forms import SignUpForm, LoginForm
from remedy.remedyblueprint import flash_errors

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

            u = User(form.username.data, form.email.data, form.password.data)
            # TODO: Copy over display name
            db.session.add(u)
            db.session.commit()

            # TODO: Generate a code and send a confirmation email
            # instead of logging in the user.
            login_user(u, True)

            return index_redirect()

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
                flash("Your account must first be confirmed. Please check your email for the confirmation link.")
                return render_template('login.html', form=form), 401               

            # We're good.
            login_user(user, True)
            return index_redirect()

        flash_errors(form)
        return render_template('login.html', form=form), 401


@auth.route('/logout/', methods=['POST'])
@login_required
def log_out():
    """
    Handles user logouts.
    """
    logout_user()
    return index_redirect()


@auth.route('/confirm-account/<code>/')
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
    activate_user = User.query. \
        filter_by(email_code=code). \
        filter_by(email_activated=False). \
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
        login_user(user, True)
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
    # Kick the current user back to the index
    # if they're already logged in
    if current_user.is_authenticated():
        return index_redirect()

    # TODO
    pass


@auth.route('/reset-password/<code>', methods=['GET', 'POST'])
def reset_password(code):
    """
    Resets a password.

    Associated template: password-reset.html
    Associated form: PasswordResetForm

    Args:
        code: The activation code, sent through email.    
    """
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
    reset_user = User.query. \
        filter_by(email_code=code). \
        filter_by(email_activated=True). \
        first()

    # Make sure we have a user.
    if reset_user is None:
        flash('The provided reset code is invalid.')
        return login_redirect()

    # Only allow codes to be used for 48 hours
    min_reset_date = datetime.utcnow() - datetime.timedelta(days=2)

    if reset_user.reset_pass_date is None or \
        reset_user.reset_pass_date < min_reset_date:
        flash('The reset code is invalid or has expired. You must request a new code.')
        return redirect(url_for('auth.request_password_reset'))

    # TODO
    pass

@auth.route('/change-password/', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Changes a password.

    Associated template: change-password.html
    Associated form: PasswordResetForm   
    """
    # TODO
    pass