import os
from flask import request, render_template, flash, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.bcrypt import Bcrypt
from app import app, db, login_manager
from .models import User, Certificate, Thing, Metric, Toggle, Snapshot
from .forms import LoginForm, CertificateUploadForm, ThingForm, MetricForm, ToggleForm, SnapshotForm
import sqlalchemy
import datetime
from datetime import time
import pytz
import boto3
from boto3.dynamodb.conditions import Key, Attr
import pygal

DT_FORMAT = '%Y/%m/%d %-I:%M %p %Z'
TZ = pytz.timezone("America/New_York")

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
                flash("Successfully logged in as %s" % user.email, 'success')
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
    flash("User logged out", 'success')
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
        things=Thing.query.order_by("name").all())


@app.route("/metrics", methods=["GET"])
@login_required
def get_metrics():
    return render_template(
        'metrics.html',
        metrics=Metric.query.join(Thing, Metric.thing_id == Thing.id).order_by("things.name").all())


@app.route("/snapshots", methods=["GET", "POST"])
@login_required
def get_snapshots():
    s3 = boto3.client('s3')
    data = []
    for key in s3.list_objects(Bucket=app.config['S3_BUCKET'], Prefix='snapshots')['Contents']:
        if not key['Key'].endswith("/"):
            local_dt = key['LastModified'].replace(tzinfo=pytz.utc).astimezone(TZ)
            name = str(key['Key'].split('/')[-1])
            ts = TZ.normalize(local_dt)
            query = Snapshot.query.join(Thing).filter(Thing.name == name.rsplit('.', 1)[0])
            try:
                query.one()
                url = s3.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': app.config['S3_BUCKET'],
                        'Key': key['Key']
                    }
                )
            except:
                #  image is not part of snapshots
                url = None
            data.append({'name': name.rsplit('.', 1)[0], 'timestamp': ts, 'url': url})
    if request.method == 'POST':
        if 'submit' in request.form:
            snapshot = Snapshot.query.join(Thing).filter(Thing.name == request.form['submit']).first()
            snapshot.value = datetime.datetime.now().strftime("%s")
        return render_template(
            'snapshots.html',
            snapshots=data)
    else:
        return render_template(
            'snapshots.html',
            snapshots=data)


@app.route('/metrics/<int:metric_id>')
@login_required
def get_metric(metric_id):
    return render_template(
        'metric.html',
        metrics=Metric.query.join(Thing, Metric.thing_id == Thing.id).order_by("things.name").all(),
        metric=Metric.query.get(metric_id))


@app.route("/toggles", methods=["GET", "POST"])
@login_required
def get_toggles():
    if request.method == 'POST':
        toggle = Toggle.query.get(int(request.form['submit'].split('-', 1)[0]))
        toggle.value = request.form['submit'].split('-', 1)[1]
        return render_template(
            'toggles.html',
            toggles=Toggle.query.order_by("title").all())
    else:
        return render_template(
            'toggles.html',
            toggles=Toggle.query.order_by("title").all())


@app.route('/new-certificate', methods=["GET", "POST"])
@login_required
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
            flash("Must enter two files", 'warning')
            return render_template('new-certificate.html', form=form)
        # store certificate record
        certificate = Certificate(name=form.name.data)
        db.session.add(certificate)
        db.session.commit()
        # store the physical files not that I have an id
        filedata[0].data.save(os.path.join(app.config['CERTIFICATES_FOLDER'], str(certificate.id) + '-cert.pem'))
        filedata[1].data.save(os.path.join(app.config['CERTIFICATES_FOLDER'], str(certificate.id) + '-key.pem'))
        return render_template(
            'new-certificate.html',
            form=form,
            filedata=filedata)
    else:
        return render_template("new-certificate.html", form=form)


