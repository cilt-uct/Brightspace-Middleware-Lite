import secrets

from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import Annotated

from db.database import get_db
from db import crud, database, models, schemas
from utils.hasher import Hasher

security = HTTPBasic()

def authenticate_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    db: Session = Depends(get_db)
):

    current_username_bytes = credentials.username.encode("utf8")
    current_password_bytes = credentials.password.encode("utf8")

    correct_username_bytes = None
    correct_password_bytes = None

    db_user = crud.get_user(db, eid=credentials.username)
    if db_user:
        correct_username_bytes = db_user.eid.encode("utf8")
        correct_password_bytes = db_user.password.encode("utf8")

    if not correct_username_bytes or not correct_password_bytes:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )

    is_correct_password = (Hasher.verify_password(current_password_bytes, correct_password_bytes))

    if correct_password_bytes and not (is_correct_username and is_correct_password):
        if db_user:
            db_user.login_count = db_user.login_count + 1
            db.session.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    if db_user:
        db_user.last_login = datetime.now()
        db_user.login_count = 0
        db.commit()

    return credentials.username
