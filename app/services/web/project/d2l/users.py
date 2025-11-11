import json
import base64

from urllib.parse import urlencode

from .response import Response

class User(object):
    def __init__(self, client) -> None:
        """Working with users in Brightspace

        https://docs.valence.desire2learn.com/res/user.html

        Args:
            client (Client): Client.
        """
        self._client = client

    def get_me(self, params: dict = None) -> Response:
        """Retrieve the current user context’s user information.

        https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-users-whoami
        GET /d2l/api/lp/(version)/users/whoami

        Args:
            params (dict, optional): Query. Defaults to None.

        Returns:
            Response:  This action returns a WhoAmIUser JSON block for the current user context.
        """
        # print("{}users/whoami".format(self._client.lp_url))
        return self._client._do_get("{}users/whoami".format(self._client.lp_url), params=params)

    def get_user(self, user_id: int = 0, full: bool = False) -> Response:
        """Retrieve data for a particular user.

        https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-users-(userId)
        GET /d2l/api/lp/(version)/users/(userId)

        Args:
            EID: str the eid of the user to get
            full: bool (Optional) - inlcude names for this user
                https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-users-(userId)-names
                GET /d2l/api/lp/(version)/users/(userId)/names

        Returns:
            Response:  This action returns a WhoAmIUser JSON block for the current user context.
        """
        result = self._client._do_get("{}users/{}".format(self._client.lp_url, user_id))
        # print(result)
        if result['status'] == 'success':
            if full:
                names = self._client._do_get("{}users/{}/names".format(self._client.lp_url, user_id))
                if names['status'] == 'success':
                    result['data']['names'] = names['data']

            return result

        return self._client.return_error_state(f'User ID not found ({user_id})')

    def get_user_by_EID(self, EID : str, full: bool = False) -> Response:
        """Retrieve data for a user based on their EID (Staff / Student / Third Party Number)

        https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-users-
        GET /d2l/api/lp/(version)/users/

        Args:
            EID: str the eid of the user to get
            full: bool (Optional) - include names for this user
                https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-users-(userId)-names
                GET /d2l/api/lp/(version)/users/(userId)/names

        Returns:
            Response:  This action returns a WhoAmIUser JSON block for the current user context.
        """

        result = self._client._do_get("{}users/?userName={}".format(self._client.lp_url, EID))
        # print(f'get_user_by_EID : {result}')
        if result['status'] == 'success':
            if full:
                names = self._client._do_get("{}users/{}/names".format(self._client.lp_url, result['data']['UserId']))
                if names['status'] == 'success':
                    result['data']['names'] = names['data']

            return result

        return self._client.return_error_state(f'User not found ({EID})')

    def get_user_by_email(self, email : str, full: bool = False) -> Response:
        """Retrieve data for a user based on userName

        https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-users-
        GET /d2l/api/lp/(version)/users/

        Args:
            EID: str the eid of the user to get
            full: bool (Optional) - inlcude names for this user
                https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-users-(userId)-names
                GET /d2l/api/lp/(version)/users/(userId)/names

        Returns:
            Response:  This action returns a WhoAmIUser JSON block for the current user context.
        """

        result = self._client._do_get("{}users/?externalEmail={}".format(self._client.lp_url, email))
        # print(result)
        if result['status'] == 'success':
            if full:
                names = self._client._do_get("{}users/{}/names".format(self._client.lp_url, result['data']['UserId']))
                if names['status'] == 'success':
                    result['data']['names'] = names['data']

            return result

        return self._client.return_error_state(f'User not found ({email})')

    def create_user(self, eid: str, org_id: str,  role: int,
                            firstname: str, lastname: str, email: str,
                            middlename: str = None,
                            legal_firstname: str = None, legal_lastname: str = None,
                            preferred_firstname: str = None, preferred_lastname: str = None,
                            sort_lastname: str = None,
                            active: bool = True, send_create_mail: bool = False) -> Response:
        """Create a new user entity.

        https://docs.valence.desire2learn.com/res/user.html#post--d2l-api-lp-(version)-users-
        POST /d2l/api/lp/(version)/users/

        Args:
            Details about the user

        Returns:
            Response:  This action returns a UserData JSON block for the newly created user,
                        to give you immediate access to the user’s UserId property.
        """

        payload = json.dumps({
            "OrgDefinedId": org_id,
            "FirstName": firstname,
            "MiddleName": middlename,
            "LastName": lastname,
            "ExternalEmail": email,
            "UserName": eid,
            "RoleId": role,
            "IsActive": active,
            "SendCreationEmail": send_create_mail
        })

        # print(f"create user: {payload}")
        result = self._client._post("{}users/".format(self._client.lp_url), data=payload)
        if result['status'] == 'success':
            if legal_firstname or legal_lastname or preferred_firstname or preferred_lastname or sort_lastname:
                names = self.update_names(result['data']['UserId'],
                                            legal_firstname, legal_lastname,
                                            preferred_firstname, preferred_lastname,
                                            sort_lastname)
                if names['status'] == 'success':
                    result['data']['names'] = names['data']

        return result

    def delete_user(self, user_id: str):
        result = self._client._delete("{}users/{}".format(self._client.lp_url, user_id))
        return result

    # internal usage
    def update_names(self, user_id:int = 0,
                            legal_firstname: str = None, legal_lastname: str = None,
                            preferred_firstname: str = None, preferred_lastname: str = None,
                            sort_lastname: str = None) -> Response:
        """
        https://docs.valence.desire2learn.com/res/user.html#put--d2l-api-lp-(version)-users-(userId)-names
        PUT /d2l/api/lp/(version)/users/(userId)/names
        """
        return self._client._put("{}users/{}/names".format(self._client.lp_url, user_id), data=json.dumps({
                "LegalFirstName": legal_firstname,
                "LegalLastName": legal_lastname,
                "PreferredFirstName": preferred_firstname,
                "PreferredLastName": preferred_lastname,
                "SortLastName": sort_lastname
            }))

    def update_user(self, eid: str, org_id: str,
                            firstname: str, lastname: str, email: str,
                            middlename: str = None,
                            legal_firstname: str = None, legal_lastname: str = None,
                            preferred_firstname: str = None, preferred_lastname: str = None,
                            sort_lastname: str = None,
                            active: bool = True) -> Response:
        """Update data for a particular user.

        https://docs.valence.desire2learn.com/res/user.html#put--d2l-api-lp-(version)-users-(userId)
        PUT /d2l/api/lp/(version)/users/(userId)

        Args:
            Details about the user

        Returns:
            Response:  This action returns a UserData JSON block for the user’s updated data.
        """

        user = self.get_user_by_EID(eid)
        if user['status'] == 'success':
            payload = json.dumps({
                "OrgDefinedId": org_id,
                "FirstName": firstname,
                "MiddleName": middlename,
                "LastName": lastname,
                "ExternalEmail": email,
                "UserName": eid,
                "Activation": {
                    "IsActive": active
                },
                "Pronouns": None
            })

            # print(f"update user: {payload}")
            result = self._client._put("{}users/{}".format(self._client.lp_url, user['data']['UserId']), data=payload)
            if result['status'] == 'success':
                if legal_firstname or legal_lastname or preferred_firstname or preferred_lastname or sort_lastname:
                    names = self.update_names(result['data']['UserId'],
                                                legal_firstname, legal_lastname,
                                                preferred_firstname, preferred_lastname,
                                                sort_lastname)
                    if names['status'] == 'success':
                        result['data']['names'] = names['data']
            return result
        return user

    # Get the user enrollment page
    def get_course_enrollments_per_page(self, user_id: str, filter_role:int = 0, bookmark:str = None) -> Response:
        """Retrieve a list of all enrollments for the provided user.

        https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-lp-(version)-enrollments-users-(userId)-orgUnits-
        GET /d2l/api/lp/(version)/enrollments/users/(userId)/orgUnits/

        Args:
            user_id (str): User ID.
            filter_role (int): Filter on a Specific Role
            bookmark (str): (optional) previous bookmark

        Returns:
            Response: This action returns a paged result set containing the resulting UserOrgUnit data blocks for the segment
                      following your bookmark parameter (or the first segment if the parameter is empty or missing).
        """


        url = f"{self._client.lp_url}/enrollments/users/{user_id}/orgUnits/"

        params = {'orgUnitTypeId' : 3} # only course offerings.
        if bookmark:
            params['bookmark'] = bookmark

        if int(filter_role) > 0:
            params['roleId'] = filter_role

        if params:
            url = '{}?{}'.format(url, urlencode(params))

        return self._client._do_get(url)

    def get_course_enrollments_by_user_id(self, user_id: str, role: int = 0) -> Response:
        """Retrieve a list of all enrollments for the provided user

        Args:
            EID (str): The EID of the user
            role (int): Search only for this role

        Returns:
            Response: This action returns a paged result set containing the resulting UserOrgUnit data blocks for the segment
                      following your bookmark parameter (or the first segment if the parameter is empty or missing).
        """

        result = {'status': 'success', 'data': []}
        has_pages = True
        bookmark = None

        while has_pages:
            page = self.get_course_enrollments_per_page(user_id, role, bookmark)

            if page['status'] == "success":
                if 'Items' in page['data']:
                    result['data'] = result['data'] + page['data']['Items']

                if 'PagingInfo' in page['data']:
                    bookmark = page['data']['PagingInfo']['Bookmark']
                    has_pages = page['data']['PagingInfo']['HasMoreItems']
                else:
                    has_pages = False
            else:
                has_pages = False
                result = page

        return result

    def get_course_enrollments_by_EID(self, EID: str, role: int = 0) -> Response:
        """Retrieve a list of all enrollments for the provided user - search by EID first

        Args:
            EID (str): The EID of the user
            role (int): Search only for this role

        Returns:
            Response: This action returns a paged result set containing the resulting UserOrgUnit data blocks for the segment
                      following your bookmark parameter (or the first segment if the parameter is empty or missing).
        """

        user = self.get_user_by_EID(EID)
        if user['status'] == 'success':
            return self.get_course_enrollments_by_user_id(user['data']['UserId'], role)

        return user

    # AMA-744
    # get users profile image
    def get_enrolled_users_profile_image(self, user_id: str) -> Response:
        """Retrieve a particular profile image, by User ID.

        https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-profile-user-(userId)-image
        GET /d2l/api/lp/(version)/profile/user/(userId)/image

        Args:
            user_id (str): The user_id of the user

        Returns:
            Response: his action returns a file stream containing the profile image for the identified profile.
            Note that the back-end service may return a profile image larger than your provided size.
        """

        # returns url of profile user image
        url = self._client._raw("GET", "{}/profile/user/{}/image".format(self._client.lp_url, user_id))
        if url.status_code == 200:
            return {'status': 'success', 'profileImage': base64.b64encode(url.content).decode('utf-8')}

        return {'status': 'ERR', 'profileImage': "Not Found"}

    # update profilepic
    def update_enrolled_users_profile_image(self, user_id: str, profileImageData: str) -> Response:
        """Update the profile image for the identified personal profile, by User ID.

        https://docs.valence.desire2learn.com/res/user.html#post--d2l-api-lp-(version)-profile-user-(userId)-image
        POST /d2l/api/lp/(version)/profile/user/(userId)/image

        Args:
            user_id (str): The user_id of the user
            profileImageData (str): profile image data

        Input:
            Provide an uploaded image file using the simple file upload process; the content-disposition part header for the file
            part should have the name profileImage
        """

        imageurl = f"{self._client.lp_url}/profile/user/{user_id}/image"

        file_name = profileImageData.filename
        file_data = profileImageData.read()
        # get extension except .
        file_extension = file_name[file_name.rfind(".")+1:]

        # Set the headers
        headers = {
            "Content-Type": "multipart/form-data; boundary=xxBOUNDARYxx",
            "Content-Length": str(len(base64.b64encode(file_data).decode()))
        }

        # construct body as bytes
        boundary = b"xxBOUNDARYxx"
        body = b"--" + boundary + b'\r\n'
        body += b'Content-Disposition: form-data; name="profileImage"; filename="' + file_name.encode() + b'"\r\n'
        body += b"Content-Type: image/"+file_extension.encode()+ b'\r\n'
        body += b"\r\n" + file_data + b"\r\n"
        body += b"--" + boundary + b"--"

        return self._client._post(imageurl, data=body, headers=headers)

    # return all users
    # def get_all_users(self, bookmark: str = None) -> Response:
    #     """Retrieve data for one or more users.

    #     Args:
    #         bookmark (str): Bookmark to use for fetching next data set segment.

    #     Returns:
    #         Response: If you use this action to find a single user’s data by userName, this route action a
    #         single UserData JSON block if successful, and a 404 Not Found if it cannot find a matching user.
    #     """

    #     users_url = f"{self._client.lp_url}/users/"

    #     print(users_url)
    #     return self._client._do_get(users_url)
