import logging

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from functools import lru_cache
from typing import Annotated, List, Union

from auth.dependencies import authenticate_user
from core.settings import AppSettings, settings

@lru_cache
def get_app_settings():
    return AppSettings()

from ui.auth.route import router as auth_router

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("uvicorn")

router.include_router(auth_router, prefix="", tags=["auth-ui"])

@router.get("/", response_class=HTMLResponse)
async def start(
    request: Request,
    settings: Annotated[AppSettings, Depends(get_app_settings)],
    username: Annotated[Union[str, RedirectResponse], Depends(authenticate_user)]
):
    logger.info(f'Accessing home page as user: {username}')

    # If authenticate_user returned a RedirectResponse, return it directly
    if isinstance(username, RedirectResponse):
        return username

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"settings": settings, "username": username}
    )
