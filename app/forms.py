from flask_wtf import Form
from wtforms import StringField, PasswordField, validators, FileField, FieldList

class LoginForm(Form):
    email = StringField('email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('password', [validators.Length(min=6, max=35)])

class CertificateUploadForm(Form):
    name = StringField('name',[validators.Optional(), validators.Length(max=50)])
    uploads = FieldList(FileField())