@app.route('/new-thing', methods=["GET", "POST"])
@login_required
def new_thing():
    form = ThingForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            thing = Thing(name=form.name.data, endpoint=form.endpoint.data,
                          certificate=form.certificate.data)
            try:
                db.session.add(thing)
                db.session.commit()
                flash("%s added successfully" % thing.name, 'success')
            except sqlalchemy.exc.IntegrityError, exc:
                reason = exc.message
                if "UNIQUE constraint" in reason:
                    flash("%s already exists" % exc.params[0], 'danger')
                db.session.rollback()

        return render_template(
            'new-thing.html',
            form=form)
    else:
        return render_template("new-thing.html", form=form)


@app.route('/new-snapshot', methods=["GET", "POST"])
@login_required
def new_snapshot():
    form = SnapshotForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            snapshot = Snapshot(thing=form.thing.data)
            try:
                db.session.add(snapshot)
                db.session.commit()
                flash("%s added successfully" % snapshot.thing.name, 'success')
            except sqlalchemy.exc.IntegrityError, exc:
                reason = exc.message
                if "NOT NULL constraint" in reason:
                    flash("Snapshot already exists", 'danger')
                db.session.rollback()

        return render_template(
            'new-snapshot.html',
            form=form)
    else:
        return render_template("new-snapshot.html", form=form)


@app.route('/new-metric', methods=["GET", "POST"])
@login_required
def new_metric():
    form = MetricForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            metric = Metric(thing=form.thing.data)
            try:
                db.session.add(metric)
                db.session.commit()
                flash("%s added successfully" % metric.thing.name, 'success')
            except sqlalchemy.exc.IntegrityError, exc:
                reason = exc.message
                if "NOT NULL constraint" in reason:
                    flash("Metric already exists", 'danger')
                db.session.rollback()

            return render_template(
                'new-metric.html',
                form=form)
    else:
        return render_template("new-metric.html", form=form)


@app.route('/new-toggle', methods=["GET", "POST"])
@login_required
def new_toggle():
    form = ToggleForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            toggle = Toggle(title=form.title.data, refkey=form.refkey.data,
                            on_str=form.on_str.data, off_str=form.off_str.data,
                            thing=form.thing.data)
            try:
                db.session.add(toggle)
                db.session.commit()
                flash("Added successfully", 'success')
            except sqlalchemy.exc.IntegrityError, exc:
                reason = exc.message
                if "UNIQUE constraint" in reason:
                    flash("%s already exists" % exc.params[0], 'danger')
                db.session.rollback()

        return render_template(
            'new-toggle.html',
            form=form)
    else:
        return render_template("new-toggle.html", form=form)


@app.route('/graph/<string:thing>/<string:metric>')
@login_required
def graph_it(thing, metric):
    try:
        dynamodb = boto3.resource('dynamodb', region_name=app.config['CERTIFICATES_FOLDER'])
        table = dynamodb.Table('sensors')
        response = table.query(
            KeyConditionExpression=Key('source').eq(thing),
            ScanIndexForward=False,
            FilterExpression=Attr('payload.state.reported.' + metric).exists(),
            Limit=2016
        )
        graph = pygal.DateTimeLine(show_legend=False, show_dots=False, x_label_rotation=35, truncate_label=-1,
                                   x_value_formatter=lambda dt: dt.strftime(DT_FORMAT))
        graph.title = metric
        x = []
        for i in response['Items']:
            x.append((datetime.datetime.fromtimestamp(float(i['timestamp']) / 1000.0),
                      i['payload']['state']['reported'][metric]))
        graph.add(metric, x)
        graph_data = graph.render_data_uri()
        return render_template('graphing.html', graph_data=graph_data)
    except Exception, e:
        return (str(e))


@app.template_filter('dt')
def _jinja2_filter_datetime(date, fmt=None):
    if fmt:
        return date.strftime(fmt)
    else:
        return date.strftime(DT_FORMAT)


@app.template_filter('ts')
def _jinja2_filter_timestamp(timestamp, fmt=None):
    if fmt:
        return datetime.datetime.fromtimestamp(timestamp, TZ).strftime(fmt)
    else:
        return datetime.datetime.fromtimestamp(timestamp, TZ).strftime(DT_FORMAT)
