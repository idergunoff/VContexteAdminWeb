import json
import datetime

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import kurtosis, skew, gaussian_kde

import numpy as np

from func import get_username
from model import *


async def graph_duel_versions_plotly(duel):
    """Generate HTML for duel versions graph using Plotly."""
    async with get_session() as session:
        result = await session.execute(
            select(DuelVersion, User.username)
            .join(User, DuelVersion.user_id == User.id)
            .filter(DuelVersion.duel_id == duel.id)
            .order_by(DuelVersion.ts)
        )
        rows = result.all()

    players = []
    for _, name in rows:
        if name not in players:
            players.append(name)

    colors = ["blue", "red"]
    color_map = {name: colors[i % len(colors)] for i, name in enumerate(players)}

    data = {name: {"x": [], "y": [], "text": [], "delta_rank": []} for name in players}
    for dv, name in rows:

        data[name]["x"].append(dv.ts)
        data[name]["y"].append(dv.idx_global)
        data[name]["text"].append(dv.text)
        data[name]["delta_rank"].append(dv.delta_rank)

    fig = go.Figure()

    for name in players:
        color = color_map.get(name, "blue")
        y_vals = [y if y > 0 else 1 for y in data[name]["y"]]

        marker_colors = [
            "yellow" if (d is not None and d > 0) else color
            for d in data[name]["delta_rank"]
        ]
        marker_sizes = [
            12 if (d is not None and d > 0) else 8
            for d in data[name]["delta_rank"]
        ]
        customdata = [
            f"Δrank: {d}" if (d is not None and d > 0) else ""
            for d in data[name]["delta_rank"]
        ]

        fig.add_trace(
            go.Scatter(
                x=data[name]["x"],
                y=y_vals,

                mode="lines+markers",
                marker=dict(color=marker_colors, size=marker_sizes),
                line=dict(color=color),
                name=name,
                text=data[name]["text"],
                customdata=customdata,
                hovertemplate="Слово: %{text}<br>Индекс: %{y}<br>Игрок: "
                + name
                + "<br>%{customdata}",

            )
        )

    fig.update_yaxes(type="log")

    return fig.to_html(full_html=True, include_plotlyjs="cdn")


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


