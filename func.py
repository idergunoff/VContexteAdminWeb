import json
import datetime

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import numpy as np

from model import *


def get_bg_color(index: int):
    if index >= 5000:
        return '#f4bcfe'
    if 2500 <= index < 5000:
        return '#aad5ff'
    if 500 <= index < 2500:
        return '#d6ffab'
    if 100 <= index < 500:
        return '#ffffbf'
    if 20 <= index < 100:
        return '#ffc673'
    if 0 <= index < 20:
        return '#ff9f98'


async def get_versions_main(trying_id: str, version_sort: str):
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
        "text": f'{n + 1}. {version.text} {version.date_version.strftime("%H:%M:%S")} ✏️️{version.index}'
                f'{" 🧿" if version.id in list_vers_hint else ""}'
                f'{" 💎" if version.id in list_hint_allusion else ""}'
                f'{" 🌎" if version.id in list_hint_center else ""}',
        "date_version": version.date_version if version_sort == "time" else version.index,
        "bg_color": get_bg_color(version.index)
    } for n, version in enumerate(versions)]

    versions_data += [{
        "text": f'{"🖼️ " if hint.hint_type == "pixel" else ""}'
                f'{"🦎 " if hint.hint_type == "tail" else ""}'
                f'{"📏 " if hint.hint_type == "metr" else ""}'
                f'{hint.hint_type.upper()} {hint.date_hint.strftime("%H:%M:%S")}',
        "date_version": hint.date_hint if version_sort == "time" else -1,
        "bg_color": '#ffffff'
    } for hint in hints_word]

    versions_data = sorted(versions_data, key=lambda x: x['date_version'])
    result = [{k: v for k, v in item.items() if k != 'date_version'} for item in versions_data]

    return {"versions": result, "username": user.username, "count_vers": len(versions)}


async def get_versions_tt(trying_id: str, version_sort: str):
    async with get_session() as session:
        result_t = await session.execute(select(Trying).filter_by(id=int(trying_id)))
        trying = result_t.scalar_one()

        result_u = await session.execute(select(User).filter_by(id=trying.user_id))
        user = result_u.scalar_one()

        result_ttt = await session.execute(select(TryingTopTen).filter_by(user_id=user.id, word_id=trying.word_id))
        trying_tt = result_ttt.scalar_one_or_none()

        if not trying_tt:
            return {"versions": [], "username": user.username, "count_vers": 0}

        result_vtt = await session.execute(select(VersionTopTen).filter_by(ttt_id=trying_tt.id))
        versions_tt = result_vtt.scalars().all()

        result_htt = await session.execute(select(HintTopTen).filter_by(ttt_id=trying_tt.id))
        hints_tt = result_htt.scalars().all()

        result_w = await session.execute(select(Word).filter_by(id=trying.word_id))
        curr_word = result_w.scalar_one()

    context = json.loads(curr_word.context)
    versions_data = [{
        "text": f'{n + 1}. {version.text} {version.date_version.strftime("%H:%M:%S")} ✏️️{version.index}',
        "date_version": version.date_version if version_sort == "time" else version.index,
        "bg_color": get_bg_color(version.index)
    } for n, version in enumerate(versions_tt)]

    versions_data += [{
        "text": f'{"🗝 " if hint.hint_type == "key" else ""}'
                f'{"🐒 " if hint.hint_type == "tail" else ""}'
                f'{"🌀 " if hint.hint_type == "metr" else ""}'
                f'{hint.hint_type.upper()} *{context[hint.index_word]}* {hint.date_hint.strftime("%H:%M:%S")}',
        "date_version": hint.date_hint if version_sort == "time" else -1,
        "bg_color": '#ffffff'
    } for hint in hints_tt]

    versions_data = sorted(versions_data, key=lambda x: x['date_version'])
    result = [{k: v for k, v in item.items() if k != 'date_version'} for item in versions_data]

    return {"versions": result, "username": user.username, "count_vers": len(versions_tt)}


