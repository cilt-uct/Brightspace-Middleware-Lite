import traceback

from flask import current_app, Blueprint, request
from flask_login import login_required

from ..utils import Utils

settings = Blueprint('settings', __name__, url_prefix='/settings')

# Get details of a notification template
@settings.route('/notifications/<int:id>', methods=['GET'])
@login_required
def get_notification_template(id: int):
    if id <= 0:
        return Utils.return_error_state('Notification ID is invalid.', 400)

    data = current_app.db_client.system.get_notifications_data(id)

    if data:
        return Utils.return_success_state(data)

    return Utils.return_error_state(f'Could not retrieve notification for ID {id}', 404)


# Update a notification template
@settings.route('/notifications/<int:id>', methods=['PUT'])
@login_required
def update_notification_template(id: int):
    if id <= 0:
        return Utils.return_error_state('Notification ID is invalid.', 400)

    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    result = current_app.db_client.system.update_notifications(
        id=data.get('id', 0),
        subject=data.get('subject', ''),
        from_email=data.get('from', ''),
        from_name=data.get('from_name', ''),
        html=data.get('html', ''),
        created_by=data.get('created_by', '0')
    )

    if result >= 0:
        return Utils.return_success_state(result)

    return Utils.return_error_state(f'Could not save notification for ID {id}', 500)
