"""
user_auth.py

This blueprint handles user authentication, everything
from sign up to log out. We use flask-login.

"""
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


@auth.route('/signup/', methods=['GET', 'POST'])
def sign_up():
    """
    Handles user signup.

    Associated template: create-account.html
    """
    form = SignUpForm()

    # Kick the current user back to the index
    # if they're already logged in
    if current_user.is_authenticated():
        return redirect(url_for('remedy.index'))

    if request.method == 'GET':
        return render_template('create-account.html', form=form)

    else:

        if form.validate_on_submit():

            u = User(form.username.data, form.email.data, form.password.data)
            db.session.add(u)
            db.session.commit()

            login_user(u, True)

            return redirect(url_for('remedy.index'))

        else:
            flash_errors(form)
            return render_template('create-account.html', form=form), 400


@auth.route('/login/', methods=['GET', 'POST'])
def sign_in():
    """
    Handles user sign-in.

    Associated template: login.html
    """
    form = LoginForm()


    # Kick the current user back to the index
    # if they're already logged in
    if current_user.is_authenticated():
        return redirect(url_for('remedy.index'))

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

            # We're good.
            login_user(user, True)
            return redirect(url_for('remedy.index'))

        flash_errors(form)
        return render_template('login.html', form=form), 401


@auth.route('/logout/', methods=['POST'])
@login_required
def log_out():
    """
    Handles user logouts.
    """
    logout_user()
    return redirect(url_for('remedy.index'))