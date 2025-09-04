"""Endpoints for duel administration pages."""

import calendar
import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from model import *


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def duel_dashboard(request: Request):
    """Render the duel admin dashboard with available months."""
    async with get_session() as session:
        result_d = await session.execute(select(Duel.created_at).order_by(Duel.created_at))
        duels = result_d.all()

    duel_month = []
    for d in duels:
        try:
            month = d[0].strftime("%m %Y")
            if month not in duel_month:
                duel_month.append(month)
        except AttributeError:
            continue

    dict_all = {"duel_id": 0, "duel_month": duel_month}
    return templates.TemplateResponse(
        "dashboard_duel.html", {"request": request, "dict_all": dict_all}
    )


@router.get("/month/{month}")
async def get_month_duel(month: str):
    """Return duels for a given month."""
    async with get_session() as session:
        date_month = datetime.datetime.strptime(month, "%m %Y")
        _, last_day = calendar.monthrange(date_month.year, date_month.month)
        result = await session.execute(
            select(Duel.id, Duel.created_at, Word.word)
            .join(Word, Duel.word_id == Word.id, isouter=True)
            .filter(
                Duel.created_at >= datetime.datetime(
                    year=date_month.year, month=date_month.month, day=1
                ),
                Duel.created_at <= datetime.datetime(
                    year=date_month.year, month=date_month.month, day=last_day
                ),
            )
            .order_by(Duel.created_at)
        )
        duels = result.all()

    return JSONResponse(
        content={
            "duels": [
                {
                    "id": d[0],
                    "date": d[1].strftime("%d.%m.%Y"),
                    "word": d[2] or "",
                }
                for d in duels
            ]
        }
    )