async def get_trying_by_word(word_id: int, sort: str):
    dict_result = {}
    async with get_session() as session:
        result_u = await session.execute(select(User).options(selectinload(User.coin)).order_by(User.date_register))
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
                ud = next((i for i in user_day if i.id == u.id), None)
                ha = [i for i in hint_allusion if i.user_id == u.id]
                hc = [i for i in hint_center if i.user_id == u.id]
                hw = next((i for i in hint_word_pixel if i.user_id == u.id), None)
                ht = next((i for i in hint_word_tail if i.user_id == u.id), None)
                hm = next((i for i in hint_word_metr if i.user_id == u.id), None)

                dict_result[u.id] = {}
                dict_result[u.id]['text'] = (f'{"🕺" if ud else ""}'
                                             f'<b>{u.username}</b> (id {u.id}) - 📦{len(t.versions)}'
                                             f'{" 🧿" + str(t.hint) if t.hint > 0 else ""}'
                                             f'{" 💎" + str(len(ha)) if ha else ""}'
                                             f'{" 🌎" + str(len(hc)) if hc else ""}'
                                             f'{" 🖼" if hw else ""}{" 🦎" if ht else ""}{" 📏" if hm else ""}')
                try:
                    dict_result[u.id]['title'] = (f'📆{u.date_register.strftime("%d-%m-%Y")}\n'
                                              f'✨{u.coin[0].coin}\n')
                except IndexError:
                    async with get_session() as session:
                        session.add(UserCoin(user_id=u.id, coin=521))
                    dict_result[u.id]['title'] = f'📆{u.date_register.strftime("%d-%m-%Y")}\n'

                dict_result[u.id]['t_id'] = t.id
                dict_result[u.id]['u_id'] = u.id
                dict_result[u.id]['date_start'] = t.date_trying
                dict_result[u.id]['date_done'] = t.date_done

                dict_result[u.id]['color'] = '#bfffbf' if t.done else '#f7faa6'
                if t.skip:
                    dict_result[u.id]['color'] = '#ffbfbf'
            else:
                continue

            tt = next((t for t in ttt if t.user_id == u.id), None)
            if tt:
                ht = next((i for i in hint_top_ten if i.user_id == u.id), None)
                dict_result[u.id]["text"] += (f'<br>🐛{len(tt.vtt)}({tt.count_word})'
                                              f' {" 🍤" if ht else ""}')
                if tt.done:
                    dict_result[u.id]["color"] = '#45ece7'

                if t.skip:
                    dict_result[u.id]['color'] = '#ffbfbf'

        if sort == 'start':
            dict_result = sorted(dict_result.values(), key=lambda x: x['date_start'])

        elif sort == 'done':
            dict_result = {k: v for k, v in dict_result.items() if v['date_done'] is not None}
            dict_result = sorted(dict_result.values(), key=lambda x: x['date_done'])
        elif sort == 'top':
            dict_result = {k: v for k, v in dict_result.items() if v['date_done'] is not None and v['color'] != '#ffbfbf'}
            dict_result = await update_dict_for_top(word_id, dict_result)
            dict_result = sorted(dict_result.values(), key=lambda x: (-x['score'], x['position']))
            for key in dict_result:
                key['text'] += f'<br>🏆{key["position"]} 🍬{key["score"]}'
                key['title'] += f'📦{key["score_vers"]} - 🧭{key["score_time"]} - 💎{key["score_pos"]}\n'
        else:
            dict_result = sorted(dict_result.values(), key=lambda item: item['u_id'])

        for key in dict_result:
            key['date_start'] = key['date_start'].strftime('%H:%M:%S')
            key['date_done'] = key['date_done'].strftime('%H:%M:%S') if key['date_done'] else None
            if sort == 'start' or sort == 'uid':
                key['title'] += f'🔫{key["date_start"]}'
                if key['date_done']:
                    key['title'] += f' - 🏁{key["date_done"]}'
            if sort == 'done' or sort == 'top':
                key['title'] += f'🔫{key["date_start"]} - 🏁{key["date_done"]}'

        dict_all = {
            "word": word.word,
            "date_play": word.date_play.strftime('%d.%m.%Y'),
            "word_id": word.id,
            "dict_result": dict_result
        }

    return dict_all


async def update_dict_for_top(word_id: int, dict_result: dict):

    list_time, list_tuple_time, list_count_vers, list_count_hint, skip_done = await calculate_stat(word_id)
    for key, value in dict_result.items():
        async with get_session() as session:
            t = await session.get(Trying, value['t_id'], options=[selectinload(Trying.versions)])
        score_vers, score_time, score_pos, user_score = await calc_trying_score(t, list_time, list_count_vers, skip_done)

        dict_result[key]['score_vers'] = score_vers
        dict_result[key]['score_time'] = score_time
        dict_result[key]['score_pos'] = score_pos
        dict_result[key]['score'] = user_score
        dict_result[key]['position'] = t.position

    return dict_result


async def calc_user_value(worst_value, best_value, current_value):
    """ Возвращает пропорциональное выбранное значение по лучшему и худшему значению """
    # Проверка на деление на ноль, чтобы избежать ошибок
    if worst_value == best_value:
        return 100
    # Рассчитываем пропорциональное значение
    proportion = (current_value - worst_value) / (best_value - worst_value)
    # Приводим к диапазону от 0 до 100
    proportional_value = int(proportion * 100)

    return proportional_value


async def calculate_stat(word_id: int):
    """ Возвращает списки разницы времени, количества версий и подсказок для удачных попыток для выбранного слова """
    async with get_session() as session:
        result_done = await session.execute(select(Trying).options(selectinload(Trying.versions)).filter_by(word_id=word_id, done=True))
        trying_done = result_done.scalars().all()

        result_skip = await session.execute(select(func.count()).select_from(Trying).filter_by(word_id=word_id, skip=True))
        skip_done = result_skip.scalar_one()

    if len(trying_done) == 0:
        return [], [], [], []
    trying_done = [t for t in trying_done if len(t.versions) > 1]
    trying_done = [t for t in trying_done if t.skip is False]
    list_time = [t.date_done - t.date_trying for t in trying_done]
    list_tuple_time = [(t.date_trying, t.date_done) for t in trying_done]
    list_count_vers = [len(t.versions) for t in trying_done]
    list_count_hint = [t.hint for t in trying_done]
    return list_time, list_tuple_time, list_count_vers, list_count_hint, skip_done


async def calc_trying_score(trying, l_time, l_count_vers, skip_done):
    """ Рассчитывает очки попытки пользователя и добавляет их в таблицу """
    score_vers = await calc_user_value(np.max(l_count_vers), np.min(l_count_vers), len(trying.versions))
    score_time = await calc_user_value(np.max(l_time).total_seconds(), np.min(l_time).total_seconds(), (trying.date_done - trying.date_trying).total_seconds())
    score_pos = await calc_user_value(len(l_time) + skip_done, 1, trying.position)
    user_score = score_vers + score_time + score_pos - (50 * trying.hint)

    return score_vers, score_time, score_pos, user_score



