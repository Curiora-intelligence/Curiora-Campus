from fastapi import APIRouter,Form,Depends
from fastapi.requests import Request
from fastapi.responses import RedirectResponse,HTMLResponse
from main import templates
import secrets,string

auth_router=APIRouter()
@auth_router.get("/",response_class=HTMLResponse)
def home(request:Request):
    return templates.TemplateResponse(request,"home.html")

@auth_router.get("/login-form",response_class=HTMLResponse)
def login_form(request:Request):
    return templates.TemplateResponse(request,"login-form.html")

@auth_router.post("/login",response_class=HTMLResponse)
def login(request:Request,userid:str=Form(...),password:str=Form(...),captcha:str=Form(...)):
    pass

@auth_router.get("/about")
async def about_redirect() -> RedirectResponse:
    return RedirectResponse(url="/#about", status_code=307)


@auth_router.get("/student-login", response_class=HTMLResponse)
async def student_login_page(request: Request) -> HTMLResponse:
    captcha_text = "".join(
    secrets.SystemRandom().choices(string.ascii_letters + string.digits, k=6))
    return templates.TemplateResponse(request, "pages/login-form.html", captcha=captcha_text)


@auth_router.post("/student-portal", response_class=HTMLResponse)
async def student_portal(request: Request,user_captcha: str = Form(""),real_captcha: str = Form("")) -> HTMLResponse:
    if user_captcha.strip() != real_captcha:
        return templates.TemplateResponse(request,"pages/login-form.html",captcha=real_captcha,
                                          error="That captcha did not match. Please try again.")
    
    return templates.TemplateResponse(request,"pages/student_portal.html")