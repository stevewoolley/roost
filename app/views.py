from flask import render_template, flash, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.bcrypt import Bcrypt
from app import app, db, login_manager
from .models import User, Certificate, Thing
from .forms import LoginForm, FileUploadForm


@login_manager.user_loader
def load_user(email):
    return User.query.filter(User.email == email).first()


@app.errorhandler(401)
def unauthorized(error):
    return render_template('401.html'), 401


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""
    bcrypt = Bcrypt(app)
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.get(form.email.data)
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data) and user.is_active:
                flash("Successfully logged in as %s" % user.email)
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                return redirect(url_for('index'))
            else:
                if user.is_active:
                    form.password.errors.append('invalid')
                else:
                    form.password.errors.append('locked')
    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the current user."""
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    flash("User logged out")
    return redirect(url_for('index'))


@app.route("/users", methods=["GET"])
@login_required
def users():
    return render_template(
        'users.html',
        users=User.query.all())


@app.route("/certificates", methods=["GET"])
@login_required
def certificates():
    return render_template(
        'certificates.html',
        certificates=Certificate.query.all())


@app.route("/things", methods=["GET"])
@login_required
def things():
    return render_template(
        'things.html',
        things=Thing.query.all())


@app.route('/upload', methods=("GET", "POST",))
def upload():
    form = FileUploadForm()
    for i in xrange(2):
        form.uploads.append_entry()
    filedata = []
    if form.validate_on_submit():
        for upload in form.uploads.entries:
            filedata.append(upload)
    return render_template("upload.html",
                           form=form,
                           filedata=filedata)
