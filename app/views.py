import os
from flask import request, render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from app import app, db, login_manager
from .models import User, Toggle
from .forms import LoginForm
import datetime
import json
import pytz
import boto3
import botocore
from boto3.dynamodb.conditions import Key, Attr
import pygal
import utils

DT_FORMAT = '%Y/%m/%d %-I:%M %p %Z'
TZ = pytz.timezone("America/New_York")


def get_all_the_things():
    client = boto3.client('iot', region_name=app.config['AWS_REGION'])
    response = client.list_things()
    things = response["things"]
    t = []
    for thing in things:
        t.append(thing['thingName'])
    return sorted(t)


def get_only_the_thing(thing):
    client = boto3.client('iot-data', region_name=app.config['AWS_REGION'])
    response = client.get_thing_shadow(thingName=thing)
    body = response["payload"]
    return json.loads(body.read())


@login_manager.user_loader
def load_user(email):
    return User.query.filter(User.email == email).first()


@app.errorhandler(401)
def unauthorized(error):
    return render_template('401.html'), 401


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', error=str(error)), 404


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


@app.route('/shadows/<thing>', methods=["GET"])
@app.route('/shadow/<thing>', methods=["GET"])
@app.route("/shadow", defaults={'thing': None}, methods=["GET"])
@app.route("/shadows", defaults={'thing': None}, methods=["GET"])
@login_required
def get_shadow(thing):
    things = get_all_the_things()
    if thing is None:
        thing = things[0]
    if thing not in things:
        return not_found_error("%s not found" % thing)
    try:
        ts = None
        t = get_only_the_thing(thing)
        if utils.has_key_chain(t, 'state', 'reported'):
            ts = t['timestamp']
        else:
            t = {}
        return render_template('shadow.html', name=thing, things=things, thing=t, ts=ts)
    except IOError as ex:
        return not_found_error("%s not found" % thing)
    except botocore.exceptions.ClientError as ex:
        return not_found_error("%s not found" % thing)


@app.route("/snapshots", methods=["GET"])
@login_required
def get_snapshots():
    s3 = boto3.client('s3')
    ext_list = ['.jpg', '.png', '.gif']
    data = []
    try:
        for key in s3.list_objects(Bucket=app.config['SNAPSHOT_BUCKET'])['Contents']:
            if os.path.splitext(os.path.basename(key['Key']))[1] in ext_list:
                name = os.path.basename(key['Key'])
                try:
                    url = s3.generate_presigned_url(
                        ClientMethod='get_object',
                        Params={
                            'Bucket': app.config['SNAPSHOT_BUCKET'],
                            'Key': key['Key']
                        }
                    )
                except Exception as e:
                    url = None
                data.append({'name': name.rsplit('.', 1)[0], 'url': url})
        return render_template('snapshots.html', snapshots=data)
    except Exception as ex:
        return not_found_error(str(ex))


@app.route("/toggles", defaults={'toggle_id': None}, methods=["GET", "POST"])
@app.route("/toggles/<int:toggle_id>", methods=["GET", "POST"])
@login_required
def get_toggles(toggle_id):
    try:
        if request.method == 'POST':
            toggle = Toggle.query.get(int(request.form['submit']))
            toggle.toggle()
            flash("%s fired" % toggle.title, 'success')
        if toggle_id:
            toggles = [Toggle.query.filter(Toggle.id == toggle_id).one()]
        else:
            toggles = Toggle.query.order_by("title").all()
        ts = datetime.datetime.now()
        return render_template('toggles.html', toggles=toggles, ts=ts)
    except Exception as e:
        return not_found_error(str(e))


# Ugly function to make y axis max range a bit more viewable
def axis_max_calc(v):
    pairs = [
        (1.00001, 1),
        (2, 2),
        (5, 5),
        (10.00001, 10),
        (20, 20),
        (25, 25),
        (30, 30),
        (40, 40),
        (50, 50),
        (100.00001, 100),
        (1000.00001, 1000),
        (10000.00001, 10000)
    ]
    for pair in pairs:
        if v < pair[0]:
            return pair[1]
    return v


@app.route('/graph/<string:thing>/<string:metric>')
@login_required
def graph_it(thing, metric, query_limit=4000):
    y_min = 0
    y_max = 0
    try:
        dynamodb = boto3.resource('dynamodb', region_name=app.config['AWS_REGION'])
        table = dynamodb.Table('sensors')
        response = table.query(
            KeyConditionExpression=Key('source').eq(thing),
            ScanIndexForward=False,
            FilterExpression=Attr('payload.state.reported.' + metric).exists(),
            Limit=query_limit
        )
        graph = pygal.DateTimeLine(show_legend=False,
                                   show_dots=False,
                                   x_label_rotation=35,
                                   truncate_label=-1,
                                   x_value_formatter=lambda dt: dt.strftime(DT_FORMAT))
        graph.title = metric
        x = []
        for i in response['Items']:
            v = i['payload']['state']['reported'][metric]
            if v is not None:
                x.append((datetime.datetime.fromtimestamp(float(i['timestamp']) / 1000.0).replace(
                    tzinfo=pytz.utc).astimezone(TZ),
                          v))
                if v > y_max:
                    y_max = v
                if v < y_min:
                    y_min = v
        graph.config.range = (y_min, axis_max_calc(y_max))
        graph.add(metric, x)
        graph_data = graph.render_data_uri()
        return render_template('graphing.html', graph_data=graph_data, thing=thing)
    except Exception as e:
        return internal_error(str(e))


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
