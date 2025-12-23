"""Endpoints for duel administration pages."""


import calendar
import datetime
import json
from enum import Enum
from math import log
from typing import Sequence

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from fastapi.templating import Jinja2Templates

from model import *
from func import get_bg_color
from graph import graph_duel_versions_plotly
from sqlalchemy import case


router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def _load_duels(session, extra_filters: Sequence):
    result = await session.execute(
        select(
            Duel.id,
            Duel.created_at,
            Duel.started_at,
            Duel.finished_at,
            Duel.winner_id,
            Duel.is_draw,
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
        .filter(Duel.status != "cancelled", *extra_filters)
        .group_by(
            Duel.id,
            Duel.created_at,
            Duel.started_at,
            Duel.finished_at,
            Duel.winner_id,
            Duel.is_draw,
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
        is_draw,
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
                "date": created.strftime("%d.%m.%Y") if created else "",
                "word": word or "",
                "start_time": started.strftime("%H:%M:%S") if started else None,
                "end_time": finished.strftime("%H:%M:%S") if finished else None,
                "duration": round((finished - started).total_seconds() / 60, 1)
                if started and finished
                else None,
                "winner_id": winner_id,
                "is_draw": is_draw,
                "participants": [],
            },
        )["participants"].append(
            {
                "id": user_id,
                "name": user_name,
                "version_count": version_count,
            }
        )

    return list(grouped.values())


def _build_shared_best_history(
    attempts: Sequence[tuple[str | int, int]],
    players: Sequence[str | int],
) -> dict[str | int, list[int]]:
    """Return best rank before each attempt for provided players."""

    histories = {player: [] for player in players}
    if not attempts:
        return histories

    best_rank: int | None = None
    for player, rank in attempts:
        if player not in histories:
            continue

        baseline = rank if best_rank is None else best_rank
        histories[player].append(baseline)
        best_rank = rank if best_rank is None else min(best_rank, rank)
    return histories


def _log_progress(
    ranks: list[int],
    shared_best_before: Sequence[int] | None = None,
    gamma: float = 10,
    scale: float = 20,
) -> float:
    """
    Логарифмическая шкала прогресса.
    Progress = scale · Σ ln((old_best + γ)/(new_best + γ))

    ranks — список рангов после каждой попытки.
    """
    if not ranks:
        return 0.0

    best = shared_best_before[0] if shared_best_before else ranks[0]
    progress = 0.0
    start_index = 0 if shared_best_before else 1

    for idx, r in enumerate(ranks[start_index:], start=start_index):
        current_best = shared_best_before[idx] if shared_best_before else best
        if r < current_best:  # улучшение
            progress += log((current_best + gamma) / (r + gamma))
            best = r
        else:
            best = min(current_best, r)

        if shared_best_before and idx + 1 < len(shared_best_before):
            best = min(shared_best_before[idx + 1], best)

    return progress * scale


def _quality_penalty(
    ranks: list[int],
    shared_best_before: Sequence[int] | None = None,
    p: float = 50000,
) -> float:
    """
    QualityPenalty = Σ max(0, r_i − best_{i-1}) / p
    Штраф за «плохие» попытки, которые увеличивают ранг относительно лучшего.
    """
    if not ranks:
        return 0.0

    best = shared_best_before[0] if shared_best_before else ranks[0]
    penalty = 0.0
    start_index = 0 if shared_best_before else 1

    for idx, r in enumerate(ranks[start_index:], start=start_index):
        current_best = shared_best_before[idx] if shared_best_before else best
        if r > current_best:                 # ушёл дальше от секрета
            r = 30000 if r == 999999 else r
            penalty += (r - current_best) / p
            best = current_best
        else:
            best = r

        if shared_best_before and idx + 1 < len(shared_best_before):
            best = min(shared_best_before[idx + 1], best)

    return penalty


def _eff_norm(
    time_sec: int,
    attempts: int,
    avg_time: int | None = None,
    avg_attempts: int | None = None,
) -> float:
    """
    Normalized efficiency (0–1), combining time and attempts.
    """

    base_time = avg_time if avg_time and avg_time > 0 else 900
    base_attempts = avg_attempts if avg_attempts and avg_attempts > 0 else 100

    time_score = max(0, (base_time - time_sec) / base_time)
    guess_score = max(0, (base_attempts - attempts) / base_attempts)

    return 0.5 * (time_score + guess_score)


class Outcome(Enum):
    WIN = 1
    DRAW = 0.5
    LOSS = 0


def _vp_components(
    *,
    outcome: Outcome,
    ranks: list[int],
    shared_best_before: Sequence[int] | None,
    time_sec: int,
    attempts: int,
    avg_time_ref: int | None = None,
    avg_attempts_ref: int | None = None,
) -> tuple[float, float, float]:
    """Return VP component scores: (progress, efficiency, quality_penalty)."""

    progress = _log_progress(ranks, shared_best_before)

    progress_factor = min(1.0, progress / 50) if progress > 0 else 0.0
    efficiency = 0.0
    if outcome is Outcome.WIN:
        efficiency = (
            _eff_norm(time_sec, attempts, avg_time_ref, avg_attempts_ref)
            * 80
            * progress_factor
        )

    qp = _quality_penalty(ranks, shared_best_before)

    return progress, efficiency, qp


def _progress_penalty_steps(
    ranks: list[int],
    shared_best_before: Sequence[int] | None = None,
    *,
    gamma: float = 10,
    scale: float = 50,
    p: float = 50000,
) -> tuple[list[float], list[float]]:
    """Calculate per-attempt progress and penalty in a single pass."""

    if not ranks:
        return [], []

    best = shared_best_before[0] if shared_best_before else ranks[0]
    start_index = 0 if shared_best_before else 1

    progress_steps = [0.0 for _ in ranks]
    penalty_steps = [0.0 for _ in ranks]

    for idx, r in enumerate(ranks[start_index:], start=start_index):
        current_best = shared_best_before[idx] if shared_best_before else best
        if r < current_best:  # improvement
            progress_steps[idx] = log((current_best + gamma) / (r + gamma)) * scale
            best = r
        else:
            r = 30000 if r == 999999 else r
            if r > current_best:
                penalty_steps[idx] = (r - current_best) / p
                best = current_best
            else:
                best = r

        if shared_best_before and idx + 1 < len(shared_best_before):
            best = min(shared_best_before[idx + 1], best)

    return progress_steps, penalty_steps


@router.get("/", response_class=HTMLResponse)
async def duel_dashboard(request: Request):

    """Render the duel admin dashboard with available months."""
    async with get_session() as session:
        result_d = await session.execute(
            select(Duel.created_at)
            .filter(Duel.status != "cancelled")
            .order_by(Duel.created_at)
        )
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

        duels = await _load_duels(
            session,
            [
                Duel.created_at
                >= datetime.datetime(year=date_month.year, month=date_month.month, day=1),
                Duel.created_at
                <= datetime.datetime(year=date_month.year, month=date_month.month, day=last_day),
            ],
        )

    return JSONResponse(content={"duels": duels})


@router.get("/by_word/{word_id}")
async def get_duels_by_word(word_id: int):
    async with get_session() as session:
        duels = await _load_duels(session, [Duel.word_id == word_id])

    return JSONResponse(content={"duels": duels})


@router.get("/by_users")
async def get_duels_by_users(ids: str | None = None):
    if not ids:
        return JSONResponse(content={"duels": []})

    try:
        user_ids = {int(i) for i in ids.split(",") if i}
    except ValueError:
        return JSONResponse(content={"duels": []})

    if not user_ids:
        return JSONResponse(content={"duels": []})

    async with get_session() as session:
        duel_ids_result = await session.execute(
            select(Duel.id)
            .join(DuelParticipant, DuelParticipant.duel_id == Duel.id)
            .filter(
                Duel.status != "cancelled",
                DuelParticipant.user_id.in_(user_ids),
            )
        )

        duel_ids = {row[0] for row in duel_ids_result.fetchall()}
        if not duel_ids:
            return JSONResponse(content={"duels": []})

        duels = await _load_duels(session, [Duel.id.in_(duel_ids)])

    return JSONResponse(content={"duels": duels})


@router.get("/versions/{duel_id}")
async def get_duel_versions(duel_id: int, sort: str = "time"):
    async with get_session() as session:
        result_info = await session.execute(
            select(
                Duel.created_at,
                Duel.started_at,
                Duel.finished_at,
                Duel.winner_id,
                Duel.is_draw,
                Word.id.label("word_id"),
                Word.word,
                User.id.label("user_id"),
                User.username.label("user_name"),
                UserDuR.du_r.label("user_du_r"),
                UserVP.vp.label("user_vp"),
                func.count(DuelVersion.id).label("version_count"),
                DuelParticipant.joined_at,
                DuelParticipant.coins_delta.label("coins_delta"),
                DuelParticipant.vp_delta.label("vp_delta"),
                DuelParticipant.du_r_delta.label("du_r_delta"),
            )
            .join(Word, Duel.word_id == Word.id, isouter=True)
            .join(DuelParticipant, DuelParticipant.duel_id == Duel.id)
            .join(User, DuelParticipant.user_id == User.id)
            .join(UserDuR, UserDuR.user_id == User.id, isouter=True)
            .join(UserVP, UserVP.user_id == User.id, isouter=True)
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
                Duel.is_draw,
                Word.id,
                Word.word,
                User.id,
                User.username,
                DuelParticipant.joined_at,
                DuelParticipant.coins_delta,
                DuelParticipant.vp_delta,
                DuelParticipant.du_r_delta,
                UserDuR.du_r,
                UserVP.vp,
            )
            .order_by(DuelParticipant.joined_at)
        )
        info_rows = result_info.all()

        if not info_rows:
            empty_payload = {
                "word": "",
                "word_id": None,
                "date": "",
                "start_time": None,
                "end_time": None,
                "winner_id": None,
                "is_draw": None,
                "participants": [],
                "versions": [],
            }
            return JSONResponse(content=empty_payload, status_code=404)

        duel_started_at: datetime.datetime | None = None
        duel_finished_at: datetime.datetime | None = None
        duel_is_draw: bool | None = None

        created, started, finished, winner_id, is_draw, word_id, word, *_ = info_rows[0]
        duel_started_at = started
        duel_finished_at = finished
        duel_is_draw = is_draw
        duel_info = {
            "word": word or "",
            "word_id": word_id,
            "date": created.strftime("%d.%m.%Y") if created else "",
            "start_time": started.strftime("%H:%M:%S") if started else None,
            "end_time": finished.strftime("%H:%M:%S") if finished else None,
            "winner_id": winner_id,
            "is_draw": is_draw,
            "participants": [],
        }

        for (
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            user_id,
            user_name,
            user_du_r,
            user_vp,
            version_count,
            _,
            coins_delta,
            vp_delta,
            du_r_delta,
        ) in info_rows:
            duel_info["participants"].append(
                {
                    "id": user_id,
                    "name": user_name,
                    "version_count": version_count,
                    "coins": coins_delta,
                    "vp": user_vp,
                    "du_r": int(user_du_r),
                    "vp_delta": vp_delta,
                    "du_r_delta": du_r_delta,
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

        players = list(player_map.keys())
        attempts = [(dv.user_id, dv.idx_global) for dv, _ in rows]
        shared_histories = _build_shared_best_history(attempts, players)

        rank_histories: dict[int, list[int]] = {pid: [] for pid in players}
        attempt_indices: dict[int, int] = {pid: 0 for pid in players}
        last_attempt_ts: dict[int, datetime.datetime | None] = {
            pid: None for pid in players
        }

        collected_versions: list[tuple[DuelVersion, User, int]] = []

        versions = []
        for dv, user in rows:
            pid = dv.user_id
            rank_histories[pid].append(dv.idx_global)
            collected_versions.append((dv, user, pid))
            last_attempt_ts[pid] = dv.ts

        progress_steps: dict[int, list[float]] = {}
        penalty_steps: dict[int, list[float]] = {}

        for pid, ranks in rank_histories.items():
            shared_best = shared_histories.get(pid, [])[: len(ranks)]
            progress_steps[pid], penalty_steps[pid] = _progress_penalty_steps(
                ranks, shared_best
            )

        for dv, user, pid in collected_versions:
            attempt_idx = attempt_indices[pid]
            attempt_indices[pid] += 1
            versions.append(
                {
                    "user_id": user.id,
                    "text": dv.text,
                    "idx_global": dv.idx_global,
                    "idx_personal": dv.idx_personal,
                    "delta_rank": dv.delta_rank,
                    "ts": dv.ts.isoformat() if dv.ts else None,
                    "player": player_map.get(dv.user_id),
                    "bg_color": get_bg_color(dv.idx_global),
                    "progress": progress_steps.get(pid, [0.0])[attempt_idx],
                    "penalty": penalty_steps.get(pid, [0.0])[attempt_idx],
                }
            )

        total_attempts = len(rows)

        for participant in duel_info["participants"]:
            pid = participant["id"]
            ranks = rank_histories.get(pid, [])
            shared_best = shared_histories.get(pid, [])[: len(ranks)]

            if duel_started_at:
                end_time = last_attempt_ts.get(pid) or duel_finished_at or duel_started_at
                time_sec = max(
                    0, int((end_time - duel_started_at).total_seconds())
                )
            else:
                time_sec = 0

            attempts_for_eff = total_attempts or len(ranks) or 0
            outcome = (
                Outcome.DRAW
                if duel_is_draw
                else Outcome.WIN
                if duel_info.get("winner_id") == pid
                else Outcome.LOSS
            )

            progress_score, efficiency_score, qp = _vp_components(
                outcome=outcome,
                ranks=ranks,
                shared_best_before=shared_best,
                time_sec=time_sec,
                attempts=attempts_for_eff,
                avg_time_ref=None,
                avg_attempts_ref=None,
            )

            participant["vp_progress"] = round(progress_score, 2)
            participant["vp_efficiency"] = round(efficiency_score, 2)
            participant["vp_quality_penalty"] = round(qp, 4)

    return JSONResponse(content={**duel_info, "versions": versions})


@router.get("/word_play_dates/{duel_id}")
async def get_duel_word_play_dates(duel_id: int):
    async with async_session() as session:
        duel_result = await session.execute(
            select(Duel).options(selectinload(Duel.word)).filter(Duel.id == duel_id)
        )
        duel = duel_result.scalar_one_or_none()
        if not duel:
            return JSONResponse(content={"detail": "Duel not found"}, status_code=404)

        participants_result = await session.execute(
            select(User.id, User.username, DuelParticipant.joined_at)
            .join(DuelParticipant, DuelParticipant.user_id == User.id)
            .filter(DuelParticipant.duel_id == duel_id)
            .order_by(DuelParticipant.joined_at)
        )
        participants_rows = participants_result.all()
        user_ids = [row[0] for row in participants_rows]

        if not user_ids:
            return JSONResponse(
                content={"word": duel.word.word if duel.word else "", "participants": []}
            )

        tryings_result = await session.execute(
            select(Trying.user_id, Trying.date_trying)
            .filter(Trying.word_id == duel.word_id, Trying.user_id.in_(user_ids))
            .order_by(Trying.date_trying)
        )
        duel_versions_result = await session.execute(
            select(DuelVersion.user_id, func.min(DuelVersion.ts))
            .filter(
                DuelVersion.duel_id == duel_id,
                DuelVersion.user_id.in_(user_ids),
            )
            .group_by(DuelVersion.user_id)
        )

        main_dates: dict[int, list[str]] = {uid: [] for uid in user_ids}
        duel_dates: dict[int, list[str]] = {uid: [] for uid in user_ids}

        for user_id, date_trying in tryings_result.all():
            if date_trying:
                main_dates[user_id].append(date_trying.isoformat())

        for user_id, ts in duel_versions_result.all():
            if ts:
                duel_dates[user_id].append(ts.isoformat())

        participants = []
        for user_id, username, _ in participants_rows:
            participants.append(
                {
                    "id": user_id,
                    "name": username,
                    "main_tryings": main_dates.get(user_id, []),
                    "duel_tryings": duel_dates.get(user_id, []),
                }
            )

    return JSONResponse(
        content={"word": duel.word.word if duel.word else "", "participants": participants}
    )


@router.get("/stats", response_class=HTMLResponse)
async def duel_stats(request: Request):
    async with get_session() as session:
        result = await session.execute(
            select(
                DuelParticipant.duel_id,
                DuelParticipant.user_id,
                DuelParticipant.coins_delta,
                DuelParticipant.vp_delta,
                Duel.is_draw,
                Duel.winner_id,
                func.count(DuelVersion.id).label("version_count"),
                func.sum(
                    case(
                        (DuelVersion.delta_rank > 0, 1),
                        else_=0,
                    )
                ).label("success_count"),
            )
            .join(Duel, DuelParticipant.duel_id == Duel.id)
            .join(
                DuelVersion,
                (DuelVersion.duel_id == DuelParticipant.duel_id)
                & (DuelVersion.user_id == DuelParticipant.user_id),
                isouter=True,
            )
            .filter(
                Duel.started_at.is_not(None),
                Duel.finished_at.is_not(None),
                func.extract("epoch", Duel.finished_at - Duel.started_at) <= 30 * 60,
            )
            .group_by(
                DuelParticipant.duel_id,
                DuelParticipant.user_id,
                DuelParticipant.coins_delta,
                DuelParticipant.vp_delta,
                Duel.is_draw,
                Duel.winner_id,
            )
        )
        rows = result.all()

    def _empty_bucket() -> dict:
        return {
            "coins_by_versions": [],
            "vp_by_versions": [],
            "coins_by_success_ratio": [],
            "vp_by_success_ratio": [],
        }

    stats = {"winners": _empty_bucket(), "losers": _empty_bucket()}

    for (
        _duel_id,
        user_id,
        coins,
        vp,
        is_draw,
        winner_id,
        version_count,
        success_count,
    ) in rows:
        if coins is not None and coins < 0:
            continue

        versions = version_count or 0
        successes = success_count or 0
        success_ratio = successes / versions if versions else 0.0

        bucket = stats["losers"]
        if not is_draw and winner_id and winner_id == user_id:
            bucket = stats["winners"]

        bucket["coins_by_versions"].append({"x": versions, "y": coins or 0})
        bucket["vp_by_versions"].append({"x": versions, "y": vp or 0})
        bucket["coins_by_success_ratio"].append(
            {"x": success_ratio, "y": coins or 0}
        )
        bucket["vp_by_success_ratio"].append({"x": success_ratio, "y": vp or 0})

    return templates.TemplateResponse(
        "duel_stats.html",
        {
            "request": request,
            "stats_json": json.dumps(stats),
        },
    )


@router.get("/graph_vers/{duel_id}", response_class=HTMLResponse)
async def duel_versions_graph(duel_id: int):
    async with get_session() as session:
        duel = await session.get(Duel, duel_id)
    if not duel:
        return HTMLResponse(content="Duel not found", status_code=404)
    html = await graph_duel_versions_plotly(duel)
    return HTMLResponse(content=html)
