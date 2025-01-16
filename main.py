import datetime
import calendar
import json

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from auth import authenticate_user, create_access_token, oauth2_scheme

from word import router as word_router

from model import *
from func import get_bg_color

app = FastAPI()

app.include_router(word_router, prefix="/word", tags=["Word"])

# Подключение статики и шаблонизатора
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/") and not request.url.path.startswith("/login"):
        token = request.cookies.get("access_token")
        if not token:
            return RedirectResponse("/login")
    response = await call_next(request)
    return response


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_action(
        request: Request,
        username: str = Form(),
        password: str = Form()
):
    user = authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"error": "Неверное имя пользователя или пароль", "request": request})
    access_token = create_access_token(data={"sub": user["username"]})
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=3600)
    return response



@app.post("/token")
async def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/logout")
async def logout_page():
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="access_token")
    return response


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    token = request.cookies.get("access_token")
    print(f"Токен: {token}")  # Печать токена в терминал
    if not token:
        return RedirectResponse(url="/login")

    dict_result = {}
    async with get_session() as session:
        result_w = await session.execute(select(Word.id, Word.word, Word.date_play).order_by(Word.date_play))
        words = result_w.all()

        result_u = await session.execute(select(User).order_by(User.date_register))
        users = result_u.scalars().all()

        result_cw = await session.execute(select(Word).filter_by(current=True))
        curr_word = result_cw.scalar_one_or_none()

        result_t = await session.execute(
            select(Trying)
            .options(selectinload(Trying.versions))
            .filter(Trying.word_id == curr_word.id))
        tryings = result_t.scalars().all()

        result_hu = await session.execute(select(UpdateTime))
        hour_update = result_hu.scalar_one_or_none().hour

        result_ud = await session.execute(
            select(User).filter(
                User.date_register > datetime.datetime(
                    year=curr_word.date_play.year,
                    month=curr_word.date_play.month,
                    day=curr_word.date_play.day, hour=hour_update),
                User.date_register < datetime.datetime(
                    year=curr_word.date_play.year,
                    month=curr_word.date_play.month,
                    day=curr_word.date_play.day, hour=hour_update) + datetime.timedelta(days=1)
            ))
        user_day = result_ud.scalars().all()

        result_ttt = await session.execute(
            select(TryingTopTen)
            .options(selectinload(TryingTopTen.vtt))
            .filter(TryingTopTen.word_id == curr_word.id))
        ttt = result_ttt.scalars().all()

        result_ur = await session.execute(select(UserRemind).filter(UserRemind.date_remind > (datetime.datetime.now() - datetime.timedelta(days=1))))
        user_remind = result_ur.scalars().all()

        result_hva = await session.execute(
            select(Trying).join(Version).join(HintMainVers)
            .filter(Trying.word_id == curr_word.id, HintMainVers.hint_type == 'allusion'))
        hint_allusion = result_hva.scalars().all()

        result_hvc = await session.execute(
            select(Trying).join(Version).join(HintMainVers)
            .filter(Trying.word_id == curr_word.id, HintMainVers.hint_type == 'center'))
        hint_center = result_hvc.scalars().all()

        result_hwp = await session.execute(
            select(Trying).join(HintMainWord)
            .filter(Trying.word_id == curr_word.id, HintMainWord.hint_type == 'pixel'))
        hint_word_pixel = result_hwp.scalars().all()

        result_hwt = await session.execute(
            select(Trying).join(HintMainWord)
            .filter(Trying.word_id == curr_word.id, HintMainWord.hint_type == 'tail'))
        hint_word_tail = result_hwt.scalars().all()

        result_hwm = await session.execute(
            select(Trying).join(HintMainWord)
            .filter(Trying.word_id == curr_word.id, HintMainWord.hint_type == 'metr'))
        hint_word_metr = result_hwm.scalars().all()

        result_htt = await session.execute(
            select(TryingTopTen).join(HintTopTen)
            .filter(TryingTopTen.word_id == curr_word.id))
        hint_top_ten = result_htt.scalars().all()

    word_month = []
    for w in words:
        try:
            if w[2].strftime("%m %Y") not in word_month:
                word_month.append(w[2].strftime("%m %Y"))
        except AttributeError:
            continue
    word_month.append("new")

    if curr_word:
        for u in users:
            t = next((t for t in tryings if t.user_id == u.id), None)
            if t:
                dict_result[u.id] = {
                    "username": u.username,
                    "date_register": u.date_register,
                    "date_last": u.date_last,
                    "score": u.score
                }
                dict_result[u.id]["t_id"] = t.id
                dict_result[u.id]["date_trying"] = t.date_trying
                dict_result[u.id]["done"] = t.done
                dict_result[u.id]["date_done"] = t.date_done
                dict_result[u.id]["hint"] = t.hint
                dict_result[u.id]["skip"] = t.skip
                dict_result[u.id]["count_vers"] = len(t.versions)
            else:
                continue

            tt = next((t for t in ttt if t.user_id == u.id), None)
            if tt:
                dict_result[u.id]["tt_id"] = tt.id
                dict_result[u.id]["date_start_tt"] = tt.date_start
                dict_result[u.id]["done_tt"] = tt.done
                dict_result[u.id]["date_done_tt"] = tt.date_done
                dict_result[u.id]["count_word_tt"] = tt.count_word
                dict_result[u.id]["count_vers_tt"] = len(tt.vtt)

                ht = next((i for i in hint_top_ten if i.user_id == u.id), None)
                dict_result[u.id]["hint_top_ten"] = True if ht else False

            else:
                dict_result[u.id]["tt_id"] = None
                dict_result[u.id]["date_start_tt"] = None
                dict_result[u.id]["done_tt"] = None
                dict_result[u.id]["date_done_tt"] = None
                dict_result[u.id]["count_word_tt"] = None
                dict_result[u.id]["count_vers_tt"] = None
                dict_result[u.id]["hint_top_ten"] = False


            ud = next((i for i in user_day if i.id == u.id), None)
            dict_result[u.id]["user_day"] = True if ud else False

            ur = next((i for i in user_remind if i.id == u.id), None)
            dict_result[u.id]["user_remind"] = True if ur else False

            ha = next((i for i in hint_allusion if i.user_id == u.id), None)
            dict_result[u.id]["hint_allusion"] = True if ha else False

            hc = next((i for i in hint_center if i.user_id == u.id), None)
            dict_result[u.id]["hint_center"] = True if hc else False

            hw = next((i for i in hint_word_pixel if i.user_id == u.id), None)
            dict_result[u.id]["hint_word_pixel"] = True if hw else False

            ht = next((i for i in hint_word_tail if i.user_id == u.id), None)
            dict_result[u.id]["hint_word_tail"] = True if ht else False

            hm = next((i for i in hint_word_metr if i.user_id == u.id), None)
            dict_result[u.id]["hint_word_metr"] = True if hm else False

        dict_all = {
            "word_month": word_month,
            "dict_result": dict_result
        }

        return templates.TemplateResponse("dashboard.html", {"request": request, "dict_all": dict_all})

        # return {
        #     "tryings":
        #         [{"id": t.id, "user": t.user.username, "ttt": len(t.user.ttt), "done": t.done, "count_vers": count_vers} for t, count_vers in tryings],
        #     "current_word":
        #             {"word": curr_word.word, "id": curr_word.id, "context": json.loads(curr_word.context)}
        # }

