# ruff: noqa: E402, I001
from functools import wraps

from .exceptions import TokenRequired

def token_required(func):
    @wraps(func)
    def client_helper(*args, **kwargs):
        client = args[0]
        token = client.get_token()
        if not token:
            return TokenRequired('Brightspace Token required. See "Getting OAuth token".', 499).get_response()
        return func(*args, **kwargs)

    return client_helper
