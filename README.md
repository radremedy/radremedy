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

See the projects [wiki](https://github.com/radremedy/radremedy/wiki) for more technical details.

This app is coded using python, [Flask](http://flask.pocoo.org/),
and a couple of [flask extensions](http://flask.pocoo.org/extensions/).
Make sure to learn Flask if you don't have any experience with it. It's
really easy to get started. Once the data is collected and added to the
database, it is handed to client side code. The client side code
is all Javascript. We use [JQuery](http://jquery.com/) and
[Bootstrap](getbootstrap.com/).

If you get lost in the directories, take a look at the [structure documentation](https://github.com/radremedy/radremedy/wiki/Structure-of-the-Project).

Runtime configurations
===

Looking at the `config.py` file you can see which environment
variables we look at. Currently, we look at 2 variables: `RAD_PRODUCTION`
and `RAD_DATA_BASE`. 

If `RAD_PRODUCTION` does not exist, the app will not be run in `debug`
mode. If it does exists(`export RAD_PRODUCTION=1`) then the app
will be ran in `debug` mode. It's very important to only do this
during development due to security concerns. In the future, more
configurations will be added for database users and passwords.

Another environment variable that we look for is `RAD_DATA_BASE`.
This variable must be set to the base of the directory containing
a copy of our folder on Dropbox. In the future it
might be in a separate repository. We use this to populate the database
during a bootstrapping phase, which only has to be run once.

On my computer, the variable is set like this:

```
echo export RAD_DATA_BASE="/home/wil/Data/Trans" >> ~/.bashrc
```

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

# Load some data into the database
# only run this if you have a copy of our data folder
python ./bootstrap.py

# if you don't, you still can get some data from the scrapers
# the bootstrap command will run the scrapers too
# after the first time, to update data run these scrapers
python ./get_save_data.py

# run the app
python ./radremedy.py runserver

```

Then visit [http://localhost:5000/](http://localhost:5000/)

Altering the Models
===

If you want to change something in the database models, take
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
