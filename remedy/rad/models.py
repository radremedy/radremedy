"""
models.py
Defines the database models.

"""
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Resource(db.Model):
    """
    A resource used to recommend health care
    providers to L.G.B.T.Q.I.A people.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    street = db.Column(db.UnicodeText)
    city = db.Column(db.UnicodeText)
    state = db.Column(db.UnicodeText)
    country = db.Column(db.UnicodeText)
    zipcode = db.Column(db.UnicodeText)
    email = db.Column(db.UnicodeText)
    phone = db.Column(db.UnicodeText)
    fax = db.Column(db.UnicodeText)
    url = db.Column(db.UnicodeText)
    description = db.Column(db.UnicodeText)
    source = db.Column(db.UnicodeText)

    visable = db.Column(db.Boolean)

    date_created = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
                               backref=db.backref('resources',
                                                  lazy='dynamic'))


class Category(db.Model):
    """
    All the resources belong to a category.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, unique=True)


class User(db.Model):
    """
    A RAD user.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.UnicodeText, nullable=False)
    email = db.Column(db.UnicodeText, nullable=False)
    gender_identity = db.Column(db.UnicodeText)
    pronouns = db.Column(db.UnicodeText)
    date_of_birth = db.Column(db.DateTime)
    # TODO: how big is a race?
    # TODO: is this going to be a ENUM(choices)?
    race = db.Column(db.Unicode(20))
    # TODO: is this going to be a ENUM(choices)?
    sexual_orientation = db.Column(db.UnicodeText)
    city = db.Column(db.UnicodeText)
    # we limit the state column to be only two
    # characters because, we are only
    # using state abbreviations
    # we won't we in trouble as long
    # as we only have users in the United States
    # and the United States doesn't take over the world
    # needing more than two letter abbreviations to states
    state = db.Column(db.Unicode(2))