async def draw_graph_word(word_id):
    async with get_session() as session:
        result_t = await session.execute(select(Trying).options(selectinload(Trying.versions)).filter_by(
            word_id=word_id, done=True
        ).order_by(desc(Trying.date_done)))
        tryings = result_t.scalars().all()

        result_tha = await session.execute(select(HintMainVers.id, Trying.id).join(
            Version, HintMainVers.version_id == Version.id
        ).join(Trying, Version.trying_id == Trying.id).filter(
            Trying.word_id == word_id,
            HintMainVers.hint_type == 'allusion'
        ))
        hint_allusion = result_tha.all()
        list_ha = [h[1] for h in hint_allusion]

        result_thc = await session.execute(select(HintMainVers.id, Trying.id).join(
            Version, HintMainVers.version_id == Version.id
        ).join(Trying, Version.trying_id == Trying.id).filter(
            Trying.word_id == word_id,
            HintMainVers.hint_type == 'center'
        ))
        hint_center = result_thc.all()
        list_hc = [h[1] for h in hint_center]

        result_thb = await session.execute(select(HintMainWord.id, Trying.id).join(
            Trying, HintMainWord.trying_id == Trying.id
        ).filter(
            Trying.word_id == word_id,
            HintMainWord.hint_type == 'bomb'
        ))
        hint_bomb = result_thb.all()
        list_hb = [h[1] for h in hint_bomb]

        result_tht = await session.execute(select(HintMainWord.id, Trying.id).join(
            Trying, HintMainWord.trying_id == Trying.id
        ).filter(
            Trying.word_id == word_id,
            HintMainWord.hint_type == 'tail'
        ))
        hint_tail = result_tht.all()
        list_ht = [h[1] for h in hint_tail]

        result_thm = await session.execute(select(HintMainWord.id, Trying.id).join(
            Trying, HintMainWord.trying_id == Trying.id
        ).filter(
            Trying.word_id == word_id,
            HintMainWord.hint_type == 'metr'
        ))
        hint_metr = result_thm.all()
        list_hm = [h[1] for h in hint_metr]

        result_thp = await session.execute(select(HintMainWord.id, Trying.id).join(
            Trying, HintMainWord.trying_id == Trying.id
        ).filter(
            Trying.word_id == word_id,
            HintMainWord.hint_type == 'pixel'
        ))
        hint_pixel = result_thp.all()
        list_hp = [h[1] for h in hint_pixel]

    list_time_done = [t.date_done for t in tryings]
    list_count_vers = [len(t.versions) for t in tryings]
    list_time_try = [(t.date_done - t.date_trying).total_seconds() / 3600 for t in tryings]
    list_user = [await get_username(t.user_id) for t in tryings]
    list_hint = [t.hint for t in tryings]
    list_skip = [t.date_done for t in tryings if t.skip]
    list_allusion, list_center, list_bomb, list_tail, list_metr, list_pixel = [], [], [], [], [], []
    for t in tryings:
        list_allusion.append(list_ha.count(t.id))
        list_center.append(list_hc.count(t.id))
        list_bomb.append(list_hb.count(t.id))
        list_tail.append(list_ht.count(t.id))
        list_metr.append(list_hm.count(t.id))
        list_pixel.append(list_hp.count(t.id))

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Количество версий", "Время угадывания"), vertical_spacing=0.05)

    fig.add_trace(go.Scatter(
        x=list_time_done,
        y=list_count_vers,
        mode='lines+markers',
        marker=dict(color='blue', size=10),
        hovertext=[
            f'{u}\n{"🧿" + str(h) if h else ""}'
            f'{"💎" + str(a) if a else ""}'
            f'{"🌎" + str(c) if c else ""}'
            f'{"💣" if b else ""}'
            f'{"🦎" if t else ""}'
            f' {"📏" if m else ""}'
            f'{"🖼" if p else ""}'
            for h, a, c, b, t, m, p, u in zip(list_hint, list_allusion, list_center, list_bomb, list_tail, list_metr, list_pixel, list_user)
        ],
        name='Количество версий'
    ), row=1, col=1)

    for s in list_skip:
        fig.add_vline(
            x= s.timestamp() * 1000,  # Преобразуем в миллисекунды для Plotly
            line=dict(color="red", width=2, dash="dash"),
            name="Skip",
            row=1, col=1
        )

    fig.add_trace(go.Scatter(
        x=list_time_done,
        y=list_time_try,
        mode='lines+markers',
        marker=dict(color='orange', size=10),
        hovertext=[
            f'{u}\n{"🧿" + str(h) if h else ""}'
            f'{"💎" + str(a) if a else ""}'
            f'{"🌎" + str(c) if c else ""}'
            f'{"💣" if b else ""}'
            f'{"🦎" if t else ""}'
            f' {"📏" if m else ""}'
            f'{"🖼" if p else ""}'
            for h, a, c, b, t, m, p, u in zip(list_hint, list_allusion, list_center, list_bomb, list_tail, list_metr, list_pixel, list_user)
        ],
        name='Время угадывания (ч)'
    ), row=2, col=1)

    for s in list_skip:
        fig.add_vline(
            x= s.timestamp() * 1000,  # Преобразуем в миллисекунды для Plotly
            line=dict(color="red", width=2, dash="dash"),
            name="Skip",
            row=2, col=1
        )

    # Добавляем "фейковый" след для легенды
    fig.add_trace(go.Scatter(
        x=[None],  # Пустые координаты, чтобы линия не рисовалась на графике
        y=[None],
        mode='lines',
        line=dict(color="red", width=2, dash="dash"),
        name="Skip"
    ))

    return fig.to_html(full_html=True, include_plotlyjs="cdn")


async def draw_distr_trying(word_id):
    async with get_session() as session:
        result_t = await session.execute(select(Trying).options(selectinload(Trying.versions)).filter_by(
            word_id=word_id, done=True, skip=False
        ))
        tryings = result_t.scalars().all()

    list_count_vers = [len(t.versions) for t in tryings]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Гистограмма (количество наблюдений)
    fig.add_trace(go.Histogram(
        x=list_count_vers,
        nbinsx=max(10, int(len(set(list_count_vers)) / 2)),  # Количество бинов
        marker=dict(color='blue', opacity=0.6),
        name='Распределение версий'
    ), secondary_y=False)

    # Плотность распределения (KDE)
    if len(list_count_vers) > 1:
        density = gaussian_kde(list_count_vers)
        x_vals = np.linspace(min(list_count_vers), max(list_count_vers), 100)
        y_vals = density(x_vals)  # Плотность вероятности
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            mode='lines',
            line=dict(color='red', width=2),
            name='Плотность распределения'
        ), secondary_y=True)

    fig.update_layout(
        title="Распределение количества версий",
        xaxis_title="Количество версий",
        yaxis_title="Частота",
        yaxis2_title="Плотность вероятности",
        bargap=0.2
    )

    return fig.to_html(full_html=True, include_plotlyjs="cdn")


