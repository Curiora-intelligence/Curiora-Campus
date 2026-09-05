from __future__ import annotations
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter,Request
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

campus_router=APIRouter(prefix="/campus",tags=["campus routes"])

@campus_router.get("/curio", response_class=HTMLResponse)
async def visual_intelligence(request: Request) -> HTMLResponse:
    """this function routes to visual_inteligence"""
    return templates.TemplateResponse(request, "pages/curio.html")


@campus_router.get("/research")
async def research_redirect() -> RedirectResponse:
    return RedirectResponse(url="/curio", status_code=307)
