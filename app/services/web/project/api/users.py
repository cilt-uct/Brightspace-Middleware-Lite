
import pandas as pd
import traceback
import re

from flask import current_app, Blueprint, request
from flask_login import login_required

from project.app import alchemy_db

from urllib.parse import urlparse, parse_qs

from ..utils import Utils
from ..constants import RE_VULA_REF_SITE

users = Blueprint('users', __name__, url_prefix='/user')

@users.route('/whoami', methods=['GET'])
@login_required
def users_whoami_handler():
    return current_app.d2l_client.user.get_me()
