import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for
from flask_apscheduler import APScheduler
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager, login_user
from flask_migrate import Migrate
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy

current = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current)

from config import Config  # noqa: E402, I001

## Setup Scheduler Jobs ####################################################

scheduler = APScheduler()


# @scheduler.task('cron', id='refresh_oauth_token', minute='*')
@scheduler.task('interval', id='refresh_oauth_token', hours=1, misfire_grace_time=900)
def scheduled_token_refresh():
    with app.app_context():
        token = app.d2l_client.do_refresh()
        if token:
            print(f'Token checked at {datetime.now()} : Expires {token.expires_at} {token.created_at}')
        else:
            print(f'ERR: token could not be checked at {datetime.now()}')


def create_app():
    app = Flask(__name__)
    scheduler.init_app(app)

    return app


app = create_app()

app.config.from_object(Config)

alchemy_db = SQLAlchemy(app)

# Regex pattern - double quotes are intentional
CORS(app, resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']}})  # noqa: Q000

if app.config['RUNNING_IN_DOCKER']:
    from extensions import PrefixMiddleware

    app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=app.config['APPLICATION_ROOT'])

d2l_url = app.config['BASE_URL'] + 'd2l/home'


@app.context_processor
def inject_global_variables() -> dict:
    globals = {'d2l_url'}
    return {'globals': dict((k, eval(k)) for k in globals)}


from .d2l.client import Client  # noqa: E402, I001
from .db.client import DBClient  # noqa: E402, I001

mysql = MySQL(app)
app.d2l_client = Client(mysql, app.config)
app.db_client = DBClient(mysql, app.config)
app.mysql = mysql

login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

migrate = Migrate(app, alchemy_db)

from .site.routes import site as site_routes  # noqa: E402, I001
from .api.routes import api as api_routes  # noqa: E402, I001

# register the blueprints for this site
app.register_blueprint(site_routes)
app.register_blueprint(api_routes)

# add jinja additions
from .site.flask_jsglue import JSGlue  # noqa: E402, I001

jsglue = JSGlue(app)

from flask_moment import Moment  # noqa: E402, I001

moment = Moment(app)

from .db.models import User  # noqa: E402, I001

login_manager.session_protection = 'strong'
login_manager.login_view = 'site.system.login'
login_manager.login_message_category = 'danger'


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()


@login_manager.request_loader
def load_user_from_header(request):
    auth = request.authorization
    if not auth:
        return None

    user = User.query.filter_by(username=auth.username).first()
    if user:
        if bcrypt.check_password_hash(user.password, auth.password):
            login_user(user)
            user.last_login = datetime.now()
            user.login_count = 0
            alchemy_db.session.commit()
            return user
        else:
            # user exist but password is wrong - increase count
            user.login_count = user.login_count + 1
            alchemy_db.session.commit()
            return None
    else:
        return None


@login_manager.unauthorized_handler
def unauthorized():
    # Check if the requested URL starts with API
    if request.path.startswith('/api'):
        return 'Unauthorized', 401
    else:
        return redirect(url_for('site.system.login'))  # Redirect to the default login page


#### error handlers ###################################################
@app.errorhandler(401)
def unauthorized_page(error):
    return render_template('errors/401.html'), 401


@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error_page(error):
    return render_template('errors/500.html'), 500


## Start-up ###########################################################
notification_sent = Path('sent.eml')


def do_startup():
    if not notification_sent.exists():
        with app.app_context():  # Ensure an app context is active
            notification_sent.touch(exist_ok=True)
            print(f'Application Version: {app.config["VERSION"]}')
            # print(app.url_map)


# push context manually to app
with app.app_context():
    do_startup()
