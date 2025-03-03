from func import *
from model import *

from xgboost import XGBClassifier
from scipy.stats import kurtosis, skew


async def check_control_al(curr_trying, model, trying_versions=False):
    (list_vers100, list_times100, distr_vers15, distr_times15, count_versions, count_hint_step,
     count_hint_allusion, count_hint_center, hint_pixel, hint_bomb, hint_tail, hint_metr,
     mean_count_vers, mean_time, median_count_vers, median_time, kurtosis_count_vers, kurtosis_time,
     skewness_count_vers, skewness_time, mean_count_vers_user, mean_time_user, median_count_vers_user,
     median_time_user, kurtosis_count_vers_user, kurtosis_time_user, skewness_count_vers_user,
     skewness_time_user, all_time) = await get_control_params(curr_trying, trying_versions)
    param = json.loads(list_vers100) + json.loads(list_times100) + json.loads(distr_vers15) + json.loads(distr_times15)
    param.append(count_versions)
    param.append(count_hint_step)
    param.append(count_hint_allusion)
    param.append(count_hint_center)
    param.append(hint_pixel)
    param.append(hint_bomb)
    param.append(hint_tail)
    param.append(hint_metr)
    param.append(mean_count_vers)
    param.append(mean_time)
    param.append(median_count_vers)
    param.append(median_time)
    param.append(kurtosis_count_vers)
    param.append(kurtosis_time)
    param.append(skewness_count_vers)
    param.append(skewness_time)
    param.append(mean_count_vers_user)
    param.append(mean_time_user)
    param.append(median_count_vers_user)
    param.append(median_time_user)
    param.append(kurtosis_count_vers_user)
    param.append(kurtosis_time_user)
    param.append(skewness_count_vers_user)
    param.append(skewness_time_user)
    param.append(all_time)
    param_test = np.array([param])
    mark = model.predict(param_test)
    probability = model.predict_proba(param_test)

    return mark[0], probability[0]