@app.get("/versions/{trying_id}")
async def get_user_versions(trying_id: str):
    async with get_session() as session:
        result = await session.execute(select(Version).filter_by(trying_id=int(trying_id)).order_by(Version.date_version))
        versions = result.scalars().all()

        result_u = await session.execute(select(User).join(Trying).filter(Trying.id == int(trying_id)))
        user = result_u.scalar_one()

        result_h = await session.execute(select(Version).join(Hint).filter(Version.trying_id == int(trying_id)))
        hints = result_h.scalars().all()

        result_ha = await session.execute(select(Version).join(HintMainVers).filter(
            Version.trying_id == int(trying_id), HintMainVers.hint_type == "allusion"))
        hints_allusion = result_ha.scalars().all()

        result_hc = await session.execute(select(Version).join(HintMainVers).filter(
            Version.trying_id == int(trying_id), HintMainVers.hint_type == "center"))
        hints_center = result_hc.scalars().all()

        result_hw = await session.execute(select(HintMainWord).filter(HintMainWord.trying_id == int(trying_id)))
        hints_word = result_hw.scalars().all()

        list_vers_hint = [hint.id for hint in hints]
        list_hint_allusion = [hint.id for hint in hints_allusion]
        list_hint_center = [hint.id for hint in hints_center]

    versions_data = [{
        "text": f'{n+1}. {version.text} {version.date_version.strftime("%H:%M:%S")} ✏️️{version.index}'
                f'{" 🧿" if version.id in list_vers_hint else ""}'
                f'{" 💎" if version.id in list_hint_allusion else ""}'
                f'{" 🌎" if version.id in list_hint_center else ""}',
        "date_version": version.date_version,
        "bg_color": get_bg_color(version.index)
    } for n, version in enumerate(versions)]

    versions_data += [{
        "text": f'{"🖼️ " if hint.hint_type == "pixel" else ""}'
                f'{"🦎 " if hint.hint_type == "tail" else ""}'
                f'{"📏 " if hint.hint_type == "metr" else ""}'
                f'{hint.hint_type.upper()} {hint.date_hint.strftime("%H:%M:%S")}',
        "date_version": hint.date_hint,
        "bg_color": '#ffffff'
    } for hint in hints_word]

    versions_data = sorted(versions_data, key=lambda x: x['date_version'])
    result = [{k: v for k, v in item.items() if k != 'date_version'} for item in versions_data]

    return JSONResponse(content={"versions": result, "username": user.username, "count_vers": len(versions)})


