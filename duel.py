"""Endpoints for duel administration pages."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from model import *


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def duel_dashboard(request: Request):
    """Render the duel admin dashboard."""
    dict_all = {"duel_id": 0, "duel_month": []}
    return templates.TemplateResponse(
        "dashboard_duel.html", {"request": request, "dict_all": dict_all}
    )

