from flask_wtf import Form
from wtforms import StringField, PasswordField, validators

class LoginForm(Form):
    email = StringField('email', [validators.Length(min=6, max=120), validators.Email()])
    password = PasswordField('password', [validators.Length(min=6, max=35)])

