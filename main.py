"""Curiora Campus application entry point.

The app intentionally keeps the campus workflows lightweight and keeps Curio
vision inference isolated behind ``app.services.vision``.  That means the web
application can start even when the optional local vision model is not yet
installed.
"""

from __future__ import annotations

import csv
import secrets
import string
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers.curio import curio_router


ROOT_DIR = Path(__file__).resolve().parent
STATIC_DIR = ROOT_DIR / "static"
TEMPLATES_DIR = ROOT_DIR / "templates"
DATA_DIR = ROOT_DIR / "data"
COMPLAINTS_FILE = DATA_DIR / "complaints.csv"
FEEDBACK_FILE = DATA_DIR / "feedback.csv"

COMPLAINT_CATEGORIES = ("Academic", "Hostel", "Mess", "Infrastructure")
TRIAGE_ESTIMATES = {
    "Academic": 2.0,
    "Hostel": 3.0,
    "Mess": 1.0,
    "Infrastructure": 5.0,
}


app = FastAPI(title="saiganesh",version="1.0.0",docs_url=None,redoc_url=None,openapi_url=None)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.include_router(curio_router)


def render(request: Request, name: str, **context: Any) -> HTMLResponse:
    """Render a page with the request consistently available to Jinja."""

    return templates.TemplateResponse(
        request=request,
        name=name,
        context=context)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error):
        return []


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _append_csv(path: Path, fieldnames: tuple[str, ...], row: dict[str, str]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    has_rows = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not has_rows:
            writer.writeheader()
        writer.writerow(row)


def _complaints() -> list[dict[str, str]]:
    """Read current and legacy complaint CSV formats into one stable shape."""

    complaints: list[dict[str, str]] = []
    for row in _read_csv(COMPLAINTS_FILE):
        complaints.append(
            {
                "category": row.get("category") or row.get("Category") or "Other",
                "description": row.get("description") or row.get("Description") or "",
                "days": row.get("days") or row.get("Days") or "—",
                "status": row.get("status") or row.get("Status") or "Pending",
            }
        )
    return complaints


def _feedback() -> list[dict[str, str]]:
    feedback: list[dict[str, str]] = []
    for row in _read_csv(FEEDBACK_FILE):
        feedback.append(
            {
                "name": row.get("name") or row.get("Name") or "Anonymous",
                "rating": row.get("rating") or row.get("Rating") or "—",
                "comment": row.get("comment") or row.get("Comment") or "",
            }
        )
    return feedback


def estimate_resolution_days(category: str) -> float:
    """A transparent fallback estimate that keeps legacy triage operational."""

    return TRIAGE_ESTIMATES.get(category, 3.0)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return render(request, "pages/home.html")


@app.get("/visual-intelligence", response_class=HTMLResponse)
async def visual_intelligence(request: Request) -> HTMLResponse:
    return render(request, "pages/visual_intelligence.html")


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
    return render(request, "pages/login-form.html", captcha=captcha_text)


@app.post("/student-portal", response_class=HTMLResponse)
async def student_portal(
    request: Request,
    user_captcha: str = Form(""),
    real_captcha: str = Form(""),
) -> HTMLResponse:
    if user_captcha.strip() != real_captcha:
        return render(
            request,
            "pages/login-form.html",
            captcha=real_captcha,
            error="That captcha did not match. Please try again.",
        )
    return render(request, "pages/student_portal.html")


@app.get("/raise-complaint", response_class=HTMLResponse)
async def complaint_form(request: Request) -> HTMLResponse:
    return render(request, "pages/complaint_form.html", categories=COMPLAINT_CATEGORIES)


@app.post("/submit-complaint", response_class=HTMLResponse)
async def save_complaint(
    request: Request,
    category: str = Form(...),
    description: str = Form(...),
) -> HTMLResponse:
    category = category.strip()
    description = description.strip()

    if category not in COMPLAINT_CATEGORIES:
        raise HTTPException(status_code=422, detail="Choose a valid issue category.")
    if not description:
        raise HTTPException(status_code=422, detail="Describe the issue before submitting.")

    days = estimate_resolution_days(category)
    _append_csv(
        COMPLAINTS_FILE,
        ("category", "description", "days", "status"),
        {
            "category": category,
            "description": description,
            "days": f"{days:g}",
            "status": "Pending",
        },
    )
    return render(
        request,
        "pages/success.html",
        heading="Issue received",
        message=f"Your {category.lower()} report is now in the campus queue.",
        detail=f"Typical first response: about {days:g} day{'s' if days != 1 else ''}.",
    )


@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request) -> HTMLResponse:
    return render(request, "pages/feedback_form.html")


@app.post("/submit-feedback", response_class=HTMLResponse)
async def save_feedback(
    request: Request,
    name: str = Form(""),
    rating: str = Form(...),
    comment: str = Form(...),
) -> HTMLResponse:
    comment = comment.strip()
    if rating not in {"1", "2", "3", "4", "5"}:
        raise HTTPException(status_code=422, detail="Choose a rating from 1 to 5.")
    if not comment:
        raise HTTPException(status_code=422, detail="Write a short comment before submitting.")

    _append_csv(
        FEEDBACK_FILE,
        ("name", "rating", "comment"),
        {
            "name": name.strip() or "Anonymous",
            "rating": rating,
            "comment": comment,
        },
    )
    return render(
        request,
        "pages/success.html",
        heading="Feedback received",
        message="Thank you for helping improve the campus experience.",
        detail="Your response has been added to the faculty feedback log.",
    )


@app.get("/faculty-login", response_class=HTMLResponse)
async def faculty_login_view(request: Request) -> HTMLResponse:
    return render(request, "pages/faculty_login.html")


@app.post("/faculty-portal", response_class=HTMLResponse)
async def faculty_dashboard(request: Request, password: str = Form(...)) -> HTMLResponse:
    if password != "saiganesh":
        return render(
            request,
            "pages/faculty_login.html",
            error="Access denied. Check the faculty password and try again.",
        )

    complaints = _complaints()
    feedback = _feedback()
    category_counts = Counter(item["category"] for item in complaints)
    highest_count = max(category_counts.values(), default=1)
    category_stats = [
        {
            "category": category,
            "count": count,
            "width": round((count / highest_count) * 100),
        }
        for category, count in category_counts.most_common()
    ]

    return render(
        request,
        "pages/faculty.html",
        complaints=[{**item, "index": index} for index, item in enumerate(complaints)],
        feedbacks=feedback,
        total=len(complaints),
        solved_total=sum(item["status"].lower().startswith("solved") for item in complaints),
        category_stats=category_stats,
    )


@app.post("/solve-complaint/{index}")
async def solve_complaint(index: int) -> RedirectResponse:
    complaints = _complaints()
    if 0 <= index < len(complaints):
        complaints[index]["status"] = "Solved"
        _write_csv(COMPLAINTS_FILE, ("category", "description", "days", "status"), complaints)
    return RedirectResponse(url="/faculty-portal", status_code=303)
