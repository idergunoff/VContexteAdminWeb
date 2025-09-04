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
    async with get_session() as session:
        date_month = datetime.datetime.strptime(month, "%m %Y")
        _, last_day = calendar.monthrange(date_month.year, date_month.month)

        result = await session.execute(
            select(
                Duel.id,
                Duel.created_at,
                Word.word,
                User.id.label("user_id"),
                User.username.label("user_name"),
            )
            .join(Word, Duel.word_id == Word.id, isouter=True)
            .join(DuelParticipant, DuelParticipant.duel_id == Duel.id)
            .join(User, DuelParticipant.user_id == User.id)
            .filter(
                Duel.created_at >= datetime.datetime(year=date_month.year, month=date_month.month, day=1),
                Duel.created_at <= datetime.datetime(year=date_month.year, month=date_month.month, day=last_day),
            )
            .order_by(Duel.created_at)
        )

        rows = result.all()
        grouped = {}
        for duel_id, created, word, user_id, user_name in rows:
            grouped.setdefault(
                duel_id,
                {
                    "id": duel_id,
                    "date": created.strftime("%d.%m.%Y"),
                    "word": word or "",
                    "participants": [],
                },
            )["participants"].append({"id": user_id, "name": user_name})

    return JSONResponse(content={"duels": list(grouped.values())})


