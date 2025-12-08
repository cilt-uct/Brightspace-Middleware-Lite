# ruff: noqa: E402, I001
import json
import os
import urllib.parse
import uuid
from datetime import datetime

import MySQLdb.cursors

from ..constants import COURSE_OFFERING_TYPE, TEACHING_ROLES
from ..utils import Utils
from .response import Response

class Course:

    def __init__(self, client) -> None:
        """Working with Courses in Brightspace

        https://docs.valence.desire2learn.com/res/course.html

        Args:
            client (Client): Library Client.
        """
        self._client = client

    def get_course_by_id(self, org_unit_id: int, params: dict = None) -> Response:
        """Retrieve a course offering.

        https://docs.valence.desire2learn.com/res/course.html#get--d2l-api-lp-(version)-courses-(orgUnitId)
        GET /d2l/api/lp/(version)/courses/(orgUnitId)

        Args:
            org_unit_id (int): Org unit ID.
            params (dict, optional): Query. Defaults to None.

        Returns:
            Response: This action returns a CourseOffering JSON block with the provided course’s information.
        """
        return self._client._do_get(f'{self._client.lp_url}courses/{org_unit_id}', params=params)

    def get_course_by_code(self, org_code: str, name: str = None, first: bool = False) -> Response:
        """Retrieve a course offering by searching the exactOrgUnitCode

        https://docs.valence.desire2learn.com/res/orgunit.html#get--d2l-api-lp-(version)-orgstructure-
        GET /d2l/api/lp/(version)/orgstructure/

        Args:
            org_code (str): Org unit code.
            org_name (str, optional): Query. Defaults to None.

        Returns:
            Response: This action returns a CourseOffering JSON block with the provided course’s information.
        """
        params = {
            'exactOrgUnitCode': urllib.parse.quote(org_code),
            'orgUnitType': COURSE_OFFERING_TYPE
        }
        if name:
            params['exactOrgUnitName'] = name

        url = f'{self._client.lp_url}orgstructure/?{urllib.parse.urlencode(params)}'
        result = self._client._do_get(url)

        if first:
            if result['status'] == 'success' and len(result['data']['Items']) > 0:
                result['data'] = result['data']['Items'][0]

                if 'Identifier' not in result['data']:
                    return self._client.return_error_state(f'No Course found ({org_code})')
            else:
                return self._client.return_error_state(f'No Course found ({org_code})')

        if result['status'] != 'success':
            return result

        # The full Course.CourseOffering JSON
        return self.get_course_by_id(result['data']['Identifier'])

    def get_course(self, val: int | str, use_id: bool = False, params: dict = None) -> Response:
        """ call the appropriate function to get the course info """
        return self.get_course_by_id(val) if use_id else self.get_course_by_code(val)

    def create_course_template(self, name: str, code: str, path: str, parent_org_id: int) -> Response:
        """Create a new course template.

        https://docs.valence.desire2learn.com/res/course.html#post--d2l-api-lp-(version)-coursetemplates-
        POST /d2l/api/lp/(version)/coursetemplates/

        Args:
            name (str): Name of the Template
            code (str): Code for the Template
            path (str): Path for the template content
            parent_org_id (int): Org unit id

        Returns:
            Response: This action returns a CourseTemplate JSON block containing the data for the new course template.
        """
        # when adding path get BadRequest - so set as empty
        payload = json.dumps({
            'Name': name,
            'Code': code,
            'Path': '',
            'ParentOrgUnitIds': [ int(parent_org_id) ]
        })

        return self._client._post(f'{self._client.lp_url}coursetemplates/', data=payload)

    def delete_course_template(self, org_unit_id: str):
        return self._client._delete(f'{self._client.lp_url}coursetemplates/{org_unit_id}')

    def get_course_template(self, code: str, name: str = None, path: str = None, parent_org_id: int = None) -> Response:

        exists = self._client.orgunit.get_course_template_by_code(code)
        if exists['status'] == 'success':
            return exists

        if None in [name, path, parent_org_id]:
            raise Exception(f'Course Template not found, please provide values for {name}, {path} and {parent_org_id}.')

        return self.create_course_template(name, code, path, parent_org_id)

    def create_site_direct(self, name: str, code: str, path: str, template_id: int, semester_id: int) -> Response:
        """Create a new course

        https://docs.valence.desire2learn.com/res/course.html#post--d2l-api-lp-(version)-courses-
        POST /d2l/api/lp/(version)/courses/

        Args:
            name (str): Name of the Course Offering
            code (str): Code for the Course Offering
            path (str): Path for the Course Offering content
            template_id (int): Template id
            semester_id (int): Semester id

        Returns:
            Response: This action returns a CourseOffering JSON block for the newly created course.
        """
        # when adding path get BadRequest - so set as empty
        payload = json.dumps({
            'Name': name,
            'Code': code,
            'Path': '',
            'CourseTemplateId': template_id,
            'SemesterId': semester_id,
            'StartDate': None,
            'EndDate': None,
            'LocaleId': None,
            'ForceLocale': False,
            'ShowAddressBook': False,
            'Description': { 'Content': f'Course for "{name}"', 'Type': 'Text' },
            'CanSelfRegister': False
        })
        # print(payload)
        return self._client._post('{self._client.lp_url}courses/', data=payload)

    def create_site(self, course_code: str,
                            name: str,
                            template_id:int,
                            semester_id:int,
                            create_even_if_it_exists: bool = False,
                            check_name: bool = False,
                            active: bool = False):

        # using course code let's see if one exist with exactOrgUnitCode = course_code
        if check_name:
            _found_course = self.get_course_by_code(course_code, name=name, first=True)
        else:
            _found_course = self.get_course_by_code(course_code, first=True)

        if create_even_if_it_exists or _found_course['status'] != 'success':
            # so let's just create a course - don't care if it exists already
            new_course = self.create_site_direct(name, course_code, '', template_id, semester_id)

            # print(new_course)
            if new_course['status'] == 'BadRequest':
                raise Exception('Some thing went wrong: ' + new_course['data'])

            new_course['data']['created'] = 1

            if new_course['status'] == 'success':
                # update course with active
                self.update_course_site(int(new_course['data']['Identifier']),
                                            new_course['data']['Name'],
                                            new_course['data']['Code'],
                                            active=active,
                                            description=new_course['data']['Description']['Text'],
                                            start_date=new_course['data']['StartDate'],
                                            end_date=new_course['data']['EndDate'])

                # update path
                update_path = self._client.orgunit.update_org_properties(int(new_course['data']['Identifier']),
                                                                new_course['data']['Name'],
                                                                new_course['data']['Code'],
                                                                '/content/enforced/{}/'.format(new_course['data']['Identifier']),
                                                                'course')
                if update_path['status'] == 'success':
                    new_course['data']['Path'] = f'/content/enforced/{new_course['data']['Identifier']}/'

            return new_course
        else:
            _found_course['data']['created'] = 0
            return _found_course

    def create_community_site(self, name: str,
                                    faculty: str,
                                    term: int = 0,
                                    course_code:str = '',
                                    create_even_if_it_exists: bool = False,
                                    check_name: bool = False,
                                    active: bool = True):
        # print(locals())

        site_term = 'other'
        if term != 'other' and int(term) > 0:
            site_term = term

        if faculty == 'other' or 'faculty' == 'null':
            faculty = 'UCT'

        semester_id = Utils.get_id_from_valid_or_default(self._client.orgunit.get_semester_by_term,
                                                            site_term,
                                                            datetime.now().year)
        template_id = Utils.get_id_from_valid_or_default(self.get_course_template,
                                                            f'{faculty}_other_template',
                                                            'UCT_other_template')

        if semester_id > 0:
            if template_id > 0:

                if not course_code:
                    guid = uuid.uuid4()
                    course_code = f'{faculty}_{guid}_{term}'

                return self.create_site(course_code=course_code,
                                            name=name,
                                            template_id=template_id,
                                            semester_id=semester_id,
                                            create_even_if_it_exists=create_even_if_it_exists,
                                            active=active)
            else:
                return self._client.return_error_state(f'No Template found ({faculty}_other_template)')
        else:
            return self._client.return_error_state(f'No Semester found ({site_term})')

    def create_course_site(self, course_code: str = '',
                                    name: str = '',
                                    template: str = '',
                                    term: int = 0,
                                    dept:str = 'other',
                                    create_even_if_it_exists: bool = False,
                                    check_name: bool = False,
                                    active: bool = True):
        # print(locals())

        site_term = 'other'
        if term != 'other' and int(term) > 0:
            site_term = term

        department_id = Utils.get_id_from_valid_or_default(self._client.orgunit.get_department_by_code,
                                                            dept, 'other')
        semester_id = Utils.get_id_from_valid_or_default(self._client.orgunit.get_semester_by_term,
                                                            site_term, datetime.now().year)

        # print(f'{department_id} {semester_id}')
        if semester_id > 0:
            _template = self.get_course_template(code=template,
                                                name=template,
                                                path='',
                                                parent_org_id=department_id)

            if _template['status'] == 'success':
                return self.create_site(course_code=course_code,
                                        name=name,
                                        template_id=_template['data']['Identifier'],
                                        semester_id=semester_id,
                                        create_even_if_it_exists=create_even_if_it_exists,
                                        check_name=check_name,
                                        active=active)
            else:
                return self._client.return_error_state(f'No Template found ({template})')
        else:
            return self._client.return_error_state(f'No Semester found ({site_term})')

    def update_course_site(self, org_id:int,
                                    name: str, code:str, active: bool,
                                    description:str,
                                    start_date:str = None, end_date:str = None) -> Response:
        """Update a current course offering.

        https://docs.valence.desire2learn.com/res/course.html#put--d2l-api-lp-(version)-courses-(orgUnitId)
        PUT /d2l/api/lp/(version)/courses/(orgUnitId)

        Args:
            name (str): Name of the Course Offering
            code (str): Code for the Course Offering

        Returns:
            Response: This action returns a CourseOffering JSON block for the newly created course.
        """

        # when adding path get BadRequest - so set as empty
        payload = json.dumps({
            'Name': name,
            'Code': code,
            'StartDate': start_date,
            'EndDate': end_date,
            'IsActive': active,
            'Description': { 'Content': description, 'Type': 'Text' },
            'CanSelfRegister': False
        })

        # print(f"update_course_site : {payload}")
        return self._client._put(f'{self._client.lp_url}courses/{org_id}', data=payload)

    def delete_course(self, org_unit_id: str):
        return self._client._delete('{self._client.lp_url}courses/{org_unit_id}')

    # TODO: Add filter by role to NEXT
    # https://{server}/d2l/api/course/classlist/10455?paged=1&lecturer=1

    def filter_by_role(self, response: Response, role: int = 0) -> Response:
        if response['status'] == 'success' and role > 0:
            if 'Objects' in response['data']:
                response['data']['Objects'] = list(filter(lambda x: (x['RoleId'] == role), response['data']['Objects']))
            else:
                response['data'] = list(filter(lambda x: (x['RoleId'] == role), response['data']))

        return response

    def get_course_classlist_by_id(self, org_unit_id: int,
                                            filter_role:int = 0,
                                            paged: bool = False,
                                            bookmark: str = None) -> Response:

        """Retrieve the enrolled users in the classlist for an org unit.

        https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-le-(version)-(orgUnitId)-classlist-
        GET /d2l/api/le/(version)/(orgUnitId)/classlist/
        GET /d2l/api/le/(version)/(orgUnitId)/classlist/paged/

        Args:
            org_unit_id (str): Org unit ID.

        Returns:
            Response: This action returns a JSON array of ClasslistUser data blocks.

        Warning:
            Some orgunits can have very large numbers of enrolled users, so the classlist can be
            a quite large collection. We advise you to make very careful use of this API call because
            it asks for an unbounded set of results.
            We strongly recommend you use the paged version of this call instead.
        """

        # NOTE: heed the warning ...
        if not paged:
            return self.filter_by_role(self._client._do_get(f'{self._client.le_url}{org_unit_id}/classlist/'),
                                        filter_role)

        params = {}
        if bookmark:
            params['bookmark'] = bookmark

        url = f'{self._client.le_url}{org_unit_id}/classlist/paged/?{urllib.parse.urlencode(params)}'
        return self.filter_by_role(self._client._do_get(url), filter_role)

    def get_course_enrollments_by_id_by_page(self, org_unit_id:int,
                                                    bookmark:str = None,
                                                    role_id:int = 0,
                                                    active:int = -1) -> Response:

        return self.get_course_enrollments_by_id(org_unit_id = org_unit_id,
                                                    bookmark = bookmark,
                                                    role_id = role_id,
                                                    active=active)

    def get_course_enrollments_by_id(self, org_unit_id:int,
                                            bookmark: str = None,
                                            role_id:int = 0,
                                            active:int = -1) -> Response:

        """Retrieve the collection of users enrolled in the identified org unit.

        https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-lp-(version)-enrollments-orgUnits-(orgUnitId)-users-
        GET /d2l/api/lp/(version)/enrollments/orgUnits/(orgUnitId)/users/

        Args:
            org_unit_id (str): Org unit ID.
            roleId (int): Optional. Filter list to a specific user role.
            isActive (int): Optional. Filter list to only active or inactive users.
            bookmark (string): Optional. Bookmark to use for fetching next data set segment.

        Returns:
            Response: This action returns a paged result set containing the resulting OrgUnitUser data blocks
            for the segment following your bookmark parameter
            (or the first segment if the parameter is empty or missing).
        """
        params = {}
        if bookmark:
           params['bookmark'] = bookmark

        if int(active) >= 0:
           params['isActive'] = 'true' if int(active) == 1 else 'false'

        if int(role_id) > 0:
           params['roleId'] = role_id

        url = f'{self._client.lp_url}/enrollments/orgUnits/{org_unit_id}/users/'
        return self._client._do_get(url, params = params)

    def get_enrollment_by_id_for_user_id(self, org_id:int, user_id:int):
        """Retrieve enrollment details for a user in the provided org unit.

        https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-lp-(version)-enrollments-orgUnits-(orgUnitId)-users-(userId)
        GET /d2l/api/lp/(version)/enrollments/orgUnits/(orgUnitId)/users/(userId)

        Args:
            orgUnitId (D2LID) - Org unit ID.
            userId (D2LID) - User ID.

        Returns:
            This action returns an EnrollmentData JSON block.
        """

        if not user_id:
            return self._client.return_error_state(f'User ({user_id}) Not Found')

        if not org_id:
            return self._client.return_error_state(f'Org ID ({org_id}) is required')

        return self._client._do_get('{self._client.lp_url}enrollments/orgUnits/{org_id}/users/{user_id}')

    def get_enrollment_by_id_for_user(self, org_id:int, user_id:int = 0, eid:str = None):
        """Retrieve enrollment details for a user in the provided org unit.

        https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-lp-(version)-enrollments-orgUnits-(orgUnitId)-users-(userId)
        GET /d2l/api/lp/(version)/enrollments/orgUnits/(orgUnitId)/users/(userId)

        Args:
            orgUnitId (D2LID) - Org unit ID.
            userId (D2LID) - User ID.

        Returns:
            This action returns an EnrollmentData JSON block.
        """
        if eid:
            _found_user = self._client.user.get_user_by_EID(eid)
            if _found_user['status'] == 'success':
                user_id = _found_user['data']['UserId']

        return self.get_enrollment_by_id_for_user_id(org_id, user_id)

    def enroll_user_in_role(self, org_unit_id: int, user_id: int, role_id: int) -> Response:
        """Enroll a lecturer to org unit

        https://docs.valence.desire2learn.com/res/enroll.html#post--d2l-api-lp-(version)-enrollments-
        POST /d2l/api/lp/(version)/enrollments/

        Args:
            org_unit_id (int): Org unit ID
            user_id (int): User ID
            role_id (int): Role ID

        Returns:
            Response: This action returns a CourseTemplate JSON block containing the data for the new course template.
        """
        payload = json.dumps({
            'OrgUnitId': int(org_unit_id),
            'UserId': int(user_id),
            'RoleId': int(role_id),
            'IsCascading': False
        })

        print(f'enroll_user_in_role {org_unit_id} {user_id} {role_id}')
        return self._client._post('{self._client.lp_url}enrollments/', data=payload)

    # Run through the batch and swap out EID's with userId's and construct the right format for D2L
    def construct_enrollment_batch(self, items: list[dict]) -> list:

        eid_to_userid = {}
        eids_to_lookup = [item['eid'] for item in items if not item.get('user_id') and item.get('eid')]

        if eids_to_lookup:
            placeholders = ','.join(['%s'] * len(eids_to_lookup))
            query = f'SELECT CN as EID, AID as UserId FROM idv_user WHERE CN IN ({placeholders})'

            with self._client.mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute(query, eids_to_lookup)
                results = cursor.fetchall()
                eid_to_userid = {entry['EID']: entry['UserId'] for entry in results}

        final_batch = []
        for item in items:
                user_id = item.get('user_id') or eid_to_userid.get(item.get('eid'))
                role_id = Utils.get_internal_role(item['role'])
                if not user_id or role_id == 0:
                    continue # Skip if no valid user_id or role_id

                final_batch.append({
                    'OrgUnitId': item['org_id'],
                    'UserId': user_id,
                    'RoleId': role_id
                })

        return final_batch

    def enroll_user_batch(self, batch:list) -> Response:
        """Create a batch of new enrollments for users.

        https://docs.valence.desire2learn.com/res/enroll.html#post--d2l-api-lp-(version)-enrollments-batch-
        POST /d2l/api/lp/(version)/enrollments/batch/

        Note: that you may only include a maximum of 1000 enrollments in each batch

        Args:
            batch (list): Array of Enrollment dictionaries
                {
                    "OrgUnitId": <number:D2LID>,
                    "UserId": <number:D2LID>,
                    "RoleId": <number:D2LID>,
                    "SendEnrollmentEmail":  <boolean>|null  // Added with LMS v20.25.1
                }

        Returns:
            This action returns a JSON array. If any attempt to create an enrollment failed, the back-end service
            includes a BatchEnrollmentError JSON block describing why creating that particular enrollment failed.
            If all enrollment actions suceeded, the service returns an empty JSON array.
        """
        if not isinstance(batch, list):
            return self._client.return_error_state(f'Batch must be a list, got {type(batch)}')

        final_batch = self.construct_enrollment_batch(batch)
        if not final_batch:
            return self._client.return_error_state(f'Batch is empty {final_batch}')

        final_result: list = []

        # Post in chunks of 1000 - D2L API limit
        for chunk in Utils.batch(final_batch, 1000):
            result = self._client._post(f'{self._client.lp_url}/enrollments/batch/', data=json.dumps(chunk))

            if result.get('status') == 'ERR':
                return result

            final_result.extend(result.get('data', []))

        # If final_result is empty, it means all enrollments were successful
        #   "If all enrollment actions suceeded, the service returns an empty JSON array."
        if not final_result:
            return self._client.return_success_state('All enrollments were successful.')

        # There were some enrollments that failed
        return self._client.return_error_state(final_result)

    def enroll_any_user(self, org_id: int = 0,
                                user_id:int = 0,
                                eid:str = None,
                                role:int = 0,
                                add_to_announcement:bool = True) -> Response:
        # print(f"{org_id}: {user_id} | {eid} : {role}")

        if not role:
            return self._client.return_error_state(f'Role ({role}) Not Found')

        if not org_id:
            return self._client.return_error_state(f'Org ID ({org_id}) is required')

        if int(user_id) > 0 or eid:
            if eid:
                _found_user = self._client.user.get_user_by_EID(eid)
            else:
                _found_user = self._client.user.get_user(user_id)

            if _found_user['status'] == 'success':
                if _found_user['data']['Activation']['IsActive']:

                    result = self.enroll_user_in_role(org_id, _found_user['data']['UserId'], role)

                    if result['status'] == 'success' and role in TEACHING_ROLES:
                        # AMA-733: Enrol into Amathuba Announcements Site
                        ama_announcement_site = self.get_course_by_code('uct-amathuba', first=True)
                        if add_to_announcement and ama_announcement_site['status'] == 'success':
                            self.enroll_user_in_role(ama_announcement_site['data']['Identifier'],
                                                        _found_user['data']['UserId'], 121) # Member

                    return result
                else:
                    msg = f'User {_found_user['data']['UserName']} ({_found_user['data']['UserId']}) is Inactive'
                    return self._client.return_error_state(msg)

            return _found_user

        return self._client.return_error_state(f'User ID ({user_id}) or EID ({eid}) is invalid')

    def enroll_student_to_multiple_sites(self, org_ids:str = None, eid:str = None, role:int = 0) -> Response:
        if eid:
            _found_user = self._client.user.get_user_by_EID(eid)

            if _found_user['status'] == 'success':
                if _found_user['data']['Activation']['IsActive']:
                    org_ids_list = org_ids.split(',')
                    for org_id in org_ids_list:
                        self.enroll_user_in_role(org_id, _found_user['data']['UserId'], role)

                    return self._client.return_success_state('Student enrolled in all sites')
                else:
                    msg = f'User {_found_user['data']['UserName']} ({_found_user['data']['UserId']}) is Inactive'
                    return self._client.return_error_state(msg)

            return _found_user

        return self._client.return_error_state(f'User ID (EID ({eid}) is invalid')

    def remove_enrollment(self, org_unit_id: int, user_id: int, params: dict = None) -> Response:
        """Delete a user's enrollment in a provided org unit.

        https://docs.valence.desire2learn.com/res/enroll.html#delete--d2l-api-lp-(version)-enrollments-orgUnits-(orgUnitId)-users-(userId)
        DELETE /d2l/api/lp/(version)/enrollments/orgUnits/(orgUnitId)/users/(userId)

        Args:
            org_unit_id (int): Org unit ID
            user_id (int): User ID

        Returns:
            Return. Unlike most delete actions, this action returns an EnrollmentData JSON block showing
                    the enrollment status just before this action deleted the user's enrollment
        """
        print(f'remove_enrollment {org_unit_id} {user_id}')
        return self._client._delete(f'{self._client.lp_url}enrollments/orgUnits/{org_unit_id}/users/{user_id}')

    def import_file(self, org_unit_id: int, filename: str, params: dict = None) -> Response:
        """Create a new course import job request.

        https://docs.valence.desire2learn.com/res/course.html#post--d2l-api-le-(version)-import-(orgUnitId)-imports-
        POST /d2l/api/le/(version)/import/(orgUnitId)/imports/

        Args:
            org_unit_id (str): Org unit ID.
            params (dict, optional): Query. Defaults to None.

        Returns:
            Response: This action returns a CourseOffering JSON block with the provided course’s information.
        """
        basename = os.path.basename(filename)

        url = '{self._client.le_url}import/{org_unit_id}/imports/'
        payload={}
        headers={'Accept': 'application/json'}
        files=[('file', (basename,open(filename,'rb'), 'application/zip'))]

        return self._client._post(url, headers=headers, data=payload, files=files)

    def copy_course_content(self, target_org_unit:int, src_org_unit:int, components = None) -> Response:
        """Queue up a new course copy job request - Copy content from Source to Target

        https://docs.valence.desire2learn.com/res/course.html#post--d2l-api-le-(version)-import-(orgUnitId)-copy-
        POST /d2l/api/le/(version)/import/(orgUnitId)/copy/

        Args:
            target_org_unit (str): Target Org unit ID.
            src_org_unit (str): Source Org unit ID.

        Returns:
            Return. This action returns a CreateCopyJobResponse JSON block.
        """

        if not components:
            components = ['Checklists', 'Content', 'CourseFiles', 'Dropbox', 'Grades', 'Quizzes', 'Rubrics']

        payload = json.dumps({
            'SourceOrgUnitId': src_org_unit,
            'Components': components,
        })

        return self._client._post('{self._client.le_url}import/{target_org_unit}/copy/', data=payload)

    def get_users_by_role(self, org_unit_id:int, role:str=None, only_active:bool = True) -> list:
        # print(f'get_users_by_role {org_unit_id=} {role=} {useActive=}')
        result = []
        if role:
            orgdata = self.get_course_enrollments_by_id(org_unit_id,
                                                        roleId=Utils.get_internal_role(role),
                                                        active=1 if only_active else -1)
            if orgdata['status'] == 'success':
                result = [
                            {
                                'name': item['User']['DisplayName'],
                                'id': item['User']['Identifier'],
                                'eid': item['User']['UserName'],
                                'email': item['User'].get('EmailAddress', None),
                                'role': item['Role']['Name']
                            }
                            for item in orgdata['data']['Items']
                        ]
        return result

    def get_list_of_owners(self, org_unit_id: int) -> list:
        # Let's fetch the owners (lecturers) for this course ...
        owners = self.get_users_by_role(org_unit_id, 'Lecturer')

        # additional lecturer role
        if not owners:
            owners = self.get_users_by_role(org_unit_id, 'LecturerTutor')

        # well lets' see if there are owners in the site ...
        if not owners:
            owners = self.get_users_by_role(org_unit_id, 'Owner')

        # well there are no lecturers / owners - then default to "Support Staff"
        if not owners:
            owners = self.get_users_by_role(org_unit_id, 'Support Staff')

        return owners
