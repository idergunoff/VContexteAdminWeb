import datetime
import calendar
import json
import os

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jinja2.runtime import new_context

from auth import authenticate_user, create_access_token, oauth2_scheme

from pydantic import BaseModel
from typing import List
import pickle


from word import router as word_router

from model import *
from func import get_bg_color, get_versions_main, get_versions_tt, get_trying_by_word, draw_graph_user, \
    graph_vers_plotly, get_first_word_by_user
from control_ai import check_control_al

app = FastAPI()

app.include_router(word_router, prefix="/word", tags=["Word"])

# Подключение статики и шаблонизатора
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")



# Эта функция будет выполнена при запуске приложения
@app.on_event("startup")
async def load_model():
    with open('control/control_model.pkl', 'rb') as f:
        app.state.control_model = pickle.load(f)  # Загружаем модель и сохраняем в app.state


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

        result_cw = await session.execute(select(Word).filter_by(current=True))
        curr_word = result_cw.scalar_one_or_none()

    word_month = []
    for w in words:
        try:
            if w[2].strftime("%m %Y") not in word_month:
                word_month.append(w[2].strftime("%m %Y"))
        except AttributeError:
            continue
    word_month.append("new")

    if curr_word:
        dict_all = await get_trying_by_word(curr_word.id, 'uid')

        dict_all["word_month"] = word_month


        return templates.TemplateResponse("dashboard.html", {"request": request, "dict_all": dict_all})


@app.get("/versions/{trying_id}")
async def get_user_versions(trying_id: str, version_sort: str, version_type: str):
    # async with get_session() as session:
    #
    #     result = await session.execute(select(Version).filter_by(trying_id=int(trying_id)).order_by(Version.date_version))
    #     versions = result.scalars().all()
    #
    #     result_u = await session.execute(select(User).join(Trying).filter(Trying.id == int(trying_id)))
    #     user = result_u.scalar_one()
    #
    #     result_h = await session.execute(select(Version).join(Hint).filter(Version.trying_id == int(trying_id)))
    #     hints = result_h.scalars().all()
    #
    #     result_ha = await session.execute(select(Version).join(HintMainVers).filter(
    #         Version.trying_id == int(trying_id), HintMainVers.hint_type == "allusion"))
    #     hints_allusion = result_ha.scalars().all()
    #
    #     result_hc = await session.execute(select(Version).join(HintMainVers).filter(
    #         Version.trying_id == int(trying_id), HintMainVers.hint_type == "center"))
    #     hints_center = result_hc.scalars().all()
    #
    #     result_hw = await session.execute(select(HintMainWord).filter(HintMainWord.trying_id == int(trying_id)))
    #     hints_word = result_hw.scalars().all()
    #
    #     list_vers_hint = [hint.id for hint in hints]
    #     list_hint_allusion = [hint.id for hint in hints_allusion]
    #     list_hint_center = [hint.id for hint in hints_center]
    #
    # versions_data = [{
    #     "text": f'{n+1}. {version.text} {version.date_version.strftime("%H:%M:%S")} ✏️️{version.index}'
    #             f'{" 🧿" if version.id in list_vers_hint else ""}'
    #             f'{" 💎" if version.id in list_hint_allusion else ""}'
    #             f'{" 🌎" if version.id in list_hint_center else ""}',
    #     "date_version": version.date_version if version_sort == "time" else version.index,
    #     "bg_color": get_bg_color(version.index)
    # } for n, version in enumerate(versions)]
    #
    # versions_data += [{
    #     "text": f'{"🖼️ " if hint.hint_type == "pixel" else ""}'
    #             f'{"🦎 " if hint.hint_type == "tail" else ""}'
    #             f'{"📏 " if hint.hint_type == "metr" else ""}'
    #             f'{hint.hint_type.upper()} {hint.date_hint.strftime("%H:%M:%S")}',
    #     "date_version": hint.date_hint if version_sort == "time" else -1,
    #     "bg_color": '#ffffff'
    # } for hint in hints_word]
    #
    # versions_data = sorted(versions_data, key=lambda x: x['date_version'])
    # result = [{k: v for k, v in item.items() if k != 'date_version'} for item in versions_data]
    content = await get_versions_main(trying_id, version_sort) if version_type == "main" else await get_versions_tt(trying_id, version_sort)
    return JSONResponse(content=content)


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


@app.get("/word/{word_id}")
async def get_word(word_id: str):
    word_id = int(word_id)
    async with get_session() as session:
        result_w = await session.execute(select(Word).filter_by(id=word_id))
        word = result_w.scalars().first()

        return JSONResponse(content={"id": word.id, "word": word.word, "context": json.loads(word.context), "order": word.order})


@app.get("/trying/{word_id}")
async def get_trying(word_id: str, trying_sort: str):
    print(word_id, trying_sort)
    word_id = int(word_id)
    dict_all = await get_trying_by_word(word_id, trying_sort)
    return JSONResponse(dict_all)


@app.post("/trying/skip/{trying_id}")
async def skip_trying(trying_id: int):
    try:
        async with get_session() as session:
            result = await session.execute(select(Trying).filter_by(id=trying_id))
            trying = result.scalars().first()
            if not trying:
                raise HTTPException(status_code=404, detail="Trying not found")

            # Переключаем флаг skip
            trying.skip = not trying.skip

        return {"message": f"Trying {trying_id} updated successfully", "skip": trying.skip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class WordContextUpdate(BaseModel):
    order: List[dict]

@app.post("/update-context/{word_id}")
async def update_context(word_id: int, context: WordContextUpdate):
    new_context = [i["word_text"].split('. ')[1] for i in context.order]
    word_id = int(word_id)
    async with get_session() as session:
        result = await session.execute(select(Word).filter_by(id=word_id))
        word = result.scalars().first()
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")

        word.context = json.dumps(new_context)

    return {"message": f"Word {word_id} updated successfully", "context": new_context}


@app.get("/trying/control_ai/{trying_id}")
async def get_control_ai(trying_id):
    async with get_session() as session:
        result_t = await session.execute(select(Trying).filter_by(id=int(trying_id)))
        trying = result_t.scalar_one()

    if not trying.done:
        return {'text': '😴'}

    model = app.state.control_model  # Получаем уже загруженную модель из app.state

    mark, prob = await check_control_al(trying, model)

    dict_result = {'text': f'❤️ {str(round(prob[0], 3))}/{str(round(prob[1], 3))}'} if mark else {'text': f'☠️ {str(round(prob[0], 3))}/{str(round(prob[1], 3))}'}
    return dict_result


@app.get("/graph_vers/{trying_id}")
async def get_graph_vers(trying_id):
    async with get_session() as session:
        result_t = await session.execute(select(Trying).filter_by(id=int(trying_id)))
        trying = result_t.scalar_one()

    chart_html = await graph_vers_plotly(trying)
    return HTMLResponse(content=chart_html, status_code=200)


@app.get("/graph_trying/{trying_id}")
async def get_graph_trying(trying_id):
    async with get_session() as session:
        result_t = await session.execute(select(Trying).filter_by(id=int(trying_id)))
        trying = result_t.scalar_one()

    chart_html = await draw_graph_user(trying.user_id)
    return HTMLResponse(content=chart_html, status_code=200)

@app.get("/first_word/{trying_id}")
async def get_first_word(trying_id):
    async with get_session() as session:
        result_t = await session.execute(select(Trying).filter_by(id=int(trying_id)))
        trying = result_t.scalar_one()

        data = await get_first_word_by_user(trying.user_id)
        return data