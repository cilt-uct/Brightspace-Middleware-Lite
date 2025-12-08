# ruff: noqa: E402, I001

from .response import Response

class Role:

    def __init__(self, client) -> None:
        """Working with roles in Brightspace

        Args:
            client (Client): Client.
        """
        self._client = client

    def get_roles(self, params: dict = None) -> Response:
        """Retrieve a list of all known user roles.

        https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-(orgUnitId)-roles-
        GET /d2l/api/lp/(version)/roles/
        Scopes: role:detail:read

        Args:
            params (dict, optional): Query. Defaults to None.

        Returns:
            Response:  This action returns a JSON array of Role data blocks containing the
                       properties of all user roles that the calling user context has permission to manage.
        """
        return self._client._do_get('{self._client.lp_url}/roles/', params=params)
