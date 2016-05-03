from app import app, db
from sqlalchemy import DateTime
import datetime
import requests
import os
import json
import logging

def set_logger(name='iot', level=logging.INFO):
    logging.basicConfig(level=level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        filename="/var/log/%s.log" % (name),
                        filemode='a')
    return logging.getLogger()

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
    snapshot = db.relationship('Snapshot', uselist=False, back_populates='thing')


def __repr__(self):
    return '<id {}>'.format(self.id)


class Metric(db.Model):
    __tablename__ = 'metrics'

    id = db.Column(db.Integer, primary_key=True)
    thing_id = db.Column(db.Integer, db.ForeignKey('things.id'), nullable=False)
    thing = db.relationship('Thing', back_populates=('metric'))

    @property
    def response(self):
        cert = (os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-cert.pem'),
                os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-key.pem'))
        headers = {'Content-Type': 'application/json'}
        if not hasattr(self, 'resp'):
            self.resp = requests.get(self.thing.endpoint, cert=cert, verify=True, headers=headers)
        return self.resp

    @property
    def items(self):
        return self.response

    def __repr__(self):
        return '<id {}>'.format(self.id)


class Toggle(db.Model):
    __tablename__ = 'toggles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    refkey = db.Column(db.String(50), nullable=False)
    on_str = db.Column(db.String(50), nullable=False)
    off_str = db.Column(db.String(50), nullable=False)
    thing_id = db.Column(db.Integer, db.ForeignKey('things.id'), nullable=False)
    thing = db.relationship('Thing', backref=db.backref('toggles', lazy='dynamic'))

    @property
    def response(self):
        cert = (os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-cert.pem'),
                os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-key.pem'))
        headers = {'Content-Type': 'application/json'}
        if not hasattr(self, 'resp'):
            self.resp = requests.get(self.thing.endpoint, cert=cert, verify=True, headers=headers)
        return self.resp

    @property
    def value(self):
        if self.refkey in self.response.json()['state']['reported']:
            return self.response.json()['state']['reported'][self.refkey]
        else:
          return None

    @value.setter
    def value(self, v):
        cert = (os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-cert.pem'),
                os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-key.pem'))
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({'state': {'desired': {self.refkey: v}}})
        self.logger.info("Toggle(value.setter): %s %s %s %s" % (str(self.thing.endpoint), str(payload), str(cert), str(headers)))
        requests.post(self.thing.endpoint, data=payload, cert=cert, verify=True, headers=headers)

    @property
    def not_value(self):
        if self.value == self.on_str:
            return self.off_str
        else:
            return self.on_str

    def __repr__(self):
        return '<id {}>'.format(self.id)


class Snapshot(db.Model):
    __tablename__ = 'snapshots'

    self.logger = set_logger()

    id = db.Column(db.Integer, primary_key=True)
    thing_id = db.Column(db.Integer, db.ForeignKey('things.id'), nullable=False)
    thing = db.relationship('Thing', back_populates=('snapshot'))

    @property
    def response(self):
        cert = (os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-cert.pem'),
                os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-key.pem'))
        headers = {'Content-Type': 'application/json'}
        if not hasattr(self, 'resp'):
            self.resp = requests.get(self.thing.endpoint, cert=cert, verify=True, headers=headers)
        return self.resp

    @property
    def value(self):
        return self.response.json()['state']['reported'][self.refkey]

    @value.setter
    def value(self, v):
        cert = (os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-cert.pem'),
                os.path.join(app.config['CERTIFICATES_BASE_FOLDER'], str(self.thing.certificate.id) + '-key.pem'))
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({'state': {'desired': {'snapshot': v}}})
        self.logger.info("Snapshot(value.setter): %s %s %s %s %s" % (str(self.thing.endpoint), str(payload), str(cert), str(headers)))
        requests.post(self.thing.endpoint, data=payload, cert=cert, verify=True, headers=headers)

    def __repr__(self):
        return '<id {}>'.format(self.id)
