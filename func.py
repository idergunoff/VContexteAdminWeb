import json
import datetime
import requests

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import kurtosis, skew

import numpy as np

from connect import TOKEN_BOT
from model import *


async def get_username(user_id: int):
    async with get_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalar_one()
        return user.username


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

        result_ua = await session.execute(select(UserAlpha))
        users_alpha = result_ua.scalars().all()
        list_alpha = [user_alpha.user_id for user_alpha in users_alpha]

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

        result_rc = await session.execute(select(ReferralCode).options(selectinload(ReferralCode.referral_user)))
        ref_code = result_rc.scalars().all()

        result_ru = await session.execute(select(ReferralUser).options(selectinload(ReferralUser.referral_code)))
        ref_user = result_ru.scalars().all()

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

        result_hvb = await session.execute(
            select(Trying).join(HintMainWord)
            .filter(Trying.word_id == word_id, HintMainWord.hint_type == 'bomb'))
        hint_word_bomb = result_hvb.scalars().all()

        result_htt = await session.execute(
            select(TryingTopTen).join(HintTopTen)
            .filter(TryingTopTen.word_id == word_id))
        hint_top_ten = result_htt.scalars().all()

        result_ut = await session.execute(select(UserTransaction).filter(
            UserTransaction.date_trans >= word.date_play,
            UserTransaction.date_trans < (word.date_play + datetime.timedelta(days=1))))
        user_trans = result_ut.scalars().all()


    count_user, count_done, count_tt_done, count_new_user, count_not_hint, list_count_vers = 0, 0, 0, 0, 0, []
    if word:
        for u in users:
            t = next((t for t in tryings if t.user_id == u.id), None)
            if t:
                count_user += 1
                ud = next((i for i in user_day if i.id == u.id), None)
                ha = [i for i in hint_allusion if i.user_id == u.id]
                hc = [i for i in hint_center if i.user_id == u.id]
                hw = next((i for i in hint_word_pixel if i.user_id == u.id), None)
                ht = next((i for i in hint_word_tail if i.user_id == u.id), None)
                hm = next((i for i in hint_word_metr if i.user_id == u.id), None)
                hb = next((i for i in hint_word_bomb if i.user_id == u.id), None)
                ua = u.id in list_alpha
                rc = next((i for i in ref_code if i.user_id == u.id), None)
                ru = next((i for i in ref_user if i.user_id == u.id), None)

                if not t.hint and not ha and not hc and not hw and not ht and not hm and not hb:
                    count_not_hint += 1
                if ud:
                    count_new_user += 1

                dict_result[u.id] = {}
                dict_result[u.id]['text'] = (f'{"👑" if ua else ""}'
                                             f'{"🕺" if ud else ""}'
                                             f'<b>{u.username}</b> (id {u.id}) - 📦{len(t.versions)}'
                                             f'{" 🧿" + str(t.hint) if t.hint > 0 else ""}'
                                             f'{" 💎" + str(len(ha)) if ha else ""}'
                                             f'{" 🌎" + str(len(hc)) if hc else ""}'
                                             f'{" 🖼" if hw else ""}{" 🦎" if ht else ""}{" 📏" if hm else ""}'
                                             f'{" 💣" if hb else ""}')
                try:
                    dict_result[u.id]['title'] = (f'📆{u.date_register.strftime("%d-%m-%Y")}\n'
                                                  f'✨{u.coin[0].coin}\n'
                                                  f'{"👥" + str(len(rc.referral_user)) if rc else ""}'
                                                  f'{"🔗" + await get_username(ru.referral_code.user_id) if ru else ""}\n')
                except IndexError:
                    async with get_session() as session:
                        session.add(UserCoin(user_id=u.id, coin=521))
                    dict_result[u.id]['title'] = f'📆{u.date_register.strftime("%d-%m-%Y")}\n'

                dict_result[u.id]['t_id'] = t.id
                dict_result[u.id]['u_id'] = u.id
                dict_result[u.id]['date_start'] = t.date_trying
                dict_result[u.id]['date_done'] = t.date_done

                dict_result[u.id]['color'] = '#bfffbf' if t.done else '#f7faa6'
                if t.done:
                    count_done += 1
                    if not t.skip:
                        list_count_vers.append(len(t.versions))
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
                    count_tt_done += 1

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

        plus_trans, minus_trans = 0, 0
        for ut in user_trans:
            if ut.amount > 0:
                plus_trans += ut.amount
            else:
                minus_trans += ut.amount

        if len(list_count_vers) == 0:
            min_vers = med_vers = skew_vers = kurt_vers = 0
        else:
            min_vers, med_vers, skew_vers, kurt_vers = (round(np.min(list_count_vers), 2), round(np.median(list_count_vers), 2),
                                                    round(skew(list_count_vers), 2), round(kurtosis(list_count_vers), 2))
        text_header = (f'<div>{word.word} {word.date_play.strftime("%d.%m.%Y")}</div>'
                       f'<div>🙂{count_user} - 🎯{count_done} - 🏆{count_tt_done}</div>'
                       f'<div>🆕{count_new_user} - 🚫💡{count_not_hint} - 💰{plus_trans}/{minus_trans}</div>'
                       f'<div>🔢{min_vers}/{med_vers} - 📈{skew_vers}/{kurt_vers}</div>')
        dict_all = {
            "word": word.word,
            "date_play": word.date_play.strftime('%d.%m.%Y'),
            "word_id": word.id,
            "text_header": text_header,
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


async def get_dict_fact(word_id):
    word_id = int(word_id)
    async with get_session() as session:
        result_ft = await session.execute(select(WordFact).filter_by(word_id=word_id, type='text'))
        word_fact_text = result_ft.scalars().first()

        result_fph = await session.execute(select(WordFact).filter_by(word_id=word_id, type='photo'))
        word_fact_photo = result_fph.scalars().first()

        result_h = await session.execute(select(HintPixel).filter_by(word_id=word_id))
        hint_pixel = result_h.scalars().first()

        result_w = await session.execute(select(Word.word).filter_by(id=word_id))
        word = result_w.scalars().first()

    dict_fact = {}
    dict_fact['text'] = word_fact_text.fact if word_fact_text else ''
    dict_fact['photo'] = await get_link_photo_tg(word_fact_photo.fact) if word_fact_photo else 0
    dict_fact['pixel'] = await get_link_photo_tg(hint_pixel.pixel) if hint_pixel else 0
    dict_fact['picture'] = await get_link_photo_tg(hint_pixel.picture) if hint_pixel else 0
    dict_fact['word'] = word

    return dict_fact


async def get_link_photo_tg(link_photo):
    file = requests.get('https://api.telegram.org/bot' + TOKEN_BOT + '/getFile?file_id=' + link_photo).json()['result']
    file_path = file['file_path']
    download_url = 'https://api.telegram.org/file/bot' + TOKEN_BOT + '/' + file_path
    return download_url
