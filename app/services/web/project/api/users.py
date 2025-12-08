
from flask import Blueprint, current_app
from flask_login import login_required

users = Blueprint('users', __name__, url_prefix='/user')

@users.route('/whoami', methods=['GET'])
@login_required
def users_whoami_handler():
    return current_app.d2l_client.user.get_me()
