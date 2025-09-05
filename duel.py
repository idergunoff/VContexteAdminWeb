"""Endpoints for duel administration pages."""


import calendar
import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from fastapi.templating import Jinja2Templates

from model import *
from func import get_bg_color


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
                Duel.started_at,
                Duel.finished_at,
                Duel.winner_id,
                Word.word,
                User.id.label("user_id"),
                User.username.label("user_name"),
                func.count(DuelVersion.id).label("version_count"),
                DuelParticipant.joined_at,
            )
            .join(Word, Duel.word_id == Word.id, isouter=True)
            .join(DuelParticipant, DuelParticipant.duel_id == Duel.id)
            .join(User, DuelParticipant.user_id == User.id)
            .join(
                DuelVersion,
                (DuelVersion.duel_id == Duel.id)
                & (DuelVersion.user_id == User.id),
                isouter=True,
            )
            .filter(
                Duel.created_at >= datetime.datetime(year=date_month.year, month=date_month.month, day=1),
                Duel.created_at <= datetime.datetime(year=date_month.year, month=date_month.month, day=last_day),
            )
            .group_by(
                Duel.id,
                Duel.created_at,
                Duel.started_at,
                Duel.finished_at,
                Duel.winner_id,
                Word.word,
                User.id,
                User.username,
                DuelParticipant.joined_at,
            )
            .order_by(Duel.created_at, DuelParticipant.joined_at)
        )

        rows = result.all()
        grouped = {}
        for (
            duel_id,
            created,
            started,
            finished,
            winner_id,
            word,
            user_id,
            user_name,
            version_count,
            _,
        ) in rows:
            grouped.setdefault(
                duel_id,
                {
                    "id": duel_id,
                    "date": created.strftime("%d.%m.%Y"),
                    "word": word or "",
                    "start_time": started.strftime("%H:%M:%S") if started else None,
                    "end_time": finished.strftime("%H:%M:%S") if finished else None,
                    "duration": round((finished - started).total_seconds()/60, 1)
                    if started and finished
                    else None,
                    "winner_id": winner_id,
                    "participants": [],
                },
            )["participants"].append(
                {
                    "id": user_id,
                    "name": user_name,
                    "version_count": version_count,
                }
            )

    return JSONResponse(content={"duels": list(grouped.values())})


@router.get("/versions/{duel_id}")
async def get_duel_versions(duel_id: int, sort: str = "time"):
    async with get_session() as session:
        result_p = await session.execute(
            select(DuelParticipant.user_id)
            .filter_by(duel_id=duel_id)
            .order_by(DuelParticipant.joined_at)
        )
        participants = result_p.scalars().all()
        player_map = {uid: idx + 1 for idx, uid in enumerate(participants)}

        order_col = DuelVersion.ts if sort == "time" else DuelVersion.idx_global
        result_v = await session.execute(
            select(DuelVersion, User)
            .join(User, DuelVersion.user_id == User.id)
            .filter(DuelVersion.duel_id == duel_id)
            .order_by(order_col)
        )
        rows = result_v.all()

        versions = [
            {
                "user_id": user.id,
                "text": dv.text,
                "idx": dv.idx_global,
                "ts": dv.ts.isoformat(),
                "player": player_map.get(dv.user_id),
                "bg_color": get_bg_color(dv.idx_global),
            }
            for dv, user in rows
        ]

    return JSONResponse(content={"versions": versions})


