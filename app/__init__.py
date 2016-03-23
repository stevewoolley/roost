from flask import Flask, flash, redirect, url_for, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from oauth import OAuthSignIn
from flask.ext.login import LoginManager


app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

lm = LoginManager(app)
lm.init_app(app)
lm.login_view = 'index'

from app import views, models