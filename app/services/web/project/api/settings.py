from flask import Blueprint
from flask_login import login_required

from ..utils import Utils

settings = Blueprint('settings', __name__, url_prefix='/settings')

# Return placeholder for settings
@settings.route('/', methods=['GET'])
@login_required
def get_roles():
    return Utils.return_success_state({'message': 'Settings endpoint placeholder'})
