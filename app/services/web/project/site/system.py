# ruff: noqa: E402, I001
from datetime import datetime
from urllib.parse import urljoin, urlparse

from flask import abort, Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from project.app import alchemy_db as db, bcrypt
from ..db.models import User
from ..forms.forms import LoginForm, RegisterForm
from ..utils import Utils

system = Blueprint('system', __name__)

@system.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.is_authenticated and not current_user.is_admin:
        return redirect(url_for('site.index'))

    form = RegisterForm(request.form)
    if form.validate_on_submit():
        user = User(name=form.name.data, username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('site.index'))

    return render_template('system/register.html', form=form, year= datetime.now().year)

@system.route('/setup', methods=['GET', 'POST'])
def setup():
    if current_user.is_authenticated and not current_user.is_admin:
        print('You are already registered.')
        flash('You are already registered.', 'info')
        return redirect(url_for('site.index'))

    form = RegisterForm(request.form)
    if form.validate_on_submit():
        user = User(name=form.name.data, username=form.username.data, password=form.password.data, is_admin=True)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        user.last_login = datetime.now()
        user.login_count = 0
        db.session.commit()

        print('You registered and are now logged in. Welcome!')
        flash('You registered and are now logged in. Welcome!', 'success')
        return redirect(url_for('site.index'))

    return render_template('system/register.html', form=form, year= datetime.now().year)

@system.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('site.index'))

    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            user.last_login = datetime.now()
            user.login_count = 0
            db.session.commit()

            next = request.args.get('next')
            # is_safe_url should check if the url is safe for redirects.
            # See http://flask.pocoo.org/snippets/62/ for an example.
            if not is_safe_url(next):
                return abort(400)

            return redirect(next or url_for('site.index'))
        else:
            user.login_count = user.login_count + 1
            db.session.commit()
            return render_template('system/login.html',
                                    form=form,
                                    year= datetime.now().year,
                                    error='Invalid staff number and/or password.')

    # check to see if there is an admin user for the system
    # if not then we force the creation of one
    has_admin = user = User.query.filter_by(is_admin=True).first()
    if not has_admin:
        return redirect(url_for('system.setup'))

    return render_template('system/login.html', form=form, year= datetime.now().year)

@system.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You were logged out.', 'success')
    return redirect(url_for('site.system.login'))

@system.get('/me')
def me():
    if current_user.is_authenticated:
        return (
            jsonify(
                {
                    'status': 'success',
                    'message': 'User logged in successfully',
                    'data': {
                        'name': current_user.name,
                        'username': current_user.username,
                        'is_admin': current_user.is_admin
                    },
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    'status': 'ERR',
                    'message': 'Not authenticated',
                }
            ),
            400,
        )

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

# DataTable - retrieve the Call log for the DataTable JS class
@system.route('/logs', methods=['POST'])
@login_required
def get_call_logs_ajax():
    data = Utils.parse_request_data(request)
    if data is None:
        return 'Invalid content type', 400

    active_status = data.get('status', 'All').split(',')

    print( active_status )

    order_details = Utils.get_order_column_name(data.get('order'), data.get('columns'))
    return current_app.db_client.logs.get_logs(  active_status = ['All'],
                                                    draw = data.get('draw', 1),
                                                    start = data.get('start', 0),
                                                    length = data.get('length', 20),
                                                    order_column = order_details[0],
                                                    order_dir = order_details[1],
                                                    search_st = data['search']['value'],
                                                    search_regex = data['search']['regex'])
