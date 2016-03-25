from app import app, db
from sqlalchemy import DateTime
import datetime
import requests
import os

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

    def __repr__(self):
        return self.name


class Thing(db.Model):
    __tablename__ = 'things'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    endpoint = db.Column(db.String(250), nullable=False)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id'))
    certificate = db.relationship('Certificate',
                                  backref=db.backref('things', lazy='dynamic'))
    metric = db.relationship('Metric', uselist=False, back_populates='thing')

    def __repr__(self):
        return self.name


class Metric(db.Model):
    __tablename__ = 'metrics'

    id = db.Column(db.Integer, primary_key=True)
    thing_id = db.Column(db.Integer, db.ForeignKey('things.id'), nullable=False)
    thing = db.relationship('Thing', back_populates=('metric'))

    @property
    def items(self):
        cert = (os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-cert.pem'),
                os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-key.pem'))
        headers = {'Content-Type': 'application/json'}
        response = requests.get(self.thing.endpoint, cert=cert, verify=True, headers=headers)

        return response

    def __repr__(self):
        return self.thing.name
