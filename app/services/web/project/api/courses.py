import os
import re
import time
import uuid
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from flask import Blueprint, current_app, request
from flask_login import login_required
from werkzeug.utils import secure_filename

from ..constants import RE_COURSE_OR_PROGRAM_SANS_SUFFIX, RE_PROGRAM
from ..utils import Utils

courses = Blueprint('courses', __name__, url_prefix='/course')

# Return course details by ID or Code
@courses.route('/', defaults={'id': 0}, methods=['GET'])
@courses.route('/<id>', methods=['GET'])
@login_required
def get_course_handler(id: int):
    params = parse_qs(urlparse(request.url).query)

    course_codes = params.get('code')
    if course_codes:
        course_code = course_codes[0]
        if not course_code.strip():
            return Utils.return_error_state('Course code cannot be empty.')

        return current_app.d2l_client.course.get_course_by_code(course_code, first=True)

    try:
        id = int(id)
    except (TypeError, ValueError):
        return Utils.return_error_state(f'Course ID required {id}')

    if id <= 0:
        return Utils.return_error_state(f'Course ID ({id}) must be positive integers.')

    return current_app.d2l_client.course.get_course_by_id(id)


# Construct the Course Offering Code to use the course/program codes
# If it's larger that the required 50 Chars then use the default
# [HELPER]
def get_course_offering_code(courses: list, term: int, default: str = ''):
    if courses:
        result = f'_{term}+'.join(courses) + f'_{term}'
        if len(result) > 50:
            return result[:50]
        return result
    return default[:50]


# Regular expression to match course or program code without suffix
# [HELPER]
def get_template_code(courses: list, default: str = ''):
    if courses:
        # use the first course / program code in the list
        find_tmpl = re.search(RE_COURSE_OR_PROGRAM_SANS_SUFFIX, courses[0])
        if find_tmpl:
            # use the first course code or program code
            # AMA-902 - Omit course period suffix from course template name
            return find_tmpl.group(1) if find_tmpl.group(1) else find_tmpl.group(2)
    return default[:50]


# A new course was created in Brightspace, now add it to the database
# and do enrollment and other tasks
# [HELPER]
def do_new_course_admin(site_aid: int, site_code: str, site_title: str, site_term: str,
                        providers: list, site_type: str, requestor: str, role: int,
                        site_active: bool=True,
                        template_id: int = 0, dept_id: int = 0, semester_id: int = 0,
                        copy_orientation: bool=False,
                        create_lr: bool=False):

    if site_term == 'other':
        term = 0
    else:
        term = int(site_term)

    # site was created - add to DB
    current_app.db_client.courses.add_course(AID=site_aid,
                                                code=site_code,
                                                title=site_title,
                                                term=term,
                                                providers=providers,
                                                type=site_type,
                                                active=site_active,
                                                template_id=template_id, dept_id=dept_id, semester_id=semester_id,
                                                created_by=requestor)

    # Do enrollment
    if requestor not in ['migration', 'refresh']:
        current_app.d2l_client.course.enroll_any_user(org_id=site_aid,
                                                        eid=requestor,
                                                        role=role)

    # TODO: copy_orientation site content if required
    # if copy_orientation:


