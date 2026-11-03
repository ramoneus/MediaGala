"""The stats page: totals, charts and highlights for all time or a single year."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.stats import build_report
from app.templating import templates

router = APIRouter()


@router.get("/stats", response_class=HTMLResponse, name="stats")
def stats(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    year: Annotated[int | None, Query(ge=1900, le=9999)] = None,
) -> HTMLResponse:
    report = build_report(crud.list_all_titles(db), year)
    return templates.TemplateResponse(request, "stats.html", {"report": report})
