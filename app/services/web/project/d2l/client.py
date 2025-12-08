import os, sys, json
import base64
import time
import requests
from requests.exceptions import ReadTimeout, ConnectTimeout, RequestException

from typing import Optional
from urllib.parse import urlencode
from requests_oauthlib import OAuth2Session
from datetime import datetime, timedelta

from functools import wraps

current = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current)

from . import exceptions
from .response import Response
from .decorators import token_required
from .exceptions import BaseError, TokenRequired

from .oauth import SharedToken, get_shared_token, set_shared_token, get_token_details

from .content import Content
from .courses import Course
from .roles import Role
from .users import User

from ..constants import DEFAULT_LP_VERSION, DEFAULT_LE_VERSION, DEFAULT_LR_VERSION, \
                        DEFAULT_EP_VERSION, DEFAULT_BFP_VERSION, DEFAULT_BAS_VERSION

class Client(object):

    def __init__(
        self,
        mysql, # SQL Connection object
        config: dict,
        requests_hooks: dict = None,
        token = None,
        retries: int = 3, backoff_factor: float = 0.5
    ) -> None:
        """Instantiates library.

        Args:
            mysql: mysql connection object
            config (dict): Dictionary contains the configuration paramaters to connect to Brightspace
            requests_hooks (dict, optional): Requests library event hooks. Defaults to None.

        Raises:
            Exception: config is not a dict.
            Exception: requests_hooks is not a dict.
        """
        if config and not isinstance(config, dict):
            raise Exception('config must be a dict - application is not configured.')

        print('init client')
        self.client_id = config['CLIENT_ID']
        self.client_secret = config['CLIENT_SECRET']
        self.base_url = '{}d2l/api/'.format(config['BASE_URL'])
        self.redirect_uri = config['REDIRECT_URI']

        self.auth_base_url = config['AUTHORIZATION_BASE_URL']
        self.token_url = config['TOKEN_URL']
        self.scope = config['SCOPE']

        # storage for token
        self.token = token

        # set database link
        self.mysql = mysql

        # TODO: retrieve values from database
        # The initial versions are set with the defaults - need to run the refresh versions function
        self.lp_version  = f'{DEFAULT_LP_VERSION}'
        self.le_version  = f'{DEFAULT_LE_VERSION}'
        self.lr_version  = f'{DEFAULT_LR_VERSION}'
        self.ep_version  = f'{DEFAULT_EP_VERSION}'
        self.bfp_version = f'{DEFAULT_BFP_VERSION}'
        self.bas_version = f'{DEFAULT_BAS_VERSION}'

        self.lp_url   = f'{self.base_url}lp/{self.lp_version}/'
        self.le_url   = f'{self.base_url}le/{self.le_version}/'
        self.lr_url   = f'{self.base_url}lr/{self.lr_version}/'
        self.ep_url   = f'{self.base_url}ep/{self.ep_version}/'
        self.bfp_url  = f'{self.base_url}bfp/{self.bfp_version}/'
        self.bas_url  = f'{self.base_url}bas/{self.bas_version}/'

        # Init the Classes
        self.content = Content(self)
        self.course = Course(self)
        self.roles = Role(self)
        self.user = User(self)

        # Request object
        self.retries = retries
        self.backoff_factor = backoff_factor

        # check if the optional requests_hooks dictionary was used
        if requests_hooks and not isinstance(requests_hooks, dict):
            raise Exception(
                'requests_hooks must be a dict. e.g. {"response": func}. http://docs.python-requests.org/en/master/user/advanced/#event-hooks'
            )
        self.requests_hooks = requests_hooks

    def authorization_url(self) -> dict:
        """Generates an Authorization URL.

        The first step to getting an access token for many OpenID Connect (OIDC) and OAuth 2.0 flows is to redirect the
        user to the identity platform /authorize endpoint.

        Args:
            redirect_uri (str): The redirect_uri of your app, where authentication responses can be sent and received by
            your app. It must exactly match one of the redirect_uris you registered in the app registration portal.
            auth_bare_uri (str): The base authentication url to use in the OAuthSession

        Returns:
            dict:
                authorization_url : Url for OAuth 2.0.
                state             : State is used to prevent CSRF, keep this for later.
        """
        my_auth = OAuth2Session(self.client_id, redirect_uri = self.redirect_uri, scope = self.scope)

        authorization_url, state = my_auth.authorization_url(self.auth_base_url)

        return {'authorization_url': authorization_url, 'state': state}

    def exchange_code(self, redirect_uri: str) -> bool:
        """Exchanges an oauth code for an user token.

        Your app uses the authorization code received in the previous step to request an access token by sending a POST
        request to the /token endpoint.

        Args:
            redirect_uri (str): The redirect_uri of your app, where authentication responses can be sent and received by
            your app.  It must exactly match one of the redirect_uris you registered in the app registration portal.
            code (str): The authorization_code that you acquired in the first leg of the flow.

        Returns:
            bool: True if success / false otherwise
        """

        my_auth = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri)
        try:
            token = my_auth.fetch_token(
                self.token_url,
                client_secret=self.client_secret,
                authorization_response=redirect_uri.replace('http://', 'https://')
            )
        except Exception as e:
            print(f"Error exchanging code for token: {e}")
            return False

        # Check for required keys
        if not all(k in token for k in ('access_token', 'refresh_token', 'expires_at')):
            print("Token response missing required fields.")
            return False

        try:
            print(token)
            self.set_token(token['access_token'], token['refresh_token'], token['expires_at'])
        except Exception as e:
            print(f"Error setting token: {e}")
            return False

        return True

    def set_token(self, token: str, refresh_token: str, expire_at) -> None:
        """Sets the User token for its use in this library.

        Args:
            token (str): Access token data (JWT)
            refresh_token (str): The refresh_token that can be traded for a new access token
            expire_at : either a integer or a datetime object of when the access token expires
        """
        if isinstance(expire_at, datetime):
            dt_expire_at = expire_at
            int_expire_at = time.mktime(expire_at.timetuple())
        else:
            dt_expire_at = datetime.fromtimestamp(expire_at)
            int_expire_at = expire_at

        self.token = self.update_db_token(token, refresh_token, int_expire_at) # Store in Database

    def _refresh_token(self, refresh_token: str) -> None:
        """Exchanges a refresh token for an user token.

        Access tokens are short lived, and you must refresh them after they expire to continue accessing resources.
        You can do so by submitting another POST request to the /token endpoint, this time providing the refresh_token
        instead of the code.

        Args:
            refresh_token (str): An OAuth 2.0 refresh token. Your app can use this token acquire additional access tokens
            after the current access token expires. Refresh tokens are long-lived, and can be used to retain access
            to resources for extended periods of time.
        """

        url = "https://auth.brightspace.com/core/connect/token"

        payload = {
            'grant_type' : 'refresh_token',
            'refresh_token' : refresh_token,
            'client_id' : self.client_id,
            'client_secret' :  self.client_secret,
            'scope' : self.scope
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            refreshed = self._parse(response)
        except requests.RequestException as e:
            print(f"HTTP error during token refresh: {e}")
            return False
        except Exception as e:
            print(f"Error parsing token refresh response: {e}")
            return False

        # Validate refreshed token structure
        if not all(k in refreshed for k in ('access_token', 'refresh_token')):
            print("Refreshed token response missing required fields.")
            return False

        try:
            header, payload, signature = get_token_details(refreshed['access_token'])
            if 'exp' not in payload:
                print("Token payload missing 'exp' field.")
                return False

            self.set_token(refreshed['access_token'], refreshed['refresh_token'], payload['exp'])
        except Exception as e:
            print(f"Error setting refreshed token: {e}")
            return False

        return True

    def do_refresh(self, force:bool = False) -> dict:
        """Call the refresh function with the appropriate values

        Returns:
            dict: status, data
        """

        if self.token is None:
            self.token = get_shared_token(self.client_id)

        if force or self.token.soon or self.token.is_expired:
            self._refresh_token(self.token.refresh_token)

        return self.token

    def get_token(self) -> dict:
        """Get the current token dict

        Returns:
            dict: access_token, expires
        """

        self.token = get_shared_token(self.client_id)

        if self.token.soon or self.token.is_expired:
            self._refresh_token(self.token.refresh_token)

        return self.token

    def is_token_valid(self) -> bool:
        """Check to see if the current access token is still valid

        Returns:
            bool: validity of access token
        """
        self.token = get_shared_token(self.client_id)
        if self.token is None:
            return False

        return self.token.is_token_valid

    def update_db_token(self, access_token: str, refresh_token: str, expires_in: int) -> bool:
        """Saves the token details to the database

        Args:
            access_token (str): Access token string
            refresh_token (str): Refresh token string
            expires_in (int): When the access token expires in unix / epoch time

        Returns:
            bool: successfully saved to database
        """

        try:
            (header, payload, signature) = get_token_details(access_token)

            return set_shared_token(client_id=self.client_id,
                             token=access_token,
                             refresh_token=refresh_token,
                             expires=expires_in,
                             expires_at=payload['exp'],
                             created_at=payload['nbf'],
                             scope=payload['scope'])

        except Exception as e:
            print(f'ERR update_db_token: {e}')
            return None

    def _do_get(self, url, **kwargs) -> Response:
        kwargs.setdefault("timeout", 10)
        return self._request("GET", url, **kwargs)

    def _post(self, url, **kwargs):
        kwargs.setdefault("timeout", 60)
        return self._request("POST", url, **kwargs)

    def _put(self, url, **kwargs):
        kwargs.setdefault("timeout", 30)
        return self._request("PUT", url, **kwargs)

    def _patch(self, url, **kwargs):
        kwargs.setdefault("timeout", 30)
        return self._request("PATCH", url, **kwargs)

    def _delete(self, url, **kwargs):
        kwargs.setdefault("timeout", 20)
        return self._request("DELETE", url, **kwargs)

    def get_all_version(self) -> dict:
        """Get all the versions

        Returns:
            dict: of versions

        """
        return self._do_get(f'{self.base_url}versions/')

    def get_lp_version(self) -> dict:
        """Get the current lp version

        Returns:
            dict: of versions

        """
        return self._do_get(f'{self.base_url}lp/versions/')

    def get_le_version(self) -> dict:
        """Get the current le version

        Returns:
            dict: of versions

        """
        return self._do_get(f'{self.base_url}le/versions/')

    def return_success_state(self, msg, code:int = 200):
        return {'status': 'success', 'data': msg}

    def return_error_state(self, msg, code:int = 400):
        return {'status': 'ERR', 'data': msg}

    @token_required
    def _request(self, method, url, headers=None, **kwargs) -> Response:
        _headers = {
            "Authorization": f'Bearer {self.token.token}'
        }

        if headers:
            _headers.update(headers)
        else:
            _headers["Accept"] = "application/json"
            if "Content-Type" not in _headers:
                _headers["Content-Type"] = "application/json"

        if self.requests_hooks:
            kwargs.update({"hooks": self.requests_hooks})

        for attempt in range(self.retries):
            try:
                data = self._parse(requests.request(method, url, headers=_headers, **kwargs))
                return {'status': 'success', 'data': data}

            except (ConnectTimeout, ReadTimeout) as e:
                if attempt < self.retries - 1:
                    sleep_time = self.backoff_factor * (2 ** attempt)
                    # print(f"[Retry {attempt+1}/{self.retries}] Timeout occurred: {e}. Retrying in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    print(f"_request 384: {e.__class__.__name__} {str(e)}")
                    return self.return_error_state(f'{e.__class__.__name__} {str(e)}')

            except Exception as e:
                print(f"_request 388: {attempt} {e.__class__.__name__} {str(e)} {issubclass(e.__class__, BaseError)}")
                if issubclass(e.__class__, BaseError):  # assuming your BaseError type
                    return e.get_response()
                else:
                    print("Oops!", e.__class__, "occurred.")
                    print(e)
                    return self.return_error_state(str(e))

    @token_required
    def _raw(self, method, url, headers=None, **kwargs):
        _headers = {
            "Authorization": f'Bearer {self.token.token}'
        }

        if headers:
            _headers.update(headers)
        else:
            _headers["Accept"] = "application/json"

            if "Content-Type" not in _headers:
                _headers["Content-Type"] = "application/json"

        if self.requests_hooks:
            kwargs.update({"hooks": self.requests_hooks})

        for attempt in range(self.retries):
            try:
                return requests.request(method, url, headers=_headers, **kwargs)

            except (ConnectTimeout, ReadTimeout) as e:
                if attempt < self.retries - 1:
                    sleep_time = self.backoff_factor * (2 ** attempt)
                    # print(f"[Retry {attempt+1}/{self.retries}] Timeout occurred: {e}. Retrying in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    return self.return_error_state(f'{e.__class__.__name__} {str(e)}')

            except Exception as e:
                if issubclass(e.__class__, BaseError):  # assuming your BaseError type
                    return e.get_response()
                else:
                    print("Oops!", e.__class__, "occurred.")
                    print(e)
                    return self.return_error_state(str(e))

    def _parse(self, response) -> Response:
        status_code = response.status_code
        r = Response(original=response)
        if status_code in (200, 201, 202, 204, 206):
            return r.data
        elif status_code == 400:
            raise exceptions.BadRequest(r.data, status_code)
        elif status_code == 401:
            raise exceptions.Unauthorized(r.data, status_code)
        elif status_code == 403:
            raise exceptions.Forbidden(r.data, status_code)
        elif status_code == 404:
            raise exceptions.NotFound(r.data, status_code)
        elif status_code == 405:
            raise exceptions.MethodNotAllowed(r.data, status_code)
        elif status_code == 406:
            raise exceptions.NotAcceptable(r.data, status_code)
        elif status_code == 409:
            raise exceptions.Conflict(r.data, status_code)
        elif status_code == 410:
            raise exceptions.Gone(r.data, status_code)
        elif status_code == 411:
            raise exceptions.LengthRequired(r.data, status_code)
        elif status_code == 412:
            raise exceptions.PreconditionFailed(r.data, status_code)
        elif status_code == 413:
            raise exceptions.RequestEntityTooLarge(r.data, status_code)
        elif status_code == 415:
            raise exceptions.UnsupportedMediaType(r.data, status_code)
        elif status_code == 416:
            raise exceptions.RequestedRangeNotSatisfiable(r.data, status_code)
        elif status_code == 422:
            raise exceptions.UnprocessableEntity(r.data, status_code)
        elif status_code == 429:
            raise exceptions.TooManyRequests(r.data, status_code)
        elif status_code == 499:
            raise exceptions.TokenRequired(r.data, status_code)
        elif status_code == 500:
            raise exceptions.InternalServerError(r.data, status_code)
        elif status_code == 501:
            raise exceptions.NotImplemented(r.data, status_code)
        elif status_code == 503:
            raise exceptions.ServiceUnavailable(r.data, status_code)
        elif status_code == 504:
            raise exceptions.GatewayTimeout(r.data, status_code)
        elif status_code == 507:
            raise exceptions.InsufficientStorage(r.data, status_code)
        elif status_code == 509:
            raise exceptions.BandwidthLimitExceeded(r.data, status_code)
        else:
            if r["error"]["innerError"]["code"] == "lockMismatch":
                # File is currently locked due to being open in the web browser
                # while attempting to reupload a new version to the drive.
                # Thus temporarily unavailable.
                raise exceptions.ServiceUnavailable(r.data)
            raise exceptions.UnknownError(r.data)
