from app import app, db
from sqlalchemy import DateTime
import datetime
import requests
import os
import json
from publisher import Publisher

CERT = (os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], 'cert.pem'),
        os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], 'key.pem'))
HEADERS = {'Content-Type': 'application/json'}


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
        return '<id {}>'.format(self.id)


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
        return '<id {}>'.format(self.id)


class Metric(db.Model):
    __tablename__ = 'metrics'

    id = db.Column(db.Integer, primary_key=True)
    thing_id = db.Column(db.Integer, db.ForeignKey('things.id'), nullable=False)
    thing = db.relationship('Thing', back_populates=('metric'))

    @property
    def response(self):
        if not hasattr(self, 'resp'):
            self.resp = requests.get(self.thing.endpoint, cert=CERT, verify=True, headers=HEADERS)
        return self.resp

    @property
    def items(self):
        return self.response

    def __repr__(self):
        return '<id {}>'.format(self.id)


class Toggle(db.Model):
    __tablename__ = 'toggles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    ref_key = db.Column(db.String(50), nullable=False)
    ref_value = db.Column(db.String(100), nullable=False)
    style = db.Column(db.String(100), nullable=False)

    def toggle(self):
        data = dict()
        data[self.ref_key] = self.ref_value
        obj = []
        msg = json.dumps(data)
        obj.append({'topic': self.topic, 'payload': msg})
        Publisher(
            app.config['MQTT_ENDPOINT'],
            os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], 'rootCA.pem'),
            os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], 'key.pem'),
            os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], 'cert.pem')
        ).publish_multiple(obj)

    def __repr__(self):
        return '<id {}>'.format(self.id)