async def graph_vers_plotly(trying):
    # Получение данных из базы данных
    async with get_session() as session:
        result_v = await session.execute(select(Version).filter_by(trying_id=trying.id).order_by(Version.date_version))
        versions = result_v.scalars().all()

        result_h = await session.execute(select(Hint).join(Version).filter(Version.trying_id == trying.id))
        hints = result_h.scalars().all()

        result_ha = await session.execute(select(HintMainVers).join(Version).filter(
            Version.trying_id == trying.id,
            HintMainVers.hint_type == 'allusion'
        ))
        hint_allusion = result_ha.scalars().all()

        result_hc = await session.execute(select(HintMainVers).join(Version).filter(
            Version.trying_id == trying.id,
            HintMainVers.hint_type == 'center'
        ))
        hint_center = result_hc.scalars().all()

        result_hp = await session.execute(
            select(HintMainWord).filter_by(trying_id=trying.id, hint_type='pixel'))
        hint_pixel = result_hp.scalar_one_or_none()

        result_hb = await session.execute(
            select(HintMainWord).filter_by(trying_id=trying.id, hint_type='bomb'))
        hint_bomb = result_hb.scalar_one_or_none()

        result_ht = await session.execute(
            select(HintMainWord).filter_by(trying_id=trying.id, hint_type='tail'))
        hint_tail = result_ht.scalar_one_or_none()

        result_hm = await session.execute(
            select(HintMainWord).filter_by(trying_id=trying.id, hint_type='metr'))
        hint_metr = result_hm.scalar_one_or_none()

        result_u = await session.execute(select(User).filter_by(id=trying.user_id))
        user = result_u.scalars().first()

    list_hints = [i.version_id for i in hints]
    list_hint_allusion = [i.version_id for i in hint_allusion]
    list_hint_center = [i.version_id for i in hint_center]

    # Инициализация списков для данных
    list_time, list_index, list_hint_time, list_hint_index, list_text = [], [], [], [], []
    list_hint_allusion_time, list_hint_allusion_index = [], []
    list_hint_center_time, list_hint_center_index = [], []

    # Заполнение списков данными
    for v in versions:
        list_time.append(v.date_version)
        list_index.append(v.index)
        list_text.append(v.text)
        if v.id in list_hints:
            list_hint_time.append(v.date_version)
            list_hint_index.append(v.index)
        if v.id in list_hint_allusion:
            list_hint_allusion_time.append(v.date_version)
            list_hint_allusion_index.append(v.index)
        if v.id in list_hint_center:
            list_hint_center_time.append(v.date_version)
            list_hint_center_index.append(v.index)

    # Обработка значений индексов
    list_index = [25000 if i == 999999 else i for i in list_index]
    list_index = [1 if i == 0 else i for i in list_index]

    # Создание графика
    fig = go.Figure()

    # Добавление основной линии
    fig.add_trace(go.Scatter(
        x=list_time,
        y=list_index,
        mode='lines+markers',
        name='Версии',
        line=dict(color='blue', width=2),
        marker=dict(size=8, color='blue'),
        text=list_text,  # Добавляем список текста
        hovertemplate='Время: %{x|%H:%M}<br>Индекс: %{y}<br>Текст: %{text}'
    ))

    # Добавление красных маркеров для подсказок
    fig.add_trace(go.Scatter(
        x=list_hint_time,
        y=list_hint_index,
        mode='markers',
        name='Подсказки',
        marker=dict(size=10, color='red', symbol='circle'),
        text=[list_text[list_time.index(t)] for t in list_hint_time],  # Соответствующий текст для подсказок
        hovertemplate='Время: %{x|%H:%M}<br>Индекс: %{y}<br>Текст: %{text}'  # Настраиваем всплывающую подсказку
    ))

    fig.add_trace(go.Scatter(
        x=list_hint_allusion_time,
        y=list_hint_allusion_index,
        mode='markers',
        name='Allusion',
        marker=dict(size=10, color='cyan', symbol='circle'),
        text=[list_text[list_time.index(t)] for t in list_hint_allusion_time],  # Соответствующий текст для подсказок
        hovertemplate='Время: %{x|%H:%M}<br>Индекс: %{y}<br>Текст: %{text}'  # Настраиваем всплывающую подсказку
    ))

    fig.add_trace(go.Scatter(
        x=list_hint_center_time,
        y=list_hint_center_index,
        mode='markers',
        name='Центр',
        marker=dict(size=10, color='orange', symbol='circle'),
        text=[list_text[list_time.index(t)] for t in list_hint_center_time],  # Соответствующий текст для подсказок
        hovertemplate='Время: %{x|%H:%M}<br>Индекс: %{y}<br>Текст: %{text}'  # Настраиваем всплывающую подсказку
    ))

    if hint_pixel:
        fig.add_vline(
            x=hint_pixel.date_hint.timestamp() * 1000,  # Преобразуем в миллисекунды для Plotly
            line=dict(color="green", width=4, dash="dash"),
            annotation_text="Пиксель",
            annotation_position="top left"
        )

    if hint_bomb:
        fig.add_vline(
            x=hint_bomb.date_hint.timestamp() * 1000,  # Преобразуем в миллисекунды для Plotly
            line=dict(color="red", width=4, dash="dash"),
            annotation_text="Бомба",
            annotation_position="top left"
        )

    if hint_tail:
        fig.add_vline(
            x=hint_tail.date_hint.timestamp() * 1000,  # Преобразуем в миллисекунды для Plotly
            line=dict(color="purple", width=4, dash="dash"),
            annotation_text="Хвост",
            annotation_position="top left"
        )

    if hint_metr:
        fig.add_vline(
            x=hint_metr.date_hint.timestamp() * 1000,  # Преобразуем в миллисекунды для Plotly
            line=dict(color="orange", width=4, dash="dash"),
            annotation_text="Метр",
            annotation_position="top left"
        )

    # Если задача выполнена, добавляем зеленый маркер
    if trying.done:
        fig.add_trace(go.Scatter(
            x=[trying.date_done],
            y=[1],
            mode='markers',
            name='Выполнено',
            marker=dict(size=10, color='green', symbol='circle')
        ))

    # Настройка оси Y (логарифмическая шкала)
    fig.update_yaxes(type="log", range=[0, 5], title_text="Индекс")

    # Настройка оси X (форматирование дат)
    fig.update_xaxes(
        tickformat="%H:%M",
        title_text="Время",
        tickangle=90,
        minor=dict(ticks="inside", showgrid=True)
    )

    # Включение сетки
    fig.update_layout(
        grid=dict(rows=1, columns=1, pattern="independent"),
        xaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=1),
        yaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=1),
        title=f"График версий {user.username}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white"
    )
    # Отображение графика
    return fig.to_html(full_html=True, include_plotlyjs="cdn")


