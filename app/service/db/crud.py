import sys

from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, func
from datetime import datetime
from typing import Optional

from . import models
from . import schemas

sys.path.append('..')
from utils.hasher import Hasher
from schemas.datatables import DataTableRequest, DataTableResponse

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(username=user.username,
                          name=user.name,
                          created_on=datetime.now(),
                          last_login=None,
                          login_count=0,
                          password=Hasher.get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
