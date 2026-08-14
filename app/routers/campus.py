from fastapi.templating import Jinja2Templates
from fastapi import APIRouter,Request
from fastapi.responses import HTMLResponse,RedirectResponse
from main import templates

campus_router=APIRouter(prefix="/campus",tags="campus routes")

@campus_router.get("/visual-intelligence", response_class=HTMLResponse)
async def visual_intelligence(request: Request) -> HTMLResponse:
    """this function routes to visual_inteligence"""
    return templates.TemplateResponse(request, "pages/visual_intelligence.html")


@campus_router.get("/research")
async def research_redirect() -> RedirectResponse:
    return RedirectResponse(url="/visual-intelligence", status_code=307)


