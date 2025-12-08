import json
import base64

from .response import Response

# REF: https://community.brightspace.com/s/article/API-Cookbook-Adding-Course-Content

class Content(object):
    def __init__(self, client) -> None:
        """Working with Course Content in Brightspace

        https://docs.valence.desire2learn.com/res/content.html

        Args:
            client (Client): Client.
        """
        self._client = client

    def retrieve_root(self, org_unit_id: int) -> Response:
        """Retrieve the root module(s) for an org unit.

        https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-root-
        GET /d2l/api/le/(version)/(orgUnitId)/content/root/

        Args:
            org_unit_id (int): Org unit ID.

        Returns:
            Return. This action returns a JSON array of ContentObject data blocks of type Module.
        """
        return self._client._do_get(f"{self._client.le_url}{org_unit_id}/content/root/")

    def get_module(self, org_unit_id: int, module_id: int) -> Response:
        """Retrieve a specific module for an org unit.

        https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-modules-(moduleId)
        GET /d2l/api/le/(version)/(orgUnitId)/content/modules/(moduleId)

        Args:
            org_unit_id (int): Org unit ID.
            module_id (int): Module ID.

        Returns:
            Return. This action returns a ContentObject JSON data block of type Module.
        """
        return self._client._do_get(f"{self._client.le_url}{org_unit_id}/content/modules/{module_id}")

    def get_module_structure(self, org_unit_id: int, module_id: int) -> Response:
        """Retrieve the structure for a specific module in an org unit.

        https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-modules-(moduleId)-structure-
        GET /d2l/api/le/(version)/(orgUnitId)/content/modules/(moduleId)/structure/

        Args:
            org_unit_id (int): Org unit ID.
            module_id (int): Module ID.

        Returns:
            Return. This action returns a JSON array of ContentObject data blocks (can by either Module or Topic type blocks).
        """
        return self._client._do_get(f"{self._client.le_url}{org_unit_id}/content/modules/{module_id}/structure/")


    def create_root_module(self, org_unit_id: int,
                                title: str,
                                desc: str,
                                hidden: bool = False) -> Response:
        """Create a new root module for an org unit.

        https://docs.valence.desire2learn.com/res/content.html#post--d2l-api-le-(version)-(orgUnitId)-content-root-
        POST /d2l/api/le/(version)/(orgUnitId)/content/root/

        Args:
            org_unit_id (int): Org unit ID.


        Returns:
            Return. This action returns a ContentObject JSON data block of type Module.
        """
        payload = json.dumps({
            "Structure": [ ],
            "ModuleStartDate": None,
            "ModuleEndDate": None,
            "IsHidden": hidden,
            "IsLocked": False,
            "Id": None,
            "Title": title,
            "Description" : desc,
            "ShortTitle": "",
            "Type": 0
        })
        return self._client._post(f"{self._client.le_url}{org_unit_id}/content/root/", data=payload)

    def delete_module(self, org_unit_id: int, module_id: int) -> Response:
        """Delete a specific module from an org unit.

        https://docs.valence.desire2learn.com/res/content.html#delete--d2l-api-le-(version)-(orgUnitId)-content-modules-(moduleId)
        DELETE /d2l/api/le/(version)/(orgUnitId)/content/modules/(moduleId)

        Args:
            org_unit_id (int): Org unit ID.
            module_id (int): Module ID.

        Returns:
            200 OK - Action succeeded
        """
        return self._client._delete(f"{self._client.le_url}{org_unit_id}/content/modules/{module_id}")

    def add_file_to_module(self, org_unit_id: int, module_id: int, details:dict, file) -> Response:
        """Add a Topic to a Module

        https://docs.valence.desire2learn.com/res/content.html#post--d2l-api-le-(version)-(orgUnitId)-content-modules-(moduleId)-structure-
        POST /d2l/api/le/(version)/(orgUnitId)/content/modules/(moduleId)/structure/

        Args:
            org_unit_id (int): Org unit ID
            module_id (int): Module ID.
            title (str): Topic Title
            short (str): Short description of topic

        Returns:
            Return. This action returns a ContentObject JSON data block of type Module.
        """

        # get the site and ge the path
        site = self._client.course.get_course_by_id(org_unit_id)
        if site['status'] == 'success':

            payload = {
                "Title": "Replace",
                "ShortTitle": "",
                "Type": 1, # https://docs.valence.desire2learn.com/res/content.html#term-CONTENT_T
                "TopicType": 1, # https://docs.valence.desire2learn.com/res/content.html#term-TOPIC_T - 1 File Topic
                "Url": f"{site['data']['Path']}{file.filename}",
                "StartDate": None,
                "EndDate": None,
                "DueDate": None,
                "IsHidden": False,
                "IsLocked": False
            }
            payload.update(details)

            # construct body as bytes
            boundary_str = "xxBOUNDARYxx"
            boundary = boundary_str.encode()

            file_data = file.stream.read()
            file_content_type = file.content_type
            if file_content_type is None:
                file_content_type = "text/html"

            body = b"--" + boundary + b'\r\n'
            body += b"Content-Type: application/json\r\n"
            body += b"\r\n" + json.dumps(payload).encode() + b"\r\n"
            body += b"--" + boundary + b'\r\n'
            body += b'Content-Disposition: form-data; name=""; filename="' + file.filename.encode() + b'"\r\n'
            body += b"Content-Type: "+ file_content_type.encode() + b'\r\n'
            body += b"\r\n" + file_data + b"\r\n"
            body += b"--" + boundary + b"--"

            # Set the headers
            headers = {
                "Content-Type": f"multipart/mixed;boundary={boundary_str}",
                "Content-Length": str(len(body))
            }

            return self._client._post(f"{self._client.le_url}{org_unit_id}/content/modules/{module_id}/structure/",
                                    data=body, headers=headers)

        return site

    def add_link_to_module(self, org_unit_id: int, module_id: int,
                                        title: str,
                                        short: str,
                                        url: str) -> Response:
        """Add a Quicklink Topic to a Module

        https://docs.valence.desire2learn.com/res/content.html#post--d2l-api-le-(version)-(orgUnitId)-content-modules-(moduleId)-structure-
        POST /d2l/api/le/(version)/(orgUnitId)/content/modules/(moduleId)/structure/

        Args:
            org_unit_id (int): Org unit ID
            module_id (int): Module ID.
            title (str): Topic Title
            short (str): Short description of topic
            url (str): The Link to the quicklink

        Returns:
            Return. This action returns a ContentObject JSON data block of type Module.
        """
        payload = json.dumps({
            "Title": title,
            "ShortTitle": short,
            "Type": 1, # https://docs.valence.desire2learn.com/res/content.html#term-CONTENT_T
            "TopicType": 3, # https://docs.valence.desire2learn.com/res/content.html#term-TOPIC_T - 3 : Link
            "Url": url,
            "StartDate": None,
            "EndDate": None,
            "DueDate": None,
            "IsHidden": False,
            "IsLocked": False
        })

        return self._client._post(f"{self._client.le_url}{org_unit_id}/content/modules/{module_id}/structure/", data=payload)

    def update_module(self, org_unit_id: int, module_id: int,
                    title: str, short: str, desc: dict, type: int, hidden: bool = False, locked: bool = False,
                    start_date: str = None, end_date: str = None, due_date: str= None) -> Response:
        """Update a particular module for an org unit.

        https://docs.valence.desire2learn.com/res/content.html#put--d2l-api-le-(version)-(orgUnitId)-content-modules-(moduleId)
         PUT /d2l/api/le/(version)/(orgUnitId)/content/modules/(moduleId)

        Args:
            org_unit_id (int): Org unit ID.

        Returns:
            Return. This action returns a ContentObject JSON data block of type Module.
        """
        payload = json.dumps({
            "Title": title,
            "ShortTitle": short,
            "Type": type,
            "Description": desc,
            "ModuleStartDate": start_date,
            "ModuleEndDate": end_date,
            "ModuleDueDate": due_date,
            "IsHidden": hidden,
            "IsLocked": locked
        })
        return self._client._put(f"{self._client.le_url}{org_unit_id}/content/modules/{module_id}", data=payload)

    def order_module(self, org_unit_id: int, object_id: int, first: bool = True) -> Response:
        '''

        https://docs.valence.desire2learn.com/res/content.html#post--d2l-api-le-(version)-(orgUnitId)-content-order-objectId-(objectId)
        POST /d2l/api/le/(version)/(orgUnitId)/content/order/objectId/(objectId)

        Args:
            org_unit_id: Org unit ID.
            object_id: ID of the module unit to be ordered.
            first: True if module should be first, False it should be last.

        Returns:
             Return. This action returns an empty JSON with the status of the API call.
        '''

        position = 'first' if first else 'last'

        return self._client._post(f"{self._client.le_url}{org_unit_id}/content/order/objectId/{object_id}?position={position}")

    # AMA 679
    def course_topics_content(self, org_unit_id: int, topic_id: int) -> Response:
        """Retrieve the root module(s) for an org unit.

        https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-topics-(topicId)
        GET /d2l/api/le/(version)/(orgUnitId)/content/topics/(topicId)

        Args:
            org_unit_id (int): Org unit ID.
            topic_id (str): Topic id.

        Returns:
            Return. This action returns a JSON array of ContentObject data blocks of type Topic.
        """

        if not org_unit_id:
            return self._client.return_error_state(f'Org ID ({org_unit_id}) is required')

        if not topic_id:
            return self._client.return_error_state(f'Topic ID ({topic_id}) is required')

        return self._client._do_get(f"{self._client.le_url}{org_unit_id}/content/topics/{topic_id}")

    # get the html
    def get_course_topic_content_file(self, org_unit_id: int, topic_id: int) -> Response:
        """Retrieve the content topic file for a content topic.

        https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-topics-(topicId)-file
        GET /d2l/api/le/(version)/(orgUnitId)/content/topics/(topicId)/file

        Args:
        org_unit_id (int): Org unit ID.
        topic_id (str): Topic id.

        Returns:
        Return. This action retrieves the underlying file for a file content topic.
        """

        # should always return topic id and orgid.
        return self._client._do_get(f"{self._client.le_url}{org_unit_id}/content/topics/{topic_id}/file")

    # update html file here
    def update_course_topic_file_html(self, org_unit_id: int, topic_id: int, topicDataHtml: str, filename: str) -> Response:
        """Replace the content topic file for a content topic.

        https://docs.valence.desire2learn.com/res/content.html#put--d2l-api-le-(version)-(orgUnitId)-content-topics-(topicId)-file
        PUT /d2l/api/le/(version)/(orgUnitId)/content/topics/(topicId)/file

        Args:
        org_unit_id (int): Org unit ID.
        topic_id (str): Topic id.
        topicDataHtml (str): request html data

        Returns:
        Return. Replace the content topic file for a content topic.
        """

        filename = filename if filename is not None else 'upload.html'

        # Set the headers
        headers = {
            "Content-Type": "multipart/form-data; boundary=xxBOUNDARYxx",
            "Content-Length": str(len(topicDataHtml))
        }

        # Construct the request body
        boundary = "xxBOUNDARYxx"
        body = (
            f"--{boundary}",
            'Content-Type: text/html; charset=utf-8',
            f'Content-Disposition: form-data; name="file"; filename="{filename}"',
            "",
            topicDataHtml,
            f"--{boundary}--"
        )

        body = "\r\n".join(body)

        # return response
        return self._client._put(f"{self._client.le_url}{org_unit_id}/content/topics/{topic_id}/file", data=body.encode('utf-8'), headers=headers, stream=True)

    # TODO - move assessment to own class
    # get all course assessments
    def get_course_assessments(self, org_unit_id: int) -> Response:
        # GET /d2l/api/le/1.0/{orgUnitId}/dropbox/folders/

        # GET /d2l/api/le/(version)/(orgUnitId)/dropbox/folders/(folderId)/submissions/


        url = f"{self._client.lp_url}/{org_unit_id}/dropbox/folders/"

        print(url)

        return self._client._do_get(f"{self._client.le_url}{org_unit_id}/dropbox/folders/")

    # TODO - move assessment to own class
    # get folders submissions by folder id
    def get_assessments_submissions_by_id(self, org_unit_id: int, folder_id: int)  -> Response:

        # GET /d2l/api/le/(version)/(orgUnitId)/dropbox/folders/(folderId)/submissions/

        url = f"{self._client.lp_url}/{org_unit_id}/dropbox/folders/{folder_id}/submissions"

        print(url)

        return self._client._do_get(f"{self._client.le_url}{org_unit_id}/dropbox/folders/{folder_id}/submissions")