# Create course [Migration]
@courses.route('/', methods=['POST'])
@courses.route('/new', methods=['POST'])
@login_required
def create_new_course_handler():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    site_type = data.get('type')

    site_faculty = data.get('faculty', 'other')
    site_faculty_list = [site_faculty]

    site_term = data.get('year', datetime.now().year)
    site_creator = data.get('user','created_by')

    site_course_code = data.get('course_code', '')
    create_even_if_it_exists = data.get('create') in (1,'1','on','yes','true') or False
    check_name = data.get('check_name') in (1,'1','on','yes','true') or False

    copy_orientation = data.get('copy_orientation') in (1,'1','on','yes','true') or False

    set_course_active = data.get('active') in (1,'1','on','yes','true') or False

    # Add LR to the course as well - see do_new_course_admin [HELPER]
    also_add_lecture_recording = data.get('lr') in (1,'1','on','yes','true') or False

    if site_type == 'community':
        site_role = data.get('role', 'Owner')

        # Normalize role to 'Owner' if invalid or disallowed
        if Utils.get_internal_role(site_role) == 0 or site_role == 'Lecturer' or site_role == 'LecturerTutor':
            site_role = 'Owner'

        site_name = data.get('name', f'Community: {site_faculty} ({site_term})')

        # community sites use the 'other' templates for the faculty
        result = current_app.d2l_client.course.create_community_site(name=site_name,
                                                                     faculty=site_faculty,
                                                                     term=site_term,
                                                                     course_code=site_course_code,
                                                                     create_even_if_it_exists=create_even_if_it_exists,
                                                                     check_name=check_name,
                                                                     active=set_course_active)

        if not result or result.get('status') != 'success':
            return result

        # Course site has been created successfully now add it to the database
        # and do some additional tasks like enrollment, copying orientation content, etc.
        do_new_course_admin(site_aid=result['data']['Identifier'],
                            site_code=result['data']['Code'],
                            site_title=result['data']['Name'],
                            site_term=site_term,
                            providers=[],
                            site_type='project',
                            site_active=set_course_active,
                            template_id=result['data']['CourseTemplate']['Identifier'],
                            dept_id=result['data']['Department']['Identifier'],
                            semester_id=result['data']['Semester']['Identifier'],
                            requestor=site_creator,
                            role=Utils.get_internal_role(site_role),
                            copy_orientation=copy_orientation,
                            create_lr=also_add_lecture_recording)

        return result

    elif site_type == 'course':
        site_role = data.get('role', 'Lecturer')
        if Utils.get_internal_role(site_role) == 0:
            site_role = 'Lecturer'
        if site_role == 'Owner': # wrong role - course sites get Lecturers
            site_role = 'Lecturer'

        if site_course_code == 'FINAID':
            site_codes = []
            site_name = data.get('name', f'Financial Aid, {datetime.now().year}')
        else:
            site_codes = [site.split('_')[0].strip(' \'"') for site in data.get('codes', '').split(',')]
            site_name = data.get('name', ', '.join(site_codes) +','+ site_term )

        site_codes = [i for i in site_codes if i] # remove empty and None

        dept = ['other']
        guid = uuid.uuid4()
        template_code = f'other_{site_term}'
        course_code = f'other_{guid}_{site_term}'
        are_there_program_codes = any(re.compile(RE_PROGRAM).fullmatch(item) for item in site_codes)

        if site_codes:
            site_codes.sort() # course codes are alphabetical

            # determine the department of this site
            with current_app.mysql.connection.cursor() as cursor:
                codes = '(' + ','.join(["'" + x + "'" for x in site_codes]) + ')'

                if codes:
                    cursor.execute(f"""SELECT ifnull(
                                                    GROUP_CONCAT(DISTINCT `src`.dept
                                                                    ORDER BY `src`.dept asc SEPARATOR ', ')
                                                    ,'other'
                                                ) as `dept`,
                                                ifnull(
                                                    GROUP_CONCAT(DISTINCT `src`.faculty
                                                                    ORDER BY `src`.faculty asc SEPARATOR ', ')
                                                    ,'other'
                                                ) as `faculty`
                                        FROM
                                        (SELECT `pc`.program_code as `provider`,
                                                `pc`.acad_career as `career`,
                                                `pc`.`description` as title,
                                                null as  `dept`,
                                                `faculty`.`code` as faculty
                                            FROM ps_program_codes `pc`
                                                left join d2l_faculty `faculty` on `faculty`.`code` = `pc`.acad_group
                                            where `pc`.`status` = 'A' and `pc`.program_code in {codes}
                                        UNION
                                            SELECT `course`.course_code as `provider`,
                                                    `course`.acad_career as `career`,
                                                    `course`.title,
                                                    `dept`.`code` as `dept`,
                                                    `faculty`.`code` as `faculty`
                                            FROM ps_courses `course`
                                                left join d2l_dept `dept` on `dept`.`code` = `course`.`dept`
                                                left join d2l_faculty `faculty` on `faculty`.`AID` = `dept`.`parent`
                                            where term >= %(term)s and `course`.course_code in {codes}) `src`""",
                                        {'term': datetime.now().year})
                    line = cursor.fetchone()
                    if line:
                        dept = line['dept'].split(',')
                        site_faculty_list = line['faculty'].split(',')

        # single department and single faculty
        if len(dept) == 1 and len(site_faculty_list) == 1:
            course_code = get_course_offering_code(site_codes, site_term, default=f'{dept[0]}_{guid}_{site_term}')
            template_code = get_template_code(site_codes, default=f'{dept[0]}_{site_term}')

            no_program_codes = not are_there_program_codes
            if 'other' in dept and 'other' not in site_faculty_list:
                # other in dept but we have a valid faculty - so switch to that faculties other dept and set template
                course_code = f'{site_faculty_list[0]}_{guid}_{site_term}' if no_program_codes else course_code
                template_code = f'{site_faculty_list[0]}_other_template' if no_program_codes else template_code
                dept = [f'{site_faculty_list[0]}-other']

        # single department and multi faculty
        if len(dept) == 1 and len(site_faculty_list) > 1:
            course_code = get_course_offering_code(site_codes, site_term, default=f'{dept[0]}_{guid}_{site_term}')
            template_code = f'other_{site_term}'

        # multi department and single faculty
        if len(dept) > 1 and len(site_faculty_list) == 1:
            course_code = get_course_offering_code(site_codes, site_term, default=f'{site_faculty}_{guid}_{site_term}')
            template_code = f'{site_faculty_list[0]}_other_template'
            dept = [f'{site_faculty_list[0]}-other']

        # multi department and multi faculty
        if len(dept) > 1 and len(site_faculty_list) > 1:
                course_code = get_course_offering_code(site_codes, site_term, default=f'UCT_{guid}_{site_term}')
                template_code = f'other_{site_term}'
                dept = ['other']

        # default if the "site_course_code" was provided then use that
        if site_course_code:
            course_code = f'{site_course_code}_{site_term}'
            template_code = get_template_code(site_codes, default=site_course_code)

            if site_course_code == 'FINAID':
                template_code = 'FINAID'

        # print(f"""
        #         course_code={course_code}
        #         name={site_name}
        #         template={template_code}
        #         term={site_term}
        #         dept={dept[0]}
        #         create_even_if_it_exists={create_even_if_it_exists}
        #         check_name={check_name}
        #         {site_creator} : {site_role}""")

        result = current_app.d2l_client.course.create_course_site(course_code=course_code,
                                                                  name=site_name,
                                                                  template=template_code,
                                                                  term=site_term,
                                                                  dept=dept[0],
                                                                  create_even_if_it_exists=create_even_if_it_exists,
                                                                  check_name=check_name,
                                                                  active=set_course_active)
        if not result or result.get('status') != 'success':
            return result

        # Course site has been created successfully now add it to the database
        # and do some additional tasks like enrollment, copying orientation content, etc.
        do_new_course_admin(site_aid=result['data']['Identifier'],
                            site_code=result['data']['Code'],
                            site_title=result['data']['Name'],
                            site_term=site_term,
                            providers=site_codes,
                            site_type='course',
                            site_active=set_course_active,
                            template_id=result['data']['CourseTemplate']['Identifier'],
                            dept_id=result['data']['Department']['Identifier'],
                            semester_id=result['data']['Semester']['Identifier'],
                            requestor=site_creator,
                            role=Utils.get_internal_role(site_role),
                            copy_orientation=copy_orientation,
                            create_lr=also_add_lecture_recording)

        return result

    return Utils.return_error_state('Course type is required')