async def draw_graph_user(user_id):
    async with get_session() as session:
        result_t = await session.execute(select(Trying).options(selectinload(Trying.versions)).filter_by(
            user_id=user_id, done=True).order_by(Trying.date_trying))
        tryings = result_t.scalars().all()

        result_w = await session.execute(select(Word.word, Word.date_play, Word.id).filter_by(order=0))
        words = result_w.all()

        result_u = await session.execute(select(User).filter_by(id=user_id))
        user = result_u.scalars().first()

        result_tha = await session.execute(select(HintMainVers.id, Trying.id).join(
            Version, HintMainVers.version_id == Version.id
        ).join(Trying, Version.trying_id == Trying.id).filter(
            Trying.user_id == user_id,
            HintMainVers.hint_type == 'allusion'
        ))
        hint_allusion = result_tha.all()
        list_ha = [h[1] for h in hint_allusion]

        result_thc = await session.execute(select(HintMainVers.id, Trying.id).join(
            Version, HintMainVers.version_id == Version.id
        ).join(Trying, Version.trying_id == Trying.id).filter(
            Trying.user_id == user_id,
            HintMainVers.hint_type == 'center'
        ))
        hint_center = result_thc.all()
        list_hc = [h[1] for h in hint_center]

        result_thb = await session.execute(select(HintMainWord.id, Trying.id).join(
            Trying, HintMainWord.trying_id == Trying.id
        ).filter(
            Trying.user_id == user_id,
            HintMainWord.hint_type == 'bomb'
        ))
        hint_bomb = result_thb.all()
        list_hb = [h[1] for h in hint_bomb]

        result_tht = await session.execute(select(HintMainWord.id, Trying.id).join(
            Trying, HintMainWord.trying_id == Trying.id
        ).filter(
            Trying.user_id == user_id,
            HintMainWord.hint_type == 'tail'
        ))
        hint_tail = result_tht.all()
        list_ht = [h[1] for h in hint_tail]

        result_thm = await session.execute(select(HintMainWord.id, Trying.id).join(
            Trying, HintMainWord.trying_id == Trying.id
        ).filter(
            Trying.user_id == user_id,
            HintMainWord.hint_type == 'metr'
        ))
        hint_metr = result_thm.all()
        list_hm = [h[1] for h in hint_metr]

        result_thp = await session.execute(select(HintMainWord.id, Trying.id).join(
            Trying, HintMainWord.trying_id == Trying.id
        ).filter(
            Trying.user_id == user_id,
            HintMainWord.hint_type == 'pixel'
        ))
        hint_pixel = result_thp.all()
        list_hp = [h[1] for h in hint_pixel]


        dict_word_text = {w[2]: f'{w[1].strftime("%d.%m")} - {w[0]}' for w in words}

        # Подготовка данных
        list_count_vers = [len(t.versions) for t in tryings]
        list_time_try = [(t.date_done - t.date_trying).total_seconds() / 3600 for t in tryings]
        list_hint = [t.hint for t in tryings]
        list_word, list_allusion, list_center, list_bomb, list_tail, list_metr, list_pixel, list_color = [], [], [], [], [], [], [], []
        for t in tryings:
            list_word.append(dict_word_text[t.word_id])
            list_allusion.append(list_ha.count(t.id))
            list_center.append(list_hc.count(t.id))
            list_bomb.append(list_hb.count(t.id)*5)
            list_tail.append(list_ht.count(t.id)*5)
            list_metr.append(list_hm.count(t.id)*5)
            list_pixel.append(list_hp.count(t.id)*5)
            list_color.append('#b28282' if t.skip else '#87CEEB')


    # Создание подграфиков с двумя осями Y
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Добавление столбцов для попыток
    fig.add_trace(
        go.Bar(
            x=[i for i in range(len(list_word))],
            y=list_count_vers,
            name="Попыток",
            marker_color=list_color,
            text=[str(v) for v in list_count_vers],
            textposition="auto",
            textfont=dict(size=11, color="#87CEEB", family="bold"),
            hovertemplate="Слово: %{customdata[0]}<br>Попыток: %{y}",
            customdata=list(zip(list_word, list_hint))  # Добавляем список подсказок в customdata
        ),
        secondary_y=False,
    )

    # Добавление столбцов для подсказок (с накоплением)
    fig.add_trace(
        go.Bar(
            x=[i for i in range(len(list_word))],
            y=list_hint,
            name="Подсказок",
            marker_color="#F08080",
            base=list_count_vers,  # Накопление поверх попыток
            text=[str(h) if h > 0 else "" for h in list_hint],
            textposition="auto",
            textfont=dict(size=11, color="#F08080", family="bold"),
            hovertemplate="Слово: %{customdata[0]}<br>Подсказок: %{customdata[1]}",  # Используем customdata[1] для подсказок
            customdata=list(zip(list_word, list_hint))  # Добавляем список подсказок в customdata
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=[i for i in range(len(list_word))],
            y=list_allusion,
            name="Allusion",
            marker_color="#e5ef47",
            base=[sum(elements) for elements in zip(list_hint, list_count_vers)],  # Накопление поверх подсказок
            text=[str(h) if h > 0 else "" for h in list_allusion],
            textposition="auto",
            textfont=dict(size=11, color="#e5ef47", family="bold"),
            hovertemplate="Слово: %{customdata[0]}<br>Allusion: %{customdata[1]}",  # Используем customdata[1] для подсказок
            customdata=list(zip(list_word, list_allusion))  # Добавляем список подсказок в customdata
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=[i for i in range(len(list_word))],
            y=list_center,
            name="Center",
            marker_color="#5def47",
            base=[sum(elements) for elements in zip(list_hint, list_count_vers, list_allusion)],  # Накопление поверх подсказок
            text=[str(h) if h > 0 else "" for h in list_center],
            textposition="auto",
            textfont=dict(size=11, color="#5def47", family="bold"),
            hovertemplate="Слово: %{customdata[0]}<br>Center: %{customdata[1]}",  # Используем customdata[1] для подсказок
            customdata=list(zip(list_word, list_center))  # Добавляем список подсказок в customdata
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=[i for i in range(len(list_word))],
            y=list_bomb,
            name="Bomb",
            marker_color="#b247ef",
            base=[0 for i in range(len(list_word))],  # Накопление поверх подсказок
            text=[str(h) if h > 0 else "" for h in list_bomb],
            textposition="auto",
            textfont=dict(size=11, color="#b247ef", family="bold"),
            hovertemplate="Слово: %{customdata}<br>Bomb",  # Используем customdata[1] для подсказок
            customdata=list_word # Добавляем список подсказок в customdata
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=[i for i in range(len(list_word))],
            y=list_tail,
            name="Tail",
            marker_color="#ef47c2",
            base=[list_bomb],  # Накопление поверх подсказок
            text=[str(h) if h > 0 else "" for h in list_tail],
            textposition="auto",
            textfont=dict(size=11, color="#ef47c2", family="bold"),
            hovertemplate="Слово: %{customdata}<br>Tail",  # Используем customdata[1] для подсказок
            customdata=list_word  # Добавляем список подсказок в customdata
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=[i for i in range(len(list_word))],
            y=list_metr,
            name="Metr",
            marker_color="#47efde",
            base=[sum(elements) for elements in zip(list_bomb, list_tail)],  # Накопление поверх подсказок
            text=[str(h) if h > 0 else "" for h in list_metr],
            textposition="auto",
            textfont=dict(size=11, color="#47efde", family="bold"),
            hovertemplate="Слово: %{customdata}<br>Metr",  # Используем customdata[1] для подсказок
            customdata=list_word # Добавляем список подсказок в customdata
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=[i for i in range(len(list_word))],
            y=list_pixel,
            name="Pixel",
            marker_color="#ff9500",
            base=[sum(elements) for elements in zip(list_bomb, list_tail, list_metr)],  # Накопление поверх подсказок
            text=[str(h) if h > 0 else "" for h in list_pixel],
            textposition="auto",
            textfont=dict(size=11, color="#ff9500", family="bold"),
            hovertemplate="Слово: %{customdata}<br>Pixel",  # Используем customdata[1] для подсказок
            customdata=list_word  # Добавляем список подсказок в customdata
        ),
        secondary_y=False,
    )

    # Добавление линии для времени угадывания
    fig.add_trace(
        go.Scatter(
            x=[i for i in range(len(list_word))],
            y=list_time_try,
            name="Часов",
            line=dict(color="#FF8C00", width=2),
            marker=dict(size=8, symbol="circle"),
            hovertemplate="Слово: %{customdata[0]}<br>Время: %{y:.2f} ч",
            customdata=list(zip(list_word, list_hint))  # Добавляем список подсказок в customdata
        ),
        secondary_y=True,
    )

    # Настройка осей и макета
    fig.update_layout(
        xaxis=dict(
            showticklabels=False,  # Убираем все метки на оси X
        ),
        yaxis=dict(
            title=dict(
                text="Количество попыток и подсказок",
                font=dict(color="#87CEEB")
            ),
            tickfont=dict(color="#87CEEB"),
            range=[0, max(list_count_vers) + max(list_hint) + 10]
        ),
        yaxis2=dict(
            title=dict(
                text="Время угадывания, часов",
                font=dict(color="#FF8C00")
            ),
            tickfont=dict(color="#FF8C00"),
            range=[0, max(list_time_try) + 1],
            overlaying="y",
            side="right"
        ),
        title=dict(
            text=user.username,
            font=dict(size=16)
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        bargap=0.2,
        barmode="stack",  # Столбцы будут накоплены друг над другом
        plot_bgcolor="white"
    )
    # Включение сетки
    fig.update_xaxes(showgrid=True, gridcolor="lightgray")
    fig.update_yaxes(showgrid=True, gridcolor="lightgray", secondary_y=False)
    fig.update_yaxes(showgrid=True, gridcolor="lightgray", secondary_y=True)

    # Если нужно вернуть HTML для использования в веб-приложении
    return fig.to_html(full_html=True, include_plotlyjs="cdn")


async def get_first_word_by_user(user_id):
    async with (get_session() as session):
        result_u = await session.execute(select(User).filter_by(id=user_id))
        user = result_u.scalar_one()

        result_t = await session.execute(select(Trying).options(selectinload(Trying.versions)).filter_by(
            user_id=user_id
        ).order_by(desc(Trying.date_trying)))
        tryings = result_t.scalars().all()

        list_result, list_count_vers, count_skip = [], [], 0
        for t in tryings:
            dict_item = {}
            result_w = await session.execute(select(Word.word, Word.date_play).filter_by(id=t.word_id))
            word = result_w.first()
            done = f'✅' if t.done else '❌'
            skip = f'⏭' if t.skip else ''
            dict_item['text'] = f'{done}{skip}{len(t.versions)}/🧿{t.hint} - {word[0]} - {word[1].strftime("%d.%m.%y")}'
            dict_item['color'] = '#ffd6d6'
            if t.done:
                dict_item['color'] = '#d6ffd6'
                list_count_vers.append(len(t.versions))
            if t.skip:
                dict_item['color'] = '#f1d6ff'
                count_skip += 1
            list_result.append(dict_item)
            list_vers = list(sorted(t.versions, key=lambda x: x.date_version))[:10]
            for v in list_vers:
                dict_item = {}
                dict_item['text'] = f'{v.index} - {v.text} - {v.date_version.strftime("%H:%M:%S")}'
                dict_item['color'] = get_bg_color(v.index)
                list_result.append(dict_item)
            list_result.append({'text': '---', 'color': '#ffffff'})

        data = {'statistics': f'{user.username} 🚪{len(tryings)} / ✅{len(list_count_vers)} / ⏭{count_skip} /'
                              f' mean📦{round(np.mean(list_count_vers), 2)} / '
                              f'med📦{round(np.median(list_count_vers), 2)}'}
        data['result'] = list_result
        return data


async def check_word_facts(word_id):
    async with get_session() as session:
        result_f = await session.execute(select(WordFact).filter_by(word_id=word_id))
        word_facts = result_f.scalars().all()

        result_h = await session.execute(select(HintPixel).filter_by(word_id=word_id))
        hint_pixel = result_h.scalars().first()

        types = set(fact.type for fact in word_facts)
        fact = ''
        if 'text' in types:
            result_tf = await session.execute(select(WordFact).filter_by(word_id=word_id, type='text'))
            text_fact = result_tf.scalar_one()

            if text_fact.fact == '🤖':
                fact = '🤖'
            else:
                fact ='📜'
    return ''.join([fact, '🖼' if 'photo' in types else '', '🖌' if hint_pixel else ''])
