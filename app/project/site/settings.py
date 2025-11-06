from flask import current_app, redirect, request, session, Blueprint, jsonify, render_template, send_from_directory, url_for
from flask_login import login_required, current_user

from ..utils import Utils

# url_prefix='/lite/settings'
settings = Blueprint('settings', __name__, url_prefix='/settings')

@settings.route('/')
@login_required
def start():
    return render_template('settings.html', user_id=current_user.eid)

# DataTable - retrieve the system users for the DataTable JS class
@settings.route('/users', methods=['POST'])
@login_required
def get_site_users_ajax():
    data = Utils.parse_request_data(request)
    if data is None:
        return 'Invalid content type', 400

    order_details = Utils.get_order_column_name(data.get("order"), data.get("columns"))
    return current_app.db_client.system.get_users(  draw = data.get('draw', 1),
                                                    start = data.get('start', 0),
                                                    length = data.get('length', 20),
                                                    order_column = order_details[0],
                                                    order_dir = order_details[1],
                                                    search_st = data["search"]["value"],
                                                    search_regex = data["search"]["regex"])
