# ruff: noqa: E402, I001, N818
# Ignore import order and naming conventions for exception classes
import json

from werkzeug.wrappers import Response

class BaseError(Exception):

    def __init__(self, data, status_code):
        # Decode bytes
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8')
            except Exception:
                data = str(data)

        # Try parse JSON if it's a string
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                data = parsed
            except json.JSONDecodeError:
                pass  # leave as plain string

        # If JSON has "Errors", unwrap it
        if isinstance(data, dict) and 'Errors' in data and len(data['Errors']) > 0:
            data = data['Errors'][0].get('Message', data)

        self.data = data
        self.status_code = status_code
        super().__init__(str(self.data))

    def __str__(self) -> str:
        return json.dumps(self.get_response())

    def get_response(self) -> Response:
        details = self.data
        if isinstance(self.data, dict) and 'details' in self.data:
            details = self.data['details']

        return {
            'status': 'ERR',
            'data': details,
            'code': self.status_code,
        }

class UnknownError(BaseError):
    pass


class TokenRequired(BaseError):
    pass


class BadRequest(BaseError):
    pass


class Unauthorized(BaseError):
    pass


class Forbidden(BaseError):
    pass


class NotFound(BaseError):
    pass


class MethodNotAllowed(BaseError):
    pass


class NotAcceptable(BaseError):
    pass


class Conflict(BaseError):
    pass


class Gone(BaseError):
    pass


class LengthRequired(BaseError):
    pass


class PreconditionFailed(BaseError):
    pass


class RequestEntityTooLarge(BaseError):
    pass


class UnsupportedMediaType(BaseError):
    pass


class RequestedRangeNotSatisfiable(BaseError):
    pass


class UnprocessableEntity(BaseError):
    pass


class TooManyRequests(BaseError):
    pass


class InternalServerError(BaseError):
    pass


class NotImplemented(BaseError):
    pass


class ServiceUnavailable(BaseError):
    pass


class GatewayTimeout(BaseError):
    pass


class InsufficientStorage(BaseError):
    pass


class BandwidthLimitExceeded(BaseError):
    pass
