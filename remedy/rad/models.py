"""
models.py

Defines the database models.

"""
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
import bcrypt

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
    
    fulladdress = db.Column(db.UnicodeText)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    date_created = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
                               backref=db.backref('resources',
                                                  lazy='dynamic'))

    def __unicode__(self):
        return self.name


class Category(db.Model):
    """
    All the resources belong to a category.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, unique=True)

    def __unicode__(self):
        return self.name or 'No category name'


class User(UserMixin, db.Model):
    """
    A RAD user.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.UnicodeText, nullable=False)
    password = db.Column(db.Unicode(128), nullable=False, server_default="")
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

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password, bcrypt.gensalt())

    def verify_password(self, password):
        return bcrypt.hashpw(password, self.password) == self.password

    def __unicode__(self):
        return self.username


class Review(db.Model):
    """
    A user will be able to leave reviews of the resources.

    """
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.UnicodeText)

    experience = db.Column(db.Unicode(10))

    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'))
    resource = db.relationship('Resource',
                               backref=db.backref('reviews',
                                                  lazy='dynamic'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('reviews',
                                              lazy='dynamic'))

    date_created = db.Column(db.DateTime)

    def __unicode__(self):
        return self.text

    def __init__(self, experience, text, resource, user):
        self.text = text
        self.experience = experience
        self.resource = resource
        self.user = user

