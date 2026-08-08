from fastapi import APIRouter,Form,Depends
from fastapi.requests import Request
from fastapi.responses import RedirectResponse,HTMLResponse
from fastapi.templating import Jinja2Templates
template=Jinja2Templates(directory="template")
 
router=APIRouter()
@router.get("/",response_class=HTMLResponse)
def home(request:Request):
    return template.TemplateResponse(request,"home.html")

@router.get("/login-form",response_class=HTMLResponse)
def login_form(request:Request):
    return template.TemplateResponse(request,"login-form.html")

@router.post("/login",response_class=HTMLResponse)
def login(request:Request,userid:str=Form(...),password:str=Form(...),captcha:str=Form(...)):
    pass