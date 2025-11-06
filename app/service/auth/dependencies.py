# auth/dependencies.py
import secrets
import bcrypt

from datetime import datetime

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
from fastapi_login.exceptions import InvalidCredentialsException

from sqlalchemy.orm import Session
from typing import Annotated, Union

from ui.auth.manager import manager
from db.database import get_db
from db import crud, models

from core.settings import AppSettings, settings, logger

security = HTTPBasic(auto_error=False)  # <- this prevents automatic 401

async def authenticate_user(request: Request, credentials: Annotated[HTTPBasicCredentials, Depends(security)] = None, db: Session = Depends(get_db)) -> Union[str, RedirectResponse]:

    logger.info(f"Authenticating user : {db.query(models.User).count()} users in DB")

    # First-run
    if db.query(models.User).count() == 0:
        return RedirectResponse(url=f"{settings.app_prefix}/setup", status_code=302)

    # Try cookie-based login
    logger.info("Trying cookie-based authentication")
    try:
        username = await manager.get_current_user(request)
        logger.info(f'Cookie-based login attempt for user: {username}')

        db_user = crud.get_user(db, username=username)
        if db_user and db_user.is_active:
            return db_user.username

    except Exception as e:
        logger.info(e)
        pass

    # Fallback to HTTPBasic
    logger.info(f"credentials {credentials}")
    if credentials:
        db_user = crud.get_user(db, username=credentials.username)
        if not db_user or not Hasher.verify_password(credentials.password.encode(), db_user.password.encode()):
            return RedirectResponse(url=f"{settings.app_prefix}/login", status_code=302)
        # successful HTTPBasic login > issue token
        access_token = manager.create_access_token(data={"sub": db_user.username})
        response = RedirectResponse(url=f"{settings.app_prefix}/", status_code=302)
        manager.set_cookie(response, access_token)
        return response

    # no token, no credentials
    return RedirectResponse(url=f"{settings.app_prefix}/login", status_code=302)


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User | None:
    try:
        username = await manager.get_current_user(request)
    except InvalidCredentialsException:
        return None

    user = crud.get_user(db, username=username)
    if not user or not user.is_active:
        return None
    return user

# Reuse your authenticate_user dependency to get the username
async def admin_required(
    username: Annotated[str, Depends(authenticate_user)],
    db: Session = Depends(get_db)
) -> models.User:
    user = crud.get_user(db, username=username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if not (user.is_active and user.is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Admins only")

    return user

async def is_first_run(db: Session = Depends(get_db)) -> bool:
    """Return True if no users exist yet"""
    return db.query(models.User).count() == 0

class Hasher():
    # Hash a password using bcrypt
    @staticmethod
    def get_password_hash(password):
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
        return hashed_password

    # Check if the provided password matches the stored password (hashed)
    @staticmethod
    def verify_password(plain_password, hashed_password):
        if not plain_password or not hashed_password:
            return False

        if isinstance(plain_password, (bytes, bytearray)):
            password_byte_enc = plain_password
        else:
            password_byte_enc = plain_password.encode('utf-8')

        if isinstance(hashed_password, (bytes, bytearray)):
            hashed_password_byte_enc = hashed_password
        else:
            hashed_password_byte_enc = hashed_password.encode('utf-8')

        return bcrypt.checkpw(password = password_byte_enc , hashed_password = hashed_password_byte_enc)
