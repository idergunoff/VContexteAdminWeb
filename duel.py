"""Endpoints for duel administration pages."""


import calendar
import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from fastapi.templating import Jinja2Templates

from model import *
from func import get_bg_color
from graph import graph_duel_versions_plotly


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
        result_info = await session.execute(
            select(
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
            .filter(Duel.id == duel_id)
            .group_by(
                Duel.created_at,
                Duel.started_at,
                Duel.finished_at,
                Duel.winner_id,
                Word.word,
                User.id,
                User.username,
                DuelParticipant.joined_at,
            )
            .order_by(DuelParticipant.joined_at)
        )
        info_rows = result_info.all()

        if info_rows:
            created, started, finished, winner_id, word, *_ = info_rows[0]
            duel_info = {
                "word": word or "",
                "date": created.strftime("%d.%m.%Y"),
                "start_time": started.strftime("%H:%M:%S") if started else None,
                "end_time": finished.strftime("%H:%M:%S") if finished else None,
                "winner_id": winner_id,
                "participants": [],
            }
        else:
            duel_info = {
                "word": "",
                "date": "",
                "start_time": None,
                "end_time": None,
                "winner_id": None,
                "participants": [],
            }

        for (
            _,
            _,
            _,
            _,
            _,
            user_id,
            user_name,
            version_count,
            _,
        ) in info_rows:
            duel_info["participants"].append(
                {
                    "id": user_id,
                    "name": user_name,
                    "version_count": version_count,
                }
            )

        player_map = {
            p["id"]: idx + 1 for idx, p in enumerate(duel_info["participants"])
        }

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
                "idx_global": dv.idx_global,
                "idx_personal": dv.idx_personal,
                "delta_rank": dv.delta_rank,
                "ts": dv.ts.isoformat() if dv.ts else None,
                "player": player_map.get(dv.user_id),
                "bg_color": get_bg_color(dv.idx_global),
            }
            for dv, user in rows
        ]

    return JSONResponse(content={**duel_info, "versions": versions})


@router.get("/graph_vers/{duel_id}", response_class=HTMLResponse)
async def duel_versions_graph(duel_id: int):
    async with get_session() as session:
        duel = await session.get(Duel, duel_id)
    if not duel:
        return HTMLResponse(content="Duel not found", status_code=404)
    html = await graph_duel_versions_plotly(duel)
    return HTMLResponse(content=html)


