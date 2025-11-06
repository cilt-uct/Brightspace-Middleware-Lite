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
from core.settings import settings
from db import database, models

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()

app = FastAPI(lifespan=lifespan,
              title=settings.title,
              description=settings.description)

models.Base.metadata.create_all(bind=database.engine)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes ########################################
from api import base as api_base
from ui import base as ui_base

app.include_router(api_base.router, prefix="/api")
app.include_router(ui_base.router)

if __name__ == "__main__":
    app.run()
