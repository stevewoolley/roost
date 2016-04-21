from flask_wtf import Form
from wtforms import StringField, PasswordField, validators, FileField, FieldList, IntegerField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from .models import Certificate, Thing


class LoginForm(Form):
    email = StringField('email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('password', [validators.Length(min=6, max=35)])


class CertificateUploadForm(Form):
    name = StringField('name', [validators.Optional(), validators.Length(max=50)])
    uploads = FieldList(FileField())


def enabled_certificates():
    return Certificate.query.all()


class ThingForm(Form):
    name = StringField('name', [validators.InputRequired(), validators.Length(max=50)])
    endpoint = StringField('endpoint', [validators.InputRequired(), validators.Length(max=250), validators.URL()])
    certificate = QuerySelectField(query_factory=enabled_certificates, get_label='name',
                                   allow_blank=False)


def enabled_things():
    return Thing.query.all()


class MetricForm(Form):
    thing_id = IntegerField('thing_id')
    thing = QuerySelectField(query_factory=enabled_things, get_label='name',
                             allow_blank=False)


class SnapshotForm(Form):
    thing_id = IntegerField('thing_id')
    thing = QuerySelectField(query_factory=enabled_things, get_label='name',
                             allow_blank=False)


class ToggleForm(Form):
    title = StringField('title', [validators.InputRequired(), validators.Length(max=100)])
    refkey = StringField('refkey', [validators.InputRequired(), validators.Length(max=50)])
    on_str = StringField('on_str', [validators.InputRequired(), validators.Length(max=50)])
    off_str = StringField('off_str', [validators.InputRequired(), validators.Length(max=50)])
    thing_id = IntegerField('thing_id')
    thing = QuerySelectField(query_factory=enabled_things, get_label='name',
                             allow_blank=False)
