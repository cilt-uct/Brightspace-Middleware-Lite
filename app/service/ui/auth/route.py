import logging

from datetime import datetime

from fastapi import Form
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException

from sqlalchemy.orm import Session

from .forms import LoginForm, RegisterForm
from .manager import manager

from auth.dependencies import admin_required, is_first_run, Hasher
from core.settings import AppSettings, settings
from db.database import get_db
from db import crud, models

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("uvicorn")

@router.get("/register", response_class=HTMLResponse)
@router.post("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db), admin_user: models.User = Depends(admin_required)):
    form = RegisterForm(request)
    await form.load_data()

    if request.method == "POST":
        if await form.is_valid():
            # Check if username already exists
            existing_user = crud.get_user(db, username=form.username)
            if existing_user:
                form.errors.append("Username already exists")
            else:
                # Create new user
                new_user = models.User(
                    username=form.username,
                    password=Hasher.get_password_hash(form.password),
                    name=form.name,
                    is_active=True,
                    is_admin=False,  # by default regular user
                    created_on=datetime.utcnow()
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                # Redirect to login after successful registration
                return RedirectResponse(url=f"{settings.app_prefix}/login", status_code=302)

    return templates.TemplateResponse("system/register.html", {"request": request, "form": form})

@router.get("/setup", response_class=HTMLResponse)
@router.post("/setup", response_class=HTMLResponse)
async def first_run(request: Request, db: Session = Depends(get_db), first_run_flag: bool = Depends(is_first_run)):

    # If there are already users, redirect to login
    if not first_run_flag:
        return RedirectResponse(url=f"{settings.app_prefix}/login", status_code=302)

    form = RegisterForm(request)
    await form.load_data()

    if request.method == "POST":
        if await form.is_valid():
            # Create the first user as admin
            new_user = models.User(
                username=form.username,
                password=Hasher.get_password_hash(form.password),
                name=form.name,
                is_active=True,
                is_admin=True,   # first user is admin
                created_on=datetime.utcnow()
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # Redirect to login after creation
            return RedirectResponse(url=f"{settings.app_prefix}/login", status_code=302)

    # GET or failed POST
    return templates.TemplateResponse("system/setup.html", {"request": request, "form": form})

@router.get("/login", response_class=HTMLResponse)
@router.post("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):

    if db.query(models.User).count() == 0:
        logger.info("No users exist, redirecting to setup")
        return RedirectResponse(url=f"{settings.app_prefix}/setup", status_code=302)

    form = LoginForm(request)
    await form.load_data()

    if request.method == "POST":
        if await form.is_valid():
            # Try to authenticate user
            db_user = crud.get_user(db, username=form.username)
            logger.info(f'Attempt login for user: {form.username} {form.password}')
            if not db_user or not Hasher.verify_password(form.password.encode(), db_user.password.encode()):
                form.errors.append("Incorrect username or password")
            else:
                # Successful login, create token & redirect
                logger.info(f'Login successful for user: {db_user.username}')
                access_token = manager.create_access_token(data={"sub": db_user.username})
                response = RedirectResponse(url=f"{settings.app_prefix}/", status_code=302)
                manager.set_cookie(response, access_token)
                return response

    # GET request or failed POST
    return templates.TemplateResponse("system/login.html", {"request": request, "form": form})


@router.get("/logout", response_class=HTMLResponse)
async def ui_logout(request: Request):
    logger.info(request.cookies)
    response = RedirectResponse(url=request.url_for("start"), status_code= 302)
    # response.set_cookie(response, "")
    return response