# Update course details in Brightspace
@courses.route('/<id>', methods=['PUT'])
@login_required
def update_course(id: int = 0):
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    try:
        id = int(id)
    except (TypeError, ValueError):
        return Utils.return_error_state(f'Course ID required {id}')

    if id <= 0:
        return Utils.return_error_state(f'Course ID required {id}')

    _found_course = current_app.d2l_client.course.get_course(val=id, use_id=True)
    if not _found_course or _found_course.get('status') != 'success':
        return _found_course

    set_course_active = data.get('active') in (1,'1','on','yes','true')
    if 'active' not in data:
        set_course_active = _found_course['data']['IsActive']

    result = current_app.d2l_client.course.update_course_site(org_id=id,
                                                            name=data.get('title', data.get('name',
                                                                                            _found_course['data']['Name'])),
                                                            code=data.get('code', _found_course['data']['Code']),
                                                            active=set_course_active,
                                                            description=data.get('desc',
                                                                                data.get('description',
                                                                                        _found_course['data']['Description']['Text']))) # noqa: E501

    if not result or result.get('status') != 'success':
        return result

    updated_site = current_app.d2l_client.course.get_course(val=id, use_id=True)
    if not updated_site or updated_site.get('status') != 'success':
        return updated_site

    # Update in Database
    current_app.db_client.courses.update_course(AID=id,
                                                code=updated_site['data']['Code'],
                                                title=updated_site['data']['Name'],
                                                term=updated_site['data']['Semester']['Code'],
                                                active=updated_site['data']['IsActive'],
                                                template_id=updated_site['data']['CourseTemplate']['Identifier'],
                                                dept_id=updated_site['data']['Department']['Identifier'],
                                                semester_id=updated_site['data']['Semester']['Identifier'])

    return updated_site


