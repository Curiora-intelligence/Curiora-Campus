from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os, string, secrets
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt,pickle

app = FastAPI(title="saiganesh",version="0.139.0",docs_url=None,redoc_url=None,openapi_url=None)

# Ensure folders exist
for folder in ["static", "templates"]:
    os.makedirs(folder, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
try:
    with open("predict.pkl",'rb') as file:
        model=pickle.load(file)
except:
    raise FileNotFoundError("run the ML model.py script to use ML model")

def predict_days(cat):
    mapping = {"Academic": 0, "Hostel": 1, "Mess": 2, "Infrastructure": 3}
    prediction = model.predict([[mapping.get(cat, 0)]])
    return round(float(prediction[0]), 1)

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request,"pages/home.html")


@app.get("/student-login", response_class=HTMLResponse)
async def student_login_page(request: Request):
    captcha_text = ''.join(secrets.SystemRandom().choices(string.ascii_letters + string.digits, k=6))
    return templates.TemplateResponse(request,"student_login.html", {"captcha": captcha_text})

@app.post("/student-portal", response_class=HTMLResponse)
async def student_portal(request: Request, user_captcha: str = Form(None), real_captcha: str = Form(None)):
    if user_captcha != real_captcha:
        return HTMLResponse("<h2>Captcha Failed! <a href='/student-login'>Try again</a></h2>")
    return templates.TemplateResponse(request,"student_portal.html")

@app.get("/raise-complaint", response_class=HTMLResponse)
async def complaint_form(request: Request):
    return templates.TemplateResponse(request,"complaint_form.html")

@app.post("/submit-complaint")
async def save_complaint(request: Request, category: str = Form(...), description: str = Form(...)):
    days = predict_days(category)
    new_data = {"Category": category, "Description": description, "Days": days, "Status": "Pending"}
    df = pd.DataFrame([new_data])
    df.to_csv("complaints.csv", mode='a', header=not os.path.exists("complaints.csv"), index=False)
    return templates.TemplateResponse(request,"success.html", {"days": days, "category": category})

@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request):
    return templates.TemplateResponse(request,"feedback_form.html")

@app.post("/submit-feedback")
async def save_feedback(request: Request, name: str = Form(None), rating: str = Form(...), comment: str = Form(...)):
    student_name = name if name else "Anonymous"
    new_feed = {"Name": student_name, "Rating": rating, "Comment": comment}
    df = pd.DataFrame([new_feed])
    df.to_csv("feedback.csv", mode='a', header=not os.path.exists("feedback.csv"), index=False)
    return HTMLResponse("<div style='text-align:center;padding:50px;'><h2>Feedback Submitted!</h2><a href='/student-portal'>Back to Portal</a></div>")

@app.get("/faculty-login", response_class=HTMLResponse)
async def faculty_login_view(request: Request):
    return templates.TemplateResponse(request,"faculty_login.html")

@app.post("/faculty-portal", response_class=HTMLResponse)
async def faculty_dashboard(request: Request, password: str = Form(...)):
    if password != "saiganesh":
        return HTMLResponse("<h2>Access Denied</h2>")

    complaints_list = []
    feedback_list = []
    
    # 1. Load Complaints & Handle Chart
    if os.path.exists("complaints.csv"):
        df_c = pd.read_csv("complaints.csv").fillna("N/A")
        if not df_c.empty:
            if "Status" not in df_c.columns:
                df_c["Status"] = "Pending"
            
            # Generate Analytics Chart
            plt.clf()
            df_c['Category'].value_counts().plot(kind='bar', color='#4e73df')
            plt.title("Complaints by Category")
            plt.tight_layout()
            plt.savefig("static/chart.png")
            
            # Reset index so loop.index0 works correctly for solving
            df_c = df_c.reset_index()
            complaints_list = df_c.to_dict(orient="records")

    # 2. Load Feedbacks
    if os.path.exists("feedback.csv"):
        df_f = pd.read_csv("feedback.csv").fillna("N/A")
        feedback_list = df_f.to_dict(orient="records")

    return templates.TemplateResponse(request,"faculty.html", {
        "complaints": complaints_list,
        "feedbacks": feedback_list,
        "total": len(complaints_list)
    })

@app.post("/solve-complaint/{index}")
async def solve_complaint(index:int=0):
    if os.path.exists("complaints.csv"):
        df = pd.read_csv("complaints.csv")
        if 0 <= index and index < len(df):
            df.loc[index, 'Status'] = 'SOLVED ✅'
            df.to_csv("complaints.csv", index=False)
    
    return HTMLResponse("<script>alert('Marked as Solved'); window.history.back();</script>")
