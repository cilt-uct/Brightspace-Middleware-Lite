import json
import traceback
import asyncio

from flask import current_app, Blueprint, request
from flask_login import login_required

from ..utils import Utils
from ..decorators import process_call_request

from .contents import contents
from .courses import courses
from .roles import roles
from .settings import settings
from .users import users

# url_prefix='/lite/api'
api = Blueprint('api', __name__, url_prefix='/api')
api.register_blueprint(contents)
api.register_blueprint(courses)
api.register_blueprint(roles)
api.register_blueprint(settings)
api.register_blueprint(users)

## Core ###############################################################
@api.route('/version', defaults={'type': ''}, methods=['GET'])
@api.route('/version/', defaults={'type': ''}, methods=['GET'])
@api.route('/version/<type>', methods=['GET'])
@login_required
def get_all_version(type):
    if (type == 'le'):
        return current_app.d2l_client.get_le_version()
    elif (type == 'lp'):
        return current_app.d2l_client.get_lp_version()
    else:
        response = current_app.d2l_client.get_all_version()

    if type:
        matches = [p for p in response['data'] if p['ProductCode'] == type]
        if (matches):
            response['data'] = matches[0]

    return response


# Define the endpoint that forwards the request to Brightspace
@api.route('/call', methods=['POST'])
@api.route('/call/', methods=['POST'])
@process_call_request
@login_required
def forward_request():
    # remote_addr_str = request.headers.get('X-Forwarded-For', request.remote_addr)
    # remote_addr_list = [x.strip() for x in remote_addr_str.split(',')]

    # # Check if the request is coming from the allowed host
    # if not any(Utils.is_allowed(ip) for ip in remote_addr_list):
    #     return Utils.return_error_state('Forbidden', 403) # Forbidden

    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    try:
        if data.get('method') == 'PUT':
            return current_app.d2l_client._put(url=data.get('url'),
                                                    data=data.get('payload'))
        elif data.get('method') == 'POST':
            return current_app.d2l_client._post(url=data.get('url'),
                                                    data=data.get('payload'))
        else:
            return current_app.d2l_client._request(method=data.get('method'),
                                                url=data.get('url'),
                                                json=data.get('payload'))

    except Exception as e:
        return Utils.return_error_state(str(e), 500)
