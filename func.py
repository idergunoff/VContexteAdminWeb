import json
import datetime

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


async def get_trying_by_word(word_id: int):
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

                dict_result[u.id]['title'] = (f'📆{u.date_register.strftime("%d-%m-%Y")}\n'
                                              f'✨{u.coin[0].coin}')

                dict_result[u.id]['t_id'] = t.id

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

        dict_all = {
            "word": word.word,
            "date_play": word.date_play.strftime('%d.%m.%Y'),
            "dict_result": dict_result
        }

    return dict_all
