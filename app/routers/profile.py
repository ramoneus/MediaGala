"""The profile page: your name and how many titles of each kind you want to finish this year."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from app import crud
from app.catalog import Kind
from app.database import get_db
from app.templating import templates

router = APIRouter()

MAX_NAME = 40
MAX_GOAL = 1000

FLASH_MESSAGES = {"saved": "Profile saved."}


def read_profile_form(form: FormData) -> tuple[str, dict[str, int], dict[str, str]]:
    """The name, the goals that were filled in, and an error message for each field that's wrong."""
    errors: dict[str, str] = {}
    name = str(form.get("name", "")).strip()
    if len(name) > MAX_NAME:
        errors["name"] = f"Keep it to {MAX_NAME} characters or fewer."

    goals: dict[str, int] = {}
    for kind in Kind:
        field = f"goal_{kind.value}"
        raw = str(form.get(field, "")).strip()
        if not raw:
            continue
        if not raw.isdecimal():
            errors[field] = "Please enter a whole number."
        elif not 1 <= int(raw) <= MAX_GOAL:
            errors[field] = f"Choose a number between 1 and {MAX_GOAL}."
        else:
            goals[kind.value] = int(raw)
    return name, goals, errors


def render(request: Request, values: dict[str, str], errors: dict[str, str], msg: str = "", code: int = 200) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "values": values,
            "errors": errors,
            "kinds": list(Kind),
            "max_name": MAX_NAME,
            "max_goal": MAX_GOAL,
            "flash": FLASH_MESSAGES.get(msg),
        },
        status_code=code,
    )


@router.get("/profile", response_class=HTMLResponse, name="profile")
def show_profile(request: Request, db: Annotated[Session, Depends(get_db)], msg: str = "") -> HTMLResponse:
    profile = crud.get_profile(db)
    values = {"name": profile.name, **{f"goal_{kind}": str(goal) for kind, goal in profile.goals.items()}}
    return render(request, values, {}, msg)


@router.post("/profile", response_class=HTMLResponse)
async def save_profile(request: Request, db: Annotated[Session, Depends(get_db)]):
    form = await request.form()
    name, goals, errors = read_profile_form(form)
    if errors:
        values = {key: str(value).strip() for key, value in form.items()}
        return render(request, values, errors, code=status.HTTP_422_UNPROCESSABLE_CONTENT)
    crud.save_profile(db, name, goals)
    return RedirectResponse("/profile?msg=saved", status_code=status.HTTP_303_SEE_OTHER)
