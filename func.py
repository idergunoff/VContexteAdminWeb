import json

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