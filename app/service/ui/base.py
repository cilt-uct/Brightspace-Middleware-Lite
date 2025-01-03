import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from functools import lru_cache
from typing import Annotated, List

from auth.dependencies import authenticate_user
from core.config import Config, config

@lru_cache
def get_config():
    return Config()

from ui.auth.route import router as auth_router

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("uvicorn")

router.include_router(auth_router, prefix="", tags=["auth-ui"])

@router.get("/", response_class=HTMLResponse)
async def start(request: Request,
                settings: Annotated[Config, Depends(get_config)],
                username: Annotated[str, Depends(authenticate_user)]):
    logger.info(username)
    logger.info(request.cookies)
    return templates.TemplateResponse(
        request=request, name="index.html", context={ "settings" : settings }
    )


# @router.post("/", response_model=UserDB, status_code=201)
# def register_user(
#     user: UserIn, commons: CommonParameters = Depends(common_parameters)
# ) -> UserDB:
#     user_db = UserDB(**user.dict())
#     commons.user_store.add_user(user_db)

#     return user_db