# Getting a list of course owners (lecturers, LecturerTutor, owners, support staff)
@courses.route('/<id>/owners', methods=['GET'])
@login_required
def get_course_owners_handler(id: int):
    try:
        id = int(id)
    except (TypeError, ValueError):
        return Utils.return_error_state(f'Course ID required {id}')

    if id <= 0:
        return Utils.return_error_state(f'Course ID ({id}) must be positive integers.')

    return Utils.return_success_state(current_app.d2l_client.course.get_list_of_owners(id))


# Getting a list of all courses
@courses.route('/list', methods=['GET'])
@login_required
def get_courses_list_handler():
    params = parse_qs(urlparse(request.url).query)
    bookmark = None
    org_code = None
    exact_code = None

    if 'bookmark' in params:
        bookmark = params['bookmark'][0]

    if 'org_code' in params:
        org_code = params['org_code'][0]

    if 'exact_code' in params:
        exact_code = params['exact_code'][0]

    # Calls org structure and filters by "Course Offering" type
    return current_app.d2l_client.orgunit.get_all_courses_by_page(bookmark=bookmark,
                                                                    org_code=org_code,
                                                                    exact_code=exact_code)


# Copy the source/src_org_id course content to the target/org_id course
@courses.route('/copy', methods=['POST'])
@courses.route('/copy_orientation', methods=['POST'])
@login_required
def handle_copy_content():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    return current_app.d2l_client.course.copy_course_content(target_org_unit=data.get('target', data.get('org_id')),
                                                             src_org_unit=data.get('source', data.get('src_org_id')))


