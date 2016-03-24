from flask_wtf import Form
from wtforms import StringField, PasswordField, validators, FileField, FieldList, IntegerField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from .models import Certificate

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
    certificate = QuerySelectField(query_factory=enabled_certificates,
                            allow_blank=True)