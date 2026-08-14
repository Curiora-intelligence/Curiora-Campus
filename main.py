"""Curiora Campus application entry point.

The app intentionally keeps the campus workflows lightweight and keeps Curio
vision inference isolated behind ``app.services.vision``.  That means the web
application can start even when the optional local vision model is not yet
installed.
"""

from __future__ import annotations


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers.authentication import auth_router
from app.routers.campus import campus_router
from app.routers.curio import curio_router


app = FastAPI(title="saiganesh",version="1.0.0",docs_url=None,redoc_url=None,openapi_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(auth_router)
app.include_router(campus_router)
app.include_router(curio_router)

