from flask import Blueprint, current_app
from flask_login import login_required

roles = Blueprint('roles', __name__, url_prefix='/roles')

# Return all roles in Brightspace
@roles.route('/', methods=['GET'])
@login_required
def get_roles():
    return current_app.d2l_client.roles.get_roles()
