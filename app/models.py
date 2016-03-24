from app import db
from sqlalchemy import DateTime
import datetime


class User(db.Model):
    __tablename__ = 'users'

    email = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=False)
    admin = db.Column(db.Boolean, default=False)

    @property
    def is_authenticated(self):
        return self.authenticated

    @property
    def is_active(self):
        return self.active

    @property
    def is_admin(self):
        return self.admin

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.email

    def __repr__(self):
        return self.email


class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    created_at = db.Column('created_at', DateTime, default=datetime.datetime.now)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

class Thing(db.Model):
    __tablename__ = 'things'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    endpoint = db.Column(db.String(250), nullable=False)
    created_at = db.Column('created_at', DateTime, default=datetime.datetime.now)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id'))
    certificate = db.relationship('Certificate',
                               backref=db.backref('things', lazy='dynamic'))

    def __repr__(self):
        return '<Thing %r>' % self.name
