"""
This file contains FastAPI app.
"""
import httpx
import logging

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_login import LoginManager

from contextlib import asynccontextmanager

# Core and Database
from core.config import config
from db import database, models

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()

app = FastAPI(lifespan=lifespan,
              title=config.title,
              description=config.description)

manager = LoginManager(config.secret, "/login")

models.Base.metadata.create_all(bind=database.engine)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

# Routes ########################################
from api import base as api_base
from ui import base as ui_base

app.include_router(api_base.router, prefix="/api")
app.include_router(ui_base.router)

if __name__ == "__main__":
    app.run()