# Duplicate an existing site
# TODO: create route which is /api/course/<id>/duplicate ['POST']
@courses.route('/duplicate', methods=['POST'])
@login_required
def duplicate_course_site():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    src_course_id = data.get('source')
    if int(src_course_id) <= 0:
        return Utils.return_error_state(f'Invalid source id ({src_course_id})')

    src_course = current_app.d2l_client.course.get_course_by_id(src_course_id)
    if src_course['status'] == 'success':
        site_term = data.get('semester', data.get('term', 0))
        src_semester_id = Utils.get_id_from_valid_or_default(current_app.d2l_client.orgunit.get_semester_by_term,
                                                       site_term,
                                                       src_course['data']['Semester']['Code'])
        semester = current_app.d2l_client.orgunit.get_org_details(src_semester_id)

        new_term_course_code = Utils.replace_year(src_course['data']['Code'], site_term)
        course_code = Utils.add_duplicate_postfix(new_term_course_code)

        if len(course_code) > 50:
            course_code = f'DUPL_{uuid.uuid4()}_{site_term}'

        # Create course based on source course
        result = current_app.d2l_client.course.create_site(course_code=course_code,
                                                            name=data.get('title', f'Copy: {src_course['data']['Name']}'), # noqa: E501
                                                            template_id=src_course['data']['CourseTemplate']['Identifier'], # noqa: E501
                                                            semester_id=src_semester_id,
                                                            create_even_if_it_exists=True,
                                                            check_name=False)
        if result['status'] != 'success':
            return Utils.return_error_state(result)

        site_creator = data.get('requestor', data.get('user', None))
        providers = current_app.db_client.courses.get_providers(src_course_id)

        course_type = 'course'
        course_details = current_app.db_client.courses.get_course(src_course_id)
        if course_type is None:
            # fetch type from DB
            course_type = course_details['type']

        role_id = Utils.get_internal_role('Lecturer')
        _found_user = current_app.d2l_client.course.get_enrollment_by_id_for_user(org_id=src_course['data']['Identifier'], # noqa: E501
                                                                                    eid=site_creator)
        if _found_user['status'] == 'success':
            role_id = _found_user['data']['RoleId']

        do_new_course_admin(site_aid=result['data']['Identifier'],
                            site_code=result['data']['Code'],
                            site_title=result['data']['Name'],
                            site_term=site_term,
                            providers=[x['provider'] for x in providers],
                            site_type=course_type,
                            site_active=result['data']['IsActive'],
                            template_id=result['data']['CourseTemplate']['Identifier'],
                            dept_id=result['data']['Department']['Identifier'],
                            semester_id=result['data']['Semester']['Identifier'],
                            requestor=site_creator,
                            role=role_id,
                            copy_orientation=False,
                            create_lr=False)

        # TODO : add task to duplicate content from source to target site

        if data.get('link', False):
            linked_count = 0

            for code in providers:
                linked = current_app.db_client.courses.add_course_provider(provider=code['provider'],
                                                                    term=semester['data']['Code'],
                                                                    aid=result['data']['Identifier'],
                                                                    type='course',
                                                                    src='user')
                if linked['results']:
                    linked_count += 1

            result['data']['linked'] = linked_count
        return result

    return Utils.return_error_state('Invalid request')


# Import a file into a course by creating a import job request for the file
@courses.route('/import_package', methods=['POST'])
@login_required
def import_package_handler():
    target_course_org_id = request.form.get('org_id')

    if 'file' not in request.files:
        return Utils.return_error_state('No file part')

    file = request.files.get('file')
    if not file or file.filename == '':
        return Utils.return_error_state('No selected file')

    if not Utils.allowed_file_zip(file):
        return Utils.return_error_state('File type not allowed')

    # Generate a unique filename using timestamp
    original_filename = secure_filename(file.filename)
    timestamp = int(time.time())
    unique_filename = f'{timestamp}_{original_filename}'
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

    try:
        # Save the uploaded file
        file.save(file_path)

        # Call D2L import
        result = current_app.d2l_client.course.import_file(target_course_org_id, file_path)

        # If import was successful, clean up the file
        if result and result.get('status') == 'success':
            try:
                os.remove(file_path)
            except Exception as e:
                print(f'Failed to delete uploaded file {file_path}: {e}')

        return result
    except Exception:
        return Utils.return_error_state('Internal server error during import', 500)


## Courses - Link #####################################################

