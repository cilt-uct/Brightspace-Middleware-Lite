from enum import Enum
from flask import current_app
from flask_login import UserMixin

from datetime import datetime
from dateutil.relativedelta import relativedelta

from project.app import alchemy_db as db
from project.app import bcrypt

class User(UserMixin, db.Model):

    __tablename__ = "system_user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    eid = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    created_on = db.Column(db.DateTime, nullable=False)
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)

    def __init__(self, name, eid, password, is_admin=False, is_active=True):
        self.name = name
        self.eid = eid
        self.password = bcrypt.generate_password_hash(password)
        self.created_on = datetime.now()
        self.is_admin = is_admin
        self.is_active = is_active

    def __repr__(self):
        return f"<EID {self.eid}>"
