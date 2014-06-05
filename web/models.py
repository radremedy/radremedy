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
    category = db.Column(db.UnicodeText)
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
