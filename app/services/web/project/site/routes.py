import os
import json
import re
from distutils import extension
from datetime import datetime, timedelta

from flask import current_app, redirect, request, session, Blueprint, jsonify, render_template, send_from_directory, url_for
from flask_login import login_required, current_user

from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from ..utils import Utils

from .settings import settings
from .system import system

# url_prefix='/lite'
site = Blueprint('site', __name__)
site.register_blueprint(settings)
site.register_blueprint(system)

## Core ###############################################################
@site.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user.name, is_admin=current_user.is_admin)

@site.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')

@site.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(current_app.config["STATIC_FOLDER"], filename)

@site.route('/ping', methods=["GET"])
def ping_pong():
    return jsonify(
        {"status": "success", "data": "pong!"}
    ), 200


## OAuth ##############################################################
@site.route('/oauth', methods=["GET"])
def oauth_login():
    auth_info = current_app.d2l_client.authorization_url()
    session['oauth_state'] = auth_info['state']
    print(f'starting: oauth login with state: {session["oauth_state"]}')

    return redirect(auth_info['authorization_url'])

@site.route('/callback', methods=["GET"])
def oauth_callback():
    state = request.args.get('state','none')
    expected_state = session.get('oauth_state', '')
    print("callback")
    # print(state)
    # print(expected_state)

    if current_app.config['RUNNING_IN_DOCKER']:
        if expected_state:
            if state != expected_state:
                print("Error, state doesn't match, redirecting without getting token.")
                return redirect(url_for('site.index')) # should be error display
        else:
            print("Error, no session")
            return redirect(url_for('site.index')) # should be error display

    if current_app.d2l_client.exchange_code(request.url):
        # found token all good
        # Get user of token
        # session['user'] = current_app.d2l_client.user.get_me()
        current_user = current_app.d2l_client.user.get_me()
        if 'status' in current_user and current_user['status'] == 'success':
            print(f"{current_user['data']['UniqueName']}")
    else:
        # token not found :(
        print("token not found :(")
        return redirect(url_for('site.index')) # should be error display

    return redirect(url_for('site.index'))

@site.route('/token_refresh', methods=['GET'])
def token_refresh_handler():
    force = int(request.args.get('force','0')) == 1
    result = current_app.d2l_client.do_refresh(force)
    return Utils.return_success_state(result.to_dict())

@site.route('/token_valid', methods=['GET'])
def token_valid_handler():
    result = current_app.d2l_client.get_token()
    return jsonify(result.is_token_valid)

@site.route('/token_expires_soon', methods=['GET'])
def token_expiry_check_handler():
    result = current_app.d2l_client.get_token()
    return Utils.return_success_state(result.to_dict())
