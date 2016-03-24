import os
from flask import request, render_template, flash, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.bcrypt import Bcrypt
from app import app, db, login_manager
from .models import User, Certificate, Thing
from .forms import LoginForm, CertificateUploadForm, ThingForm
import sqlalchemy


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
def get_users():
    return render_template(
        'users.html',
        users=User.query.all())


@app.route("/certificates", methods=["GET"])
@login_required
def get_certificates():
    return render_template(
        'certificates.html',
        certificates=Certificate.query.all())


@app.route("/things", methods=["GET"])
@login_required
def get_things():
    return render_template(
        'things.html',
        things=Thing.query.all())


@app.route("/metrics", methods=["GET"])
@login_required
def get_metrics():
    return render_template(
        'metrics.html',
        things=Thing.query.all())


@app.route('/new-certificate', methods=["GET", "POST"])
def new_certificate():
    form = CertificateUploadForm()
    if request.method == 'POST':
        # validate uploads
        filedata = []
        two_good_files = True
        if form.validate_on_submit():
            for upload in form.uploads.entries:
                filedata.append(upload)
                if not upload.data.filename:  # file is invalid if filename empty
                    two_good_files = False
        if not two_good_files:
            flash("Must enter two files")
            return render_template('new-certificate.html', form=form)
        # store certificate record
        certificate = Certificate(name=form.name.data)
        db.session.add(certificate)
        db.session.commit()
        my_id = certificate.id
        # store the physical files not that I have an id
        filedata[0].data.save(os.path.join(app.config['CERTIFICATES_FOLDER'], str(my_id) + '-cert.pem'))
        filedata[1].data.save(os.path.join(app.config['CERTIFICATES_FOLDER'], str(my_id) + '-key.pem'))
        return render_template(
            'new-certificate.html',
            form=form,
            filedata=filedata)
    else:
        return render_template("new-certificate.html", form=form)


@app.route('/new-thing', methods=["GET", "POST"])
def new_thing():
    form = ThingForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            thing = Thing(name=form.name.data, endpoint=form.endpoint.data,
                          certificate=form.certificate.data)
            try:
                db.session.add(thing)
                db.session.commit()
                flash("%s added successfully" % thing.name)
            except sqlalchemy.exc.IntegrityError, exc:
                reason = exc.message
                if "UNIQUE constraint" in reason:
                    flash("%s already exists" % exc.params[0])
                db.session.rollback()

        return render_template(
            'new-thing.html',
            form=form)
    else:
        return render_template("new-thing.html", form=form)