async def get_control_params(trying, trying_versions=False):
    async with get_session() as session:

        result_v = await session.execute(select(Version).filter_by(trying_id=trying.id).order_by(Version.date_version))
        versions = result_v.scalars().all()

        result_ha = await session.execute(select(func.count()).select_from(HintMainVers).join(Version).filter(
            Version.trying_id == trying.id,
            HintMainVers.hint_type == 'allusion'
        ))
        count_hint_allusion = result_ha.scalar_one()

        result_hc = await session.execute(select(func.count()).select_from(HintMainVers).join(Version).filter(
            Version.trying_id == trying.id,
            HintMainVers.hint_type == 'center'
        ))
        count_hint_center = result_hc.scalar_one()

        if not trying_versions:
            result_uv = await session.execute(select(Trying).options(selectinload(Trying.versions)).filter(
                Trying.word_id == trying.word_id,
                Trying.done == True
            ))
            trying_versions = result_uv.scalars().all()

        result_ut = await session.execute(select(Trying).options(selectinload(Trying.versions)).filter(
            Trying.user_id == trying.user_id,
            Trying.done == True
        ))
        user_trying = result_ut.scalars().all()

        result_hp = await session.execute(select(func.count()).select_from(HintMainWord).filter_by(trying_id=trying.id, hint_type='pixel'))
        hint_pixel = result_hp.scalar_one()

        result_hb = await session.execute(select(func.count()).select_from(HintMainWord).filter_by(trying_id=trying.id, hint_type='bomb'))
        hint_bomb = result_hb.scalar_one()

        result_ht = await session.execute(select(func.count()).select_from(HintMainWord).filter_by(trying_id=trying.id, hint_type='tail'))
        hint_tail = result_ht.scalar_one()

        result_hm = await session.execute(select(func.count()).select_from(HintMainWord).filter_by(trying_id=trying.id, hint_type='metr'))
        hint_metr = result_hm.scalar_one()

    list_vers = [v.index for v in versions]
    list_times = [(versions[i+1].date_version - versions[i].date_version).total_seconds() for i in range(len(versions) - 1)]
    list_vers100 = json.dumps(interpolate_list(list_vers))
    list_times100 = json.dumps(interpolate_list(list_times)) if list_times else json.dumps([0 for _ in range(100)])
    distr_vers15 = json.dumps(get_distribution(list_vers, 5))
    distr_times15 = json.dumps(get_distribution(list_times, 5)) if list_times else json.dumps([0 for _ in range(5)])
    count_versions = len(versions)
    count_hint_step = trying.hint

    all_time = (trying.date_done - trying.date_trying).total_seconds()

    count_vers = [len(t.versions) for t in trying_versions if t.date_done < trying.date_done]
    times = [(t.date_done - t.date_trying).total_seconds() for t in trying_versions if t.date_done < trying.date_done]
    user_count_vers = [len(t.versions) for t in user_trying]
    user_times = [(t.date_done - t.date_trying).total_seconds() for t in user_trying]

    mean_count_vers = np.mean(count_vers)
    mean_time = np.mean(times)
    median_count_vers = np.median(count_vers)
    median_time = np.median(times)
    kurtosis_count_vers = kurtosis(count_vers)
    kurtosis_time = kurtosis(times)
    skewness_count_vers = skew(count_vers)
    skewness_time = skew(times)

    mean_count_vers_user = np.mean(user_count_vers)
    mean_time_user = np.mean(user_times)
    median_count_vers_user = np.median(user_count_vers)
    median_time_user = np.median(user_times)
    kurtosis_count_vers_user = kurtosis(user_count_vers)
    kurtosis_time_user = kurtosis(user_times)
    skewness_count_vers_user = skew(user_count_vers)
    skewness_time_user = skew(user_times)

    mean_count_vers = 0 if np.isnan(mean_count_vers) else mean_count_vers
    mean_time = 0 if np.isnan(mean_time) else mean_time
    median_count_vers = 0 if np.isnan(median_count_vers) else median_count_vers
    median_time = 0 if np.isnan(median_time) else median_time
    kurtosis_count_vers = 0 if np.isnan(kurtosis_count_vers) else kurtosis_count_vers
    kurtosis_time = 0 if np.isnan(kurtosis_time) else kurtosis_time
    skewness_count_vers = 0 if np.isnan(skewness_count_vers) else skewness_count_vers
    skewness_time = 0 if np.isnan(skewness_time) else skewness_time

    mean_count_vers_user = 0 if np.isnan(mean_count_vers_user) else mean_count_vers_user
    mean_time_user = 0 if np.isnan(mean_time_user) else mean_time_user
    median_count_vers_user = 0 if np.isnan(median_count_vers_user) else median_count_vers_user
    median_time_user = 0 if np.isnan(median_time_user) else median_time_user
    kurtosis_count_vers_user = 0 if np.isnan(kurtosis_count_vers_user) else kurtosis_count_vers_user
    kurtosis_time_user = 0 if np.isnan(kurtosis_time_user) else kurtosis_time_user
    skewness_count_vers_user = 0 if np.isnan(skewness_count_vers_user) else skewness_count_vers_user
    skewness_time_user = 0 if np.isnan(skewness_time_user) else skewness_time_user

    return (list_vers100, list_times100, distr_vers15, distr_times15, count_versions, count_hint_step,
            count_hint_allusion, count_hint_center, hint_pixel, hint_bomb, hint_tail, hint_metr,
            mean_count_vers, mean_time, median_count_vers, median_time, kurtosis_count_vers, kurtosis_time,
            skewness_count_vers, skewness_time, mean_count_vers_user, mean_time_user, median_count_vers_user,
            median_time_user, kurtosis_count_vers_user, kurtosis_time_user, skewness_count_vers_user,
            skewness_time_user, all_time)


def interpolate_list(lst):
    # Преобразуем список в массив NumPy
    arr = np.array(lst)

    # Создаем равномерное разбиение от 0 до длины исходного списка
    x = np.linspace(0, len(lst) - 1, len(lst))

    # Создаем равномерное разбиение от 0 до 99 для создания нового списка из 100 чисел
    new_x = np.linspace(0, len(lst) - 1, 100)

    # Интерполируем значения для новых точек
    new_y = np.interp(new_x, x, arr)

    # Преобразуем массив NumPy обратно в список
    new_list = list(new_y)

    return new_list


def get_distribution(values: list, n: int) -> list:
    # Находим минимальное и максимальное значения в наборе данных
    min_val = min(values)
    max_val = max(values)
    # Вычисляем размер интервала
    interval = (max_val - min_val) / n
    if interval == 0:
        return [len(values)] + [0] * (n - 1)
    # Создаем список, который будет содержать количество значений в каждом интервале
    distribution = [0] * n
    # Итерируем по значениям и распределяем их по соответствующему интервалу
    for value in values:
        index = int((value - min_val) / interval)
        # Если значение попадает в последний интервал, то оно приравнивается к последнему интервалу
        if index == n:
            index -= 1
        distribution[index] += 1
    # Возвращаем количество значений в каждом интервале
    return distribution
