from flask import current_app
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime, timedelta

from project.app import alchemy_db as db
from project.utils import Utils

TOKEN_VALID_CHECK = timedelta(minutes=30)
TOKEN_SOON_CHECK = timedelta(hours=3)

class SharedToken(db.Model):
    __tablename__ = "auth_token"

    client_id = db.Column(db.String(255), primary_key=True)
    token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)

    expires = db.Column(db.Integer)
    expires_at = db.Column(db.DateTime)
    scope = db.Column(db.Text)

    modified_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, client_id, token, refresh_token, expires, expires_at, created_at, scope):

        self.client_id = client_id
        self.token = token
        self.refresh_token = refresh_token
        self.expires = expires
        self.expires_at = datetime.fromtimestamp(expires_at)
        self.created_at = datetime.fromtimestamp(created_at)
        self.modified_at = datetime.now()

    def __repr__(self):
        return f'<SharedToken {self.expires_at}>'

    @property
    def is_expired(self) -> bool:
        return self.expires_at < datetime.now()

    @property
    def active(self) -> bool:
        return not self.is_expired

    @property
    def is_token_valid(self) -> bool:
        return self.expires > (datetime.now() - TOKEN_VALID_CHECK).timestamp()

    @property
    def countdown(self) -> int:
        return str(self.expires - datetime.now().timestamp())

    @property
    def soon(self) -> bool:
        return self.expires < (datetime.now() - TOKEN_SOON_CHECK).timestamp()

    def to_dict(self, exclude=["client_id", "token", "refresh_token", "scope"]):

        data = {
            "client_id": self.client_id,
            "token": self.token,
            "refresh_token": self.refresh_token,
            "expires": self.expires,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "active": self.active,
            "is_expired": self.is_expired,
            "is_token_valid": self.is_token_valid,
            "countdown": self.countdown,
            "soon": self.soon,
        }
        if exclude:
            for key in exclude:
                data.pop(key, None)
        return data

def get_shared_token(client_id):
    return SharedToken.query.filter_by(client_id=client_id).first()

def set_shared_token(client_id, token, refresh_token, expires, expires_at, created_at, scope):
    print(f'Saved token to database: {client_id}, expires at: {datetime.fromtimestamp(expires_at)}')

    existing = SharedToken.query.filter_by(client_id=client_id).first()
    if existing:
        existing.token = token
        existing.refresh_token = refresh_token
        existing.expires = expires
        existing.expires_at = datetime.fromtimestamp(expires_at)
        existing.created_at = datetime.fromtimestamp(created_at)
        existing.scope = scope
        existing.modified_at = datetime.now()
        db.session.commit()
        return existing
    else:
        new_token = SharedToken(client_id=client_id,
                                token=token,
                                refresh_token=refresh_token,
                                expires=expires,
                                expires_at=expires_at,
                                created_at=created_at,
                                scope=scope)
        db.session.add(new_token)
        db.session.commit()
        return new_token

def get_token_details(access_token: str) -> list:
    """Convert JWT access token into headet, payload, signature

    Args:
        _str (str): JWT access token

    Returns:
        list: (header, payload, signature)
    """
    (header, payload, signature) = access_token.split('.')
    header = Utils.get_json_from_base64(header)
    payload = Utils.get_json_from_base64(payload)

    return (header, payload, signature)
