RADRemedy
=

Front end for the radremedy project. Used to recommend health care providers to lgbtqi people

(Referral Aggregator Database)

RAD is a tool to curate referral information for multiple
agencies, improving their quality of data, avoiding duplication,
and sparing organizations from the time and expertise of managing
their referral data IT infrastructure.

Development began at Trans*h4ck Chicago 2014.

For Users
==

For Developers
==

See the [Contributing document](https://github.com/radremedy/radremedy/blob/master/CONTRIBUTING.md) if interest *after* reading this section.

This app is coded using python, [Flask](http://flask.pocoo.org/),
and a couple of [flask extensions](http://flask.pocoo.org/extensions/).
Make sure to learn Flask if you don't have any experience with it. It's
really easy to get started. Once the data is collected and added to the
database all is handed to client side code. The client side code
is all Javascript. We use [JQuery](http://jquery.com/) and
[Bootstrap](getbootstrap.com/).

Usage
===

```
# copy the project into your computer
git clone https://github.com/radremedy/radremedy
cd ./radremedy/

# install the requirements for the project
pip install -r requirements.txt
cd ./remedy

# create the database
python ./radremedy.py db upgrade
# there will be a bootstrap command here in the future
# run the app
python ./radremedy.py runserver

```

Then visit [http://localhost:5000/](http://localhost:5000/)

Runtime configurations
===

Looking at the `config.py` file you can see which environment
variables we look at. Currently we only look for `RAD_PRODUCTION`,
if this variable is available the app will not be ran in `debug`
mode. If it does exists(`export RAD_PRODUCTION=1`) then the app
will be ran in `debug` mode. It's very important to only do this
during development because of security reasons. In the future more
configurations will be added for database users and passwords.

Altering the Models
===

If you want to change something in the database models take
a look at the `models.py` file. The models are defined using
[Flask-SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/).
When you are done making changes run the database migration.
This makes it so that you can undo your changes without
breaking the data.

```
python ./radremedy.py db migrate
python ./radremedy.py db upgrade
```

Other people running your fork, will only have to run `upgrade`
because you already created the migration.

```
python ./radremedy.py db upgrade
```