@app.get("/month_word/{month}")
async def get_month_word(month: str):
    async with get_session() as session:
        if month == "new":
            result = await session.execute(select(Word.id, Word.word, Word.order).filter(Word.order != 0).order_by(Word.order))
            words = result.all()

            return JSONResponse(content={"words": [{"id": word[0], "word": word[1], "order": word[2]} for word in words]})
        else:
            date_month = datetime.datetime.strptime(month, "%m %Y")
            _, last_day = calendar.monthrange(date_month.year, date_month.month)
            result = await session.execute(select(Word.id, Word.word, Word.date_play).filter(
                Word.date_play >= datetime.datetime(year=date_month.year, month=date_month.month, day=1),
                Word.date_play <= datetime.datetime(year=date_month.year, month=date_month.month, day=last_day)
            ).order_by(Word.date_play))
            words = result.all()

            return JSONResponse(content={"words": [{"id": word[0], "word": word[1], "order": word[2].strftime("%d.%m.%Y")} for word in words]})

@app.get("/trying/{word_id}")
async def get_trying(word_id: str):
    dict_result = {}
    word_id = int(word_id)
    async with get_session() as session:
        result_u = await session.execute(select(User).order_by(User.date_register))
        users = result_u.scalars().all()

        result_w = await session.execute(select(Word).filter_by(id=word_id))
        word = result_w.scalar_one_or_none()

        result_t = await session.execute(
            select(Trying)
            .options(selectinload(Trying.versions))
            .filter(Trying.word_id == word_id))
        tryings = result_t.scalars().all()

        result_ud = await session.execute(
            select(User).filter(
                User.date_register > word.date_play,
                User.date_register < (word.date_play + datetime.timedelta(days=1))
            ))
        user_day = result_ud.scalars().all()

        result_ttt = await session.execute(
            select(TryingTopTen)
            .options(selectinload(TryingTopTen.vtt))
            .filter(TryingTopTen.word_id == word_id))
        ttt = result_ttt.scalars().all()

        result_hva = await session.execute(
            select(Trying).join(Version).join(HintMainVers)
            .filter(Trying.word_id == word_id, HintMainVers.hint_type == 'allusion'))
        hint_allusion = result_hva.scalars().all()

        result_hvc = await session.execute(
            select(Trying).join(Version).join(HintMainVers)
            .filter(Trying.word_id == word_id, HintMainVers.hint_type == 'center'))
        hint_center = result_hvc.scalars().all()

        result_hwp = await session.execute(
            select(Trying).join(HintMainWord)
            .filter(Trying.word_id == word_id, HintMainWord.hint_type == 'pixel'))
        hint_word_pixel = result_hwp.scalars().all()

        result_hwt = await session.execute(
            select(Trying).join(HintMainWord)
            .filter(Trying.word_id == word_id, HintMainWord.hint_type == 'tail'))
        hint_word_tail = result_hwt.scalars().all()

        result_hwm = await session.execute(
            select(Trying).join(HintMainWord)
            .filter(Trying.word_id == word_id, HintMainWord.hint_type == 'metr'))
        hint_word_metr = result_hwm.scalars().all()

        result_htt = await session.execute(
            select(TryingTopTen).join(HintTopTen)
            .filter(TryingTopTen.word_id == word_id))
        hint_top_ten = result_htt.scalars().all()

    if word:
        for u in users:
            t = next((t for t in tryings if t.user_id == u.id), None)
            if t:
                dict_result[u.id] = {
                    "username": u.username,
                    "date_register": u.date_register.strftime('%d.%m.%Y'),
                    "date_last": u.date_last.strftime('%d.%m.%Y %H:%M'),
                    "score": u.score
                }
                dict_result[u.id]["t_id"] = t.id
                dict_result[u.id]["date_trying"] = t.date_trying.strftime('%d.%m.%Y %H:%M:%S')
                dict_result[u.id]["done"] = t.done
                dict_result[u.id]["date_done"] = t.date_done.strftime('%d.%m.%Y %H:%M:%S') if t.done else None
                dict_result[u.id]["hint"] = t.hint
                dict_result[u.id]["skip"] = t.skip
                dict_result[u.id]["count_vers"] = len(t.versions)
            else:
                continue

            tt = next((t for t in ttt if t.user_id == u.id), None)
            if tt:
                dict_result[u.id]["tt_id"] = tt.id
                dict_result[u.id]["date_start_tt"] = tt.date_start.strftime('%d.%m.%Y %H:%M:%S')
                dict_result[u.id]["done_tt"] = tt.done
                dict_result[u.id]["date_done_tt"] = tt.date_done.strftime('%d.%m.%Y %H:%M:%S') if tt.done else None
                dict_result[u.id]["count_word_tt"] = tt.count_word
                dict_result[u.id]["count_vers_tt"] = len(tt.vtt)

                ht = next((i for i in hint_top_ten if i.user_id == u.id), None)
                dict_result[u.id]["hint_top_ten"] = True if ht else False

            else:
                dict_result[u.id]["tt_id"] = None
                dict_result[u.id]["date_start_tt"] = None
                dict_result[u.id]["done_tt"] = None
                dict_result[u.id]["date_done_tt"] = None
                dict_result[u.id]["count_word_tt"] = None
                dict_result[u.id]["count_vers_tt"] = None
                dict_result[u.id]["hint_top_ten"] = False

            ud = next((i for i in user_day if i.id == u.id), None)
            dict_result[u.id]["user_day"] = True if ud else False

            ha = next((i for i in hint_allusion if i.user_id == u.id), None)
            dict_result[u.id]["hint_allusion"] = True if ha else False

            hc = next((i for i in hint_center if i.user_id == u.id), None)
            dict_result[u.id]["hint_center"] = True if hc else False

            hw = next((i for i in hint_word_pixel if i.user_id == u.id), None)
            dict_result[u.id]["hint_word_pixel"] = True if hw else False

            ht = next((i for i in hint_word_tail if i.user_id == u.id), None)
            dict_result[u.id]["hint_word_tail"] = True if ht else False

            hm = next((i for i in hint_word_metr if i.user_id == u.id), None)
            dict_result[u.id]["hint_word_metr"] = True if hm else False

        dict_all = {
            "word": word.word,
            "date_play": word.date_play.strftime('%d.%m.%Y'),
            "dict_result": dict_result
        }

        return JSONResponse(dict_all)
