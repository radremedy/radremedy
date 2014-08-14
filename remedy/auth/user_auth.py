from flask import render_template, Blueprint, redirect, url_for, request, current_app, session
from flask.ext.login import LoginManager, login_user, login_required, logout_user
from rad.models import User, db
from .forms import SignUpForm, LoginForm

auth = Blueprint('auth', __name__)
login_manager = LoginManager()
login_manager.login_view = 'auth.sign_in'


@login_manager.user_loader
def get_user(uid):
    return User.query.get(int(uid))


@auth.route('/signup/', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()

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
            print(form.errors)
            return render_template('create-account.html', form=form), 400


@auth.route('/login/', methods=['GET', 'POST'])
def sign_in():
    form = LoginForm()

    if request.method == 'GET':
        return render_template('login.html', form=form)

    else:
        if form.validate_on_submit():

            user = User.query.filter_by(username=form.username.data).first()

            if user is not None and user.verify_password(form.password.data):
                login_user(user, True)

                return redirect(url_for('remedy.index'))

        return render_template('login.html', form=form), 401


@auth.route('/logout/', methods=['POST'])
@login_required
def log_out():
    logout_user()
    return redirect(url_for('remedy.index'))