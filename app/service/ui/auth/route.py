import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException

from sqlalchemy.orm import Session

from .forms import LoginForm
from db.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("uvicorn")


# def query_user(credentials:str, Session = Depends(get_db)):

#     current_username_bytes = credentials.username.encode("utf8")
#     current_password_bytes = credentials.password.encode("utf8")

#     correct_username_bytes = None
#     correct_password_bytes = None

#     db_user = crud.get_user(db, eid=credentials.username)
#     if db_user:
#         correct_username_bytes = db_user.eid.encode("utf8")
#         correct_password_bytes = db_user.password.encode("utf8")

#     if not correct_username_bytes or not correct_password_bytes:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Basic"},
#         )

#     is_correct_username = secrets.compare_digest(
#         current_username_bytes, correct_username_bytes
#     )

#     is_correct_password = (Hasher.verify_password(current_password_bytes, correct_password_bytes))

#     if correct_password_bytes and not (is_correct_username and is_correct_password):
#         if db_user:
#             db_user.login_count = db_user.login_count + 1
#             db.session.commit()

#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Basic"},
#         )

#     if db_user:
#         db_user.last_login = datetime.now()
#         db_user.login_count = 0
#         db.commit()

#     return credentials.username

# @router.post("/login")
# def login(data: OAuth2PasswordRequestForm = Depends()):
#     email = data.username
#     password = data.password

#     user = query_user(email)
#     if not user:
#         # you can return any response or error of your choice
#         raise InvalidCredentialsException
#     elif password != user["password"]:
#         raise InvalidCredentialsException

#     return {"status": "Success"}

# @router.get("/login/")
# def login(request: Request):
#     return templates.TemplateResponse("system/login.html", {"request": request})

# @router.post("/login/")
# async def login(request: Request, db: Session = Depends(get_db)):
#     form = LoginForm(request)
#     await form.load_data()
#     if await form.is_valid():
#         try:
#             form.__dict__.update(msg="Login Successful :)")
#             response = templates.TemplateResponse("system/login.html", form.__dict__)
#             login_for_access_token(response=response, form_data=form, db=db)
#             return response
#         except HTTPException:
#             form.__dict__.update(msg="")
#             form.__dict__.get("errors").append("Incorrect Email or Password")
#             return templates.TemplateResponse("system/login.html", form.__dict__)
#     return templates.TemplateResponse("system/login.html", form.__dict__)

@router.get("/logout", response_class=HTMLResponse)
async def ui_logout(request: Request):
    logger.info(request.cookies)
    response = RedirectResponse(url=request.url_for("start"), status_code= 302)
    # response.set_cookie(response, "")
    return response
