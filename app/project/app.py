import os
import unittest
import logging

from flask import Flask, render_template, request, abort, url_for, redirect
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager, login_user
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_mysqldb import MySQL

from datetime import datetime
from pathlib import Path

from .config import Config

app = Flask(__name__)
app.config.from_object(Config)

alchemy_db = SQLAlchemy(app)

CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

if app.config['SERVER_TYPE'] == 'test':
    print('-----------------------------Running tests--------------------------------')
    tests = unittest.TestLoader().discover("project/tests")
    unittest.TextTestRunner().run(tests)
    print('-----------------------------Tests ended--------------------------------')

if app.config['RUNNING_IN_DOCKER']:
    from .extensions import PrefixMiddleware
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix= app.config['APPLICATION_ROOT'])

d2l_url=app.config['BASE_URL'] + 'lite/home'

@app.context_processor
def inject_global_variables() -> dict:
    globals = {'d2l_url'}
    return {'globals': dict(((k, eval(k)) for k in globals))}

from .d2l.client import Client
from .db.client import DBClient

mysql = MySQL(app)
app.d2l_client = Client(mysql, app.config)
app.db_client = DBClient(mysql, app.config)
app.mysql = mysql

login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

migrate = Migrate(app, alchemy_db)

from .site.routes import site
from .api.routes import api

# register the blueprints for this site
app.register_blueprint(api)
app.register_blueprint(site)

# add jinja additions
from .site.flask_jsglue import JSGlue
jsglue = JSGlue(app)

from flask_moment import Moment
moment = Moment(app)

from .db.models import User

login_manager.session_protection = 'strong'
login_manager.login_view = "site.system.login"
login_manager.login_message_category = "danger"

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()

@login_manager.request_loader
def load_user_from_header(request):
    auth = request.authorization
    if not auth:
        return None

    user = User.query.filter_by(eid=auth.username).first()
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
        return "Unauthorized", 401
    else:
        return redirect(url_for('site.system.login'))  # Redirect to the default login page

#### error handlers ###################################################
@app.errorhandler(401)
def unauthorized_page(error):
    return render_template("errors/401.html"), 401

@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def server_error_page(error):
    return render_template("errors/500.html"), 500
