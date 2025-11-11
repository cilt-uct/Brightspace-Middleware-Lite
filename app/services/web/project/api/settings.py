import traceback

from flask import current_app, Blueprint, request
from flask_login import login_required

from ..utils import Utils

settings = Blueprint('settings', __name__, url_prefix='/settings')
