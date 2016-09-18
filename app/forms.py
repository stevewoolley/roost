from flask_wtf import Form
from wtforms import StringField, PasswordField, validators, IntegerField


class LoginForm(Form):
    email = StringField('email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('password', [validators.Length(min=6, max=35)])


class ToggleForm(Form):
    title = StringField('title', [validators.InputRequired(), validators.Length(max=100)])
    topic = StringField('topic', [validators.InputRequired(), validators.Length(max=200)])
    ref_key = StringField('ref_key', [validators.InputRequired(), validators.Length(max=50)])
    ref_value = StringField('ref_value', [validators.InputRequired(), validators.Length(max=100)])
    style = StringField('style', [validators.InputRequired(), validators.Length(max=100)])
