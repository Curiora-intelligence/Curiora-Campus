"""Curiora Campus application entry point.

The app intentionally keeps the campus workflows lightweight and keeps Curio
vision inference isolated behind ``app.services.vision``.  That means the web
application can start even when the optional local vision model is not yet
installed.
"""

from __future__ import annotations

import secrets
import string
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers.curio import curio_router


app = FastAPI(title="saiganesh",version="1.0.0",docs_url=None,redoc_url=None,openapi_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(curio_router)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request,"pages/home.html")


@app.get("/visual-intelligence", response_class=HTMLResponse)
async def visual_intelligence(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/visual_intelligence.html")


@app.get("/research")
async def research_redirect() -> RedirectResponse:
    return RedirectResponse(url="/visual-intelligence", status_code=307)


@app.get("/about")
async def about_redirect() -> RedirectResponse:
    return RedirectResponse(url="/#about", status_code=307)


@app.get("/student-login", response_class=HTMLResponse)
async def student_login_page(request: Request) -> HTMLResponse:
    captcha_text = "".join(
        secrets.SystemRandom().choices(string.ascii_letters + string.digits, k=6)
    )
    return templates.TemplateResponse(request, "pages/login-form.html", captcha=captcha_text)


@app.post("/student-portal", response_class=HTMLResponse)
async def student_portal(
    request: Request,
    user_captcha: str = Form(""),
    real_captcha: str = Form(""),
) -> HTMLResponse:
    if user_captcha.strip() != real_captcha:
        return templates.TemplateResponse(
            request,
            "pages/login-form.html",
            captcha=real_captcha,
            error="That captcha did not match. Please try again.",
        )
    return templates.TemplateResponse(request, "pages/student_portal.html")