# Get the class list of the site
@courses.route('/classlist/', defaults={'id': 0}, methods=['GET'])
@courses.route('/classlist/<id>', methods=['GET'])
@login_required
def get_course_classlist_handler(id: int):
    try:
        id = int(id)
    except (TypeError, ValueError):
        return Utils.return_error_state('Course ID must be valid integers.')

    if id <= 0:
        return Utils.return_error_state(f'Course ID ({id}) must be positive integers.')

    params = parse_qs(urlparse(request.url).query)
    paged = False
    bookmark = None
    filter_role = 0

    if 'paged' in params:
        paged = (params['paged'][0] == 'True' or params['paged'][0] == 'true' or params['paged'][0] == '1')

    if 'bookmark' in params:
        bookmark = params['bookmark'][0]

    if 'administrator' in params:
        filter_role = Utils.get_internal_role('Administrator')

    if 'designer' in params:
        filter_role = Utils.get_internal_role('Designer')

    if 'staff' in params:
        filter_role = Utils.get_internal_role('Staff')

    if 'lecturer' in params:
        filter_role = Utils.get_internal_role('Lecturer')

    if 'owner' in params:
        filter_role = Utils.get_internal_role('Owner')

    if 'support' in params:
        filter_role = Utils.get_internal_role('Support Staff')

    if 'tutor' in params:
        filter_role = Utils.get_internal_role('Tutor')

    if 'guest' in params:
        filter_role = Utils.get_internal_role('Guest')

    if 'student' in params:
        filter_role = Utils.get_internal_role('Student')

    if 'member' in params:
        filter_role = Utils.get_internal_role('Member')

    if 'observer' in params:
        filter_role = Utils.get_internal_role('Observer')

    return current_app.d2l_client.course.get_course_classlist_by_id(int(id),
                                                                    bookmark=bookmark, paged=paged,
                                                                    filter_role=filter_role)


## Courses - Enrollments ##############################################
# Returns all enrollments for a user based on EID
@courses.route('/enroll/', defaults={'eid': ''}, methods=['GET'])
@courses.route('/enroll/<eid>', methods=['GET'])
@login_required
def get_course_enrollments_handler(eid: str):
    query_params = parse_qs(urlparse(request.url).query)
    eid = query_params.get('eid', [eid])[0]

    if not eid:
        return Utils.return_error_state('EID is required', 400)

    return current_app.d2l_client.course.get_course_enrollments_by_EID(eid)


# Enroll a user from user_id or eid into course (org_id) as role
# [HELPER]
def do_enroll_of_any_user(org_id: int = 0, user_id: int = 0, eid: str = None, role: int = None):
    # print(f'do_enroll_of_any_user: {org_id} {user_id} {eid} {role}')

    if int(org_id) == 0:
        return Utils.return_error_state('Org ID invalid')

    if int(user_id) == 0 and eid is None:
        return Utils.return_error_state('User ID/EID invalid')

    if role is None:
        return Utils.return_error_state('Role invalid')

    return current_app.d2l_client.course.enroll_any_user(org_id=org_id,
                                                         user_id=user_id,
                                                         eid=eid,
                                                         role=role)


# Enroll a user into course (org_id) as role; uses do_enroll_of_any_user [HELPER]
# TODO: add route which is /api/course/<org_id>/enroll/<role/role_id>/<eid/user_id> ['POST']
@courses.route('/enroll/user', methods=['POST'])
@login_required
def do_enroll_user():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    return do_enroll_of_any_user(org_id=int(data.get('org_id', 0)),
                                 user_id=int(data.get('user_id', 0)),
                                 eid=data.get('eid', None),
                                 role=Utils.get_internal_role(data.get('role', '')))


# Enroll a user into course (org_id) as lecturer; uses do_enroll_of_any_user [HELPER]
# TODO: add route which is /api/course/<org_id>/enroll/lecturer/<eid/user_id> ['POST']
@courses.route('/enroll/lecturer', methods=['POST'])
@login_required
def do_enroll_lecturer():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    return do_enroll_of_any_user(org_id=int(data.get('org_id', 0)),
                                 user_id=int(data.get('user_id', 0)),
                                 eid=data.get('eid', None),
                                 role=Utils.get_internal_role('Lecturer'))


