import json

from flask import Blueprint, current_app, request
from flask_login import login_required

from ..utils import Utils

contents = Blueprint('contents', __name__, url_prefix='/content')

# Get root content for a course
@contents.route('<org_id>', methods=['GET'])
@contents.route('/root/<org_id>', methods=['GET'])
@login_required
def get_course_content_all(org_id: int):
    try:
        org_id_int = int(org_id)
    except (TypeError, ValueError):
        return Utils.return_error_state('org_id must be valid integers.')

    if org_id_int <= 0:
        return Utils.return_error_state(f'{org_id=} must be positive integers.')

    return current_app.d2l_client.content.retrieve_root(org_id)


# Get specific module content for a course
@contents.route('/<org_id>/module/<module_id>', methods=['GET'])
@login_required
def get_course_module(org_id: int, module_id: int):
    try:
        org_id_int = int(org_id)
        module_id_int = int(module_id)
    except (TypeError, ValueError):
        return Utils.return_error_state('org_id and module_id must be valid integers.')

    if org_id_int <= 0 or module_id_int <= 0:
        return Utils.return_error_state(f'{org_id=} and {module_id=} must be positive integers.')

    return current_app.d2l_client.content.get_module(org_id, module_id)


# Get structure of a specific module in a course
@contents.route('/<org_id>/module/<module_id>/structure', methods=['GET'])
@login_required
def get_course_module_structure(org_id: int, module_id: int):
    try:
        org_id_int = int(org_id)
        module_id_int = int(module_id)
    except (TypeError, ValueError):
        return Utils.return_error_state('org_id and module_id must be valid integers.')

    if org_id_int <= 0 or module_id_int <= 0:
        return Utils.return_error_state(f'{org_id=} and {module_id=} must be positive integers.')

    return current_app.d2l_client.content.get_module_structure(org_id, module_id)


# Add a file (HTML) to a specific module in a course as content item
@contents.route('/<org_id>/module/<module_id>', methods=['POST'])
@login_required
def add_file_to_module(org_id: int, module_id: int):
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    try:
        org_id_int = int(org_id)
        module_id_int = int(module_id)
    except (TypeError, ValueError):
        return Utils.return_error_state('org_id and module_id must be valid integers.')

    if org_id_int <= 0 or module_id_int <= 0:
        return Utils.return_error_state(f'{org_id=} and {module_id=} must be positive integers.')

    if 'file' not in request.files:
        return Utils.return_error_state('No file part in the request')

    details = data.get('detail')
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except json.JSONDecodeError:
            return Utils.return_error_state('Detail is not valid JSON')

    try:
        return current_app.d2l_client.content.add_file_to_module(org_unit_id=org_id,
                                                                module_id=module_id,
                                                                details=details,
                                                                file=request.files['file'])

    except Exception as e:
        return Utils.return_error_state(f'Could not add file to module {org_id=} {module_id=}: {e}', 500)


# Update the description (HTML) of a specific module in a course
@contents.route('/<org_id>/module/<module_id>/update', methods=['PUT'])
@login_required
def update_module_description(org_id: str, module_id: str):
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    description = data.get('description')
    if not description:
        return Utils.return_error_state('Missing required field: description.')

    try:
        org_id_int = int(org_id)
        module_id_int = int(module_id)
    except (TypeError, ValueError):
        return Utils.return_error_state('org_id and module_id must be valid integers.')

    if org_id_int <= 0 or module_id_int <= 0:
        return Utils.return_error_state(f'{org_id=} and {module_id=} must be positive integers.')

    try:
        root = current_app.d2l_client.content.retrieve_root(org_id)
    except Exception as e:
        return Utils.return_error_state(f'Error retrieving modules ({e}).', 502)

    if root.get('status') != 'success' or not isinstance(root.get('data'), list):
        return Utils.return_error_state('Failed to retrieve modules or malformed response.', 502)

    parent_node = next(
        (module for module in root['data'] if str(module.get('Id')) == module_id), None
    )

    if not parent_node:
        return Utils.return_error_state(f'Module {module_id} not found.', 404)

    update_result = current_app.d2l_client.content.update_module(org_id, module_id,
                                                    title=parent_node.get('Title'),
                                                    short=parent_node.get('ShortTitle'),
                                                    desc={'Content': description, 'Type': 'HTML'},
                                                    locked=parent_node.get('IsLocked', False),
                                                    type=parent_node.get('Type'),
                                                    hidden=False,  # Always make visible
                                                    start_date=parent_node.get('ModuleStartDate'),
                                                    end_date=parent_node.get('ModuleEndDate'),
                                                    due_date=parent_node.get('ModuleDueDate'))

    if update_result.get('status') != 'success':
        return Utils.return_error_state('Failed to update module description.', 502)

    return Utils.return_success_state({'org_id': org_id, 'parent_id': module_id, 'updated': True})