async def draw_distr_ai_trying(word_id):
    async with get_session() as session:
        result_t = await session.execute(select(Trying).options(selectinload(Trying.versions)).filter_by(
            word_id=word_id, done=True, skip=False
        ))
        tryings = result_t.scalars().all()

        result_ai = await session.execute(select(AITrying).filter_by(word_id=word_id).order_by(AITrying.id))
        ai_entries = result_ai.scalars().all()

    list_count_vers = [len(t.versions) for t in tryings]
    list_count_ai = []
    for entry in ai_entries:
        try:
            idx_list = json.loads(entry.idx) if entry.idx else []
        except json.JSONDecodeError:
            idx_list = []
        list_count_ai.append(len(idx_list))

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=False,
        subplot_titles=(
            "Распределение количества версий (основные попытки)",
            "Распределение количества попыток (AITrying)"
        ),
        vertical_spacing=0.08,
        specs=[[{"secondary_y": True}], [{"secondary_y": True}]]
    )

    fig.add_trace(go.Histogram(
        x=list_count_vers,
        nbinsx=max(10, int(len(set(list_count_vers)) / 2)) if list_count_vers else 10,
        marker=dict(color='blue', opacity=0.6),
        name='Распределение версий'
    ), row=1, col=1, secondary_y=False)

    if len(list_count_vers) > 1:
        density = gaussian_kde(list_count_vers)
        x_vals = np.linspace(min(list_count_vers), max(list_count_vers), 100)
        y_vals = density(x_vals)
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            mode='lines',
            line=dict(color='red', width=2),
            name='Плотность (версии)'
        ), row=1, col=1, secondary_y=True)

    fig.add_trace(go.Histogram(
        x=list_count_ai,
        nbinsx=max(10, int(len(set(list_count_ai)) / 2)) if list_count_ai else 10,
        marker=dict(color='green', opacity=0.6),
        name='Распределение AITrying'
    ), row=2, col=1, secondary_y=False)

    if len(list_count_ai) > 1:
        density = gaussian_kde(list_count_ai)
        x_vals = np.linspace(min(list_count_ai), max(list_count_ai), 100)
        y_vals = density(x_vals)
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            mode='lines',
            line=dict(color='orange', width=2),
            name='Плотность (AITrying)'
        ), row=2, col=1, secondary_y=True)

    fig.update_layout(
        title="Распределения по количеству попыток",
        bargap=0.2
    )
    fig.update_xaxes(title_text="Количество версий", row=1, col=1)
    fig.update_xaxes(title_text="Количество попыток (AITrying)", row=2, col=1)
    fig.update_yaxes(title_text="Частота", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Плотность вероятности", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Частота", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Плотность вероятности", row=2, col=1, secondary_y=True)

    return fig.to_html(full_html=True, include_plotlyjs="cdn")


async def draw_graph_ai_trying(ai_trying_id):
    async with get_session() as session:
        result_ai = await session.execute(select(AITrying).filter_by(id=ai_trying_id))
        entry = result_ai.scalars().first()

    if not entry:
        fig = go.Figure()
        fig.update_layout(title="AITrying запись не найдена")
        return fig.to_html(full_html=True, include_plotlyjs="cdn")

    try:
        idx_list = json.loads(entry.idx) if entry.idx else []
    except json.JSONDecodeError:
        idx_list = []

    x_vals = list(range(1, len(idx_list) + 1))
    y_vals = [val if val > 0 else 1 for val in idx_list]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='lines+markers',
        marker=dict(color='blue', size=6),
        line=dict(color='blue', width=2),
        name='AITrying'
    ))

    fig.update_layout(
        title="График попытки AITrying",
        xaxis_title="Шаг",
        yaxis_title="Индекс (логарифмическая шкала)"
    )
    fig.update_yaxes(type="log")

    return fig.to_html(full_html=True, include_plotlyjs="cdn")