# Enroll a user into course (org_id) as owner; uses do_enroll_of_any_user [HELPER]
# TODO: add route which is /api/course/<org_id>/enroll/owner/<eid/user_id> ['POST']
@courses.route('/enroll/owner', methods=['POST'])
@login_required
def do_enroll_owner():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    return do_enroll_of_any_user(org_id=int(data.get('org_id', 0)),
                                 user_id=int(data.get('user_id', 0)),
                                 eid=data.get('eid', None),
                                 role=Utils.get_internal_role('Owner'))


# Enroll a user into course (org_id) as student; uses do_enroll_of_any_user [HELPER]
# TODO: add route which is /api/course/<org_id>/enroll/student/<eid/user_id> ['POST']
@courses.route('/enroll/student', methods=['POST'])
@login_required
def do_enroll_student():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    return do_enroll_of_any_user(org_id=int(data.get('org_id', 0)),
                                 user_id=int(data.get('user_id', 0)),
                                 eid=data.get('eid', None),
                                 role=Utils.get_internal_role('Student'))


# Enroll a user as student into multiple courses (org_ids)
@courses.route('/enroll/student/bulk', methods=['POST'])
@login_required
def bulk_enroll_student():
    return current_app.d2l_client.course.enroll_student_to_multiple_sites(org_ids=str(request.form.get('org_ids', '')),
                                                                          eid=request.form.get('eid', None),
                                                                          role=Utils.get_internal_role('Student'))


# Enroll a user into course (org_id) as member; uses do_enroll_of_any_user [HELPER]
# TODO: add route which is /api/course/<org_id>/enroll/member/<eid/user_id> ['POST']
@courses.route('/enroll/member', methods=['POST'])
@login_required
def do_enroll_member():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    return do_enroll_of_any_user(org_id=int(data.get('org_id', 0)),
                                 user_id=int(data.get('user_id', 0)),
                                 eid=data.get('eid', None),
                                 role=Utils.get_internal_role('Member'))

# Check if a user item is valid for batch enrollment
def is_valid_user_item(item):
    """Validate a single user item in the batch."""
    if not isinstance(item, dict):
        return False
    if 'org_id' not in item or 'role' not in item:
        return False
    if not ('eid' in item or 'user_id' in item):
        return False
    return True

# Enroll a batch of users into various courses (org_id)
# [ { "org_id": <number>, "eid": <string>, "user_id": <number>, "role": <string/number> } ]
@courses.route('/enroll/batch', methods=['POST'])
@login_required
def do_enroll_batch():
    data = Utils.parse_request_data(request)
    if data is None:
        return Utils.return_error_state('Invalid content type', 406)

    batch = data.get('batch', [])

    if not isinstance(batch, list) or not batch:
        return Utils.return_error_state('Batch must be a non-empty list')

    if not all(is_valid_user_item(item) for item in batch):
        return Utils.return_error_state('Each item in batch must be a dict with "org_id","eid"/"user_id", and "role" keys') # noqa: E501

    return current_app.d2l_client.course.enroll_user_batch(batch=batch)


# Un-enrol / remove enrollment of a user from course (org_id) by EID
@courses.route('/<org_id>/enroll/<eid>', methods=['DELETE'])
@courses.route('/<org_id>/enrollment/<eid>', methods=['DELETE']) # [legacy]
@login_required
def remove_enrollment(org_id: int = 0, eid: str = ''):
    try:
        org_id = int(org_id)
    except (TypeError, ValueError):
        return Utils.return_error_state(f'Org ID ({org_id}) should be a valid number')

    # print(f"un-enroll : {org_id}: {eid}")
    if org_id > 0 and eid:
        user = current_app.d2l_client.user.get_user_by_EID(eid)
        if not user or user.get('status') != 'success':
            return user

        return current_app.d2l_client.course.remove_enrollment(org_id, user['data']['UserId'])

    return Utils.return_error_state(f'Org ID ({org_id}) or EID ({eid}) invalid')