# Get course topics content - either all topics (root) or a specific topic
@contents.route('/<org_id>/topics', methods=['GET'])
@contents.route('/<org_id>/topics/<topic_id>', methods=['GET'])
@login_required
def get_course_topics_content(org_id: int = 0, topic_id = None):
    if int(org_id) <= 0:
        return Utils.return_error_state(f'{org_id=} must be a positive integer.')

    if topic_id:
        return current_app.d2l_client.content.course_topics_content(org_id, topic_id)

    return current_app.d2l_client.content.retrieve_root(org_id)


# Get or update topic (HTML)
@contents.route('/<org_id>/topics/<topic_id>/file', methods=['GET', 'PUT'])
@login_required
def course_topics_file(org_id: int, topic_id: int):
    if int(org_id) <= 0:
        return Utils.return_error_state(f'{org_id=} must be a positive integer.')

    if int(topic_id) <= 0:
        return Utils.return_error_state(f'{topic_id=} must be a positive integer.')

    current_topic_content = current_app.d2l_client.content.get_course_topic_content_file(org_id, topic_id)

    # get the file here
    if request.method == 'GET':
        return current_topic_content

    # put file if checks are true
    if request.method == 'PUT':
        data = Utils.parse_request_data(request)
        if data is None:
            return Utils.return_error_state('Invalid content type', 406)

        if current_topic_content['status'] == 'success':
            filename = data.get('name') if 'name' in data else None
            return current_app.d2l_client.content.update_course_topic_file_html(
                org_unit_id=org_id, topic_id=topic_id, topic_data_html=data.get('html'), filename=filename)

    return Utils.return_error_state('Method Not Allowed', 405)


# Reorder a module based on it's title and position
# [HELPER]
def reorder_module(org_id: int, title: str, position: str):
    """
    Reorder a module based on its title and position.
    :param org_id: Organization ID
    :param title: Title of the module to reorder
    :param position: New position for the module
    :return: Result of the reordering operation
    """
    if int(org_id) <= 0:
        return Utils.return_error_state(f'{org_id=} must be a positive integer.')

    modules = current_app.d2l_client.content.retrieve_root(org_unit_id=org_id)['data']

    module_id = next((module.get('Id') for module in modules if module.get('Title') == title), None)

    if not module_id:
        return Utils.return_error_state(f'Module with title "{title}" not found.', 404)

    try:
        return current_app.d2l_client.content.order_module(
            org_unit_id=org_id,
            object_id=module_id,
            first=True if position == 'first' else False
        )
    except Exception:
        return Utils.return_error_state(f'Failed to reorder module "{title}".', 500)

# Order modules in a course by title and position; uses reorder_module
# [HELPER]
@contents.route('/order', methods=['POST'])
@login_required
def order_module():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    try:
        org_id = int(data.get('org_id', 0))
    except (ValueError, TypeError):
        return Utils.return_error_state('Invalid organization ID.')

    title = data.get('title', '')
    if not title:
        return Utils.return_error_state('Title is required.')

    return reorder_module(org_id, title=title, position=data.get('position', 'first'))


# Put a module called "Course Info" first if found; uses reorder_module [HELPER]
@contents.route('/order/course_info', methods=['POST'])
@login_required
def order_course_info():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    try:
        org_id = int(data.get('org_id', 0))
    except (ValueError, TypeError):
        return Utils.return_error_state('Invalid organization ID.')

    return reorder_module(org_id, title='Course Info', position='first')


# Put a module called "Course Outline" first if found; uses reorder_module [HELPER]
@contents.route('/order/course_outline', methods=['POST'])
@login_required
def order_course_outline():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    try:
        org_id = int(data.get('org_id', 0))
    except (ValueError, TypeError):
        return Utils.return_error_state('Invalid organization ID.')

    return reorder_module(org_id, title='Course Outline', position='first')
