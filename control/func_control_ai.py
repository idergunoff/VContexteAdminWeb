import pickle
import os
import shutil

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_curve, auc
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from tqdm import tqdm
import numpy as np
from xgboost import XGBClassifier
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from control.control_ai import get_control_params
from control.model_control import *
from model import *

feature_names = (
    [f'versions_{i}' for i in range(100)] +
    [f'times_{i}' for i in range(100)] +
    [f'distr_vers_{i}' for i in range(5)] +
    [f'distr_times_{i}' for i in range(5)] +
    [
        'count_vers',
        'count_hint_step',
        'count_hint_allusion',
        'count_hint_center',
        'hint_pixel',
        'hint_bomb',
        'hint_tail',
        'hint_metr',
        'hint_crash',
        'mean_count_vers',
        'mean_time',
        'median_count_vers',
        'median_time',
        'kurtosis_count_vers',
        'kurtosis_time',
        'skewness_count_vers',
        'skewness_time',
        'mean_count_vers_user',
        'mean_time_user',
        'median_count_vers_user',
        'median_time_user',
        'kurtosis_count_vers_user',
        'kurtosis_time_user',
        'skewness_count_vers_user',
        'skewness_time_user',
        'all_time'
    ]
)


async def get_update_list_trying_train():
    """ Обновляет список тренировочных попыток """
    trying_true = session_ctrl_ai.query(TryingTrainControl).filter_by(honestly=True).all()
    trying_false = session_ctrl_ai.query(TryingTrainControl).filter_by(honestly=False).all()
    data = {}
    data['list_true'] = []
    data['list_false'] = []
    for i in trying_true:
        data['list_true'].append([f'{i.username} {i.word}\n{i.date_trying.strftime("%d.%m.%Y %H:%M:%S")}', i.trying_id])

    for i in trying_false:
        data['list_false'].append([f'{i.username} {i.word}\n{i.date_trying.strftime("%d.%m.%Y %H:%M:%S")}', i.trying_id])

    data['count_true'] = len(trying_true)
    data['count_false'] = len(trying_false)
    return data


async def add_trying_to_model(honestly, trying_id):
    msg = ''
    async with get_session() as session:
        result_t = await session.execute(select(Trying).filter_by(id=trying_id))
        trying = result_t.scalar_one()

        result_w = await session.execute(select(Word.word).filter_by(id=trying.word_id))
        word = result_w.scalar_one()

        result_u = await session.execute(select(User).filter_by(id=trying.user_id))
        user = result_u.scalar_one()

    trying_ctrl = session_ctrl_ai.query(TryingTrainControl).filter_by(trying_id=trying.id).first()
    if trying_ctrl:
        if trying_ctrl.honestly == True and honestly == False:
            session_ctrl_ai.query(ParamControl).filter_by(trying_train_id=trying_ctrl.id).delete()
            session_ctrl_ai.delete(trying_ctrl)
            session_ctrl_ai.commit()
            msg += f'Попытка #{trying_id} удалена из класса TRUE'
        else:
            msg += f'Попытка #{trying_id} уже добавлена в обучающую выборку.'
            return msg

    (list_vers100, list_times100, distr_vers15, distr_times15, count_versions, count_hint_step,
     count_hint_allusion, count_hint_center, hint_pixel, hint_bomb, hint_tail, hint_metr, hint_crash,
     mean_count_vers, mean_time, median_count_vers, median_time, kurtosis_count_vers, kurtosis_time,
     skewness_count_vers, skewness_time, mean_count_vers_user, mean_time_user, median_count_vers_user,
     median_time_user, kurtosis_count_vers_user, kurtosis_time_user, skewness_count_vers_user,
     skewness_time_user, all_time) = await get_control_params(trying, trying_versions=False)

    new_trying = TryingTrainControl(
        model_id=1,
        honestly=honestly,
        trying_id=trying.id,
        date_trying=trying.date_done,
        word=word,
        username=user.username
    )

    session_ctrl_ai.add(new_trying)
    session_ctrl_ai.commit()

    new_param = ParamControl(
        trying_train_id=new_trying.id,
        versions=list_vers100,
        times=list_times100,
        distr_vers=distr_vers15,
        distr_times=distr_times15,
        count_vers=count_versions,
        count_hint_step=count_hint_step,
        count_hint_allusion=count_hint_allusion,
        count_hint_center=count_hint_center,
        hint_pixel=hint_pixel,
        hint_bomb=hint_bomb,
        hint_tail=hint_tail,
        hint_metr=hint_metr,
        hint_crash=hint_crash,
        mean_count_vers=mean_count_vers,
        mean_time=mean_time,
        median_count_vers=median_count_vers,
        median_time=median_time,
        kurtosis_count_vers=kurtosis_count_vers,
        kurtosis_time=kurtosis_time,
        skewness_count_vers=skewness_count_vers,
        skewness_time=skewness_time,
        mean_count_vers_user=mean_count_vers_user,
        mean_time_user=mean_time_user,
        median_count_vers_user=median_count_vers_user,
        median_time_user=median_time_user,
        kurtosis_count_vers_user=kurtosis_count_vers_user,
        kurtosis_time_user=kurtosis_time_user,
        skewness_count_vers_user=skewness_count_vers_user,
        skewness_time_user=skewness_time_user,
        all_time=all_time
    )
    session_ctrl_ai.add(new_param)
    session_ctrl_ai.commit()

    msg += f' Попытка #{trying_id} добавлена в обучающую выборку'

    return msg


async def rm_trying_from_model(trying_id):
    trying_ctrl = session_ctrl_ai.query(TryingTrainControl).filter_by(trying_id=trying_id).first()
    session_ctrl_ai.query(ParamControl).filter_by(trying_train_id=trying_ctrl.id).delete()
    session_ctrl_ai.delete(trying_ctrl)
    session_ctrl_ai.commit()

    return f'Попытка #{trying_id} удалена из обучающей выборки'


async def auto_add_trying(honestly: bool, count_trying):
    list_true_id = [i.trying_id for i in session_ctrl_ai.query(TryingTrainControl).filter_by(honestly=True).all()]
    list_false_id = [i.trying_id for i in session_ctrl_ai.query(TryingTrainControl).filter_by(honestly=False).all()]

    async with get_session() as session:
        result = await session.execute(select(Trying).options(selectinload(Trying.versions)).filter(
            Trying.done == True, Trying.skip != honestly).order_by(func.random()).limit(count_trying))
        new_tryings = result.scalars().all()

    count_add_trying, count_rm_true = 0, 0

    for t in tqdm(new_tryings):
        if len(t.versions) == 1 or (len(t.versions) >= 200 and not honestly):
            continue
        if honestly:
            if t.id not in list_true_id:
                await add_trying_to_model(honestly, t.id)
                count_add_trying += 1
        else:
            if t.id not in list_false_id:
                if t.id in list_true_id:
                    await rm_trying_from_model(t.id)
                    count_rm_true += 1
                await add_trying_to_model(honestly, t.id)
                count_add_trying += 1

    return f'В класс {str(honestly)} добавлено {count_add_trying} попыток{ " из класса TRUE удалено " + str(count_rm_true) if not honestly else ""}.'



async def build_table_train():
    """ Построение таблицы модели контроля """
    list_param, list_mark = [], []
    for t in session_ctrl_ai.query(TryingTrainControl).options(selectinload(TryingTrainControl.param)).all():
        list_mark.append(t.honestly)
        param = json.loads(t.param.versions) + json.loads(t.param.times) + json.loads(t.param.distr_vers) + json.loads(t.param.distr_times)
        param.append(t.param.count_vers)
        param.append(t.param.count_hint_step)
        param.append(t.param.count_hint_allusion)
        param.append(t.param.count_hint_center)

        param.append(t.param.hint_pixel)
        param.append(t.param.hint_bomb)
        param.append(t.param.hint_tail)
        param.append(t.param.hint_metr)
        param.append(t.param.hint_crash)

        param.append(t.param.mean_count_vers)
        param.append(t.param.mean_time)
        param.append(t.param.median_count_vers)
        param.append(t.param.median_time)
        param.append(t.param.kurtosis_count_vers)
        param.append(t.param.kurtosis_time)
        param.append(t.param.skewness_count_vers)
        param.append(t.param.skewness_time)

        param.append(t.param.mean_count_vers_user)
        param.append(t.param.mean_time_user)
        param.append(t.param.median_count_vers_user)
        param.append(t.param.median_time_user)
        param.append(t.param.kurtosis_count_vers_user)
        param.append(t.param.kurtosis_time_user)
        param.append(t.param.skewness_count_vers_user)
        param.append(t.param.skewness_time_user)

        param.append(t.param.all_time)

        list_param.append(param)
    return np.array(list_param) , np.array(list_mark)


async def train_model():
    msg = ''
    training_sample, mark = await build_table_train()
    training_sample_train, training_sample_test, markup_train, markup_test = train_test_split(
        training_sample, mark, test_size=0.20, random_state=0, stratify=mark)
    smote = SMOTE(random_state=0)
    training_sample_train, markup_train = smote.fit_resample(training_sample_train, markup_train)
    pipe_steps = []
    std_scaler = StandardScaler()
    pipe_steps.append(('std_scaler', std_scaler))
    model_class = XGBClassifier(n_estimators=1000, learning_rate=0.1, random_state=0)

    pipe_steps.append(('mlp', model_class))
    pipeline = Pipeline(pipe_steps)
    pipeline.fit(training_sample_train, markup_train)
    msg += f'Score on test: {pipeline.score(training_sample_test, markup_test)}<br>'
    msg += f'Score on train: {pipeline.score(training_sample_train, markup_train)}<br>'
    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

    scores_cv = cross_val_score(pipeline, training_sample, mark, cv=kf, n_jobs=-1)

    msg += f'CV scores: {" ;".join(map(lambda x: str(round(x, 3)), scores_cv))}<br>'
    msg += f'CV score: {round(np.mean(scores_cv), 3)} +/- {round(np.std(scores_cv), 3)}<br>'


    preds_train = pipeline.predict(training_sample)
    preds_t = pipeline.predict(training_sample_test)
    # msg += f'accuracy {accuracy_score(markup_test, preds_t, normalize=True)}<br>'
    # msg += f'precision {precision_score(markup_test, preds_t, average="binary")}<br>'
    # msg += f"recall {recall_score(markup_test, preds_t, average='binary')} <br>"
    # msg += f"f1 {f1_score(markup_test, preds_t, average='binary')} <br>"

    # --- ROC кривая ---
    preds_test = pipeline.predict_proba(training_sample_test)[:, 1]
    fpr, tpr, thresholds = roc_curve(markup_test, preds_test, pos_label=1)
    roc_auc = auc(fpr, tpr)

    # --- Кросс-валидация ---
    cv_x = list(range(1, len(scores_cv) + 1))
    cv_y = scores_cv

    # --- Важность признаков ---
    # XGBClassifier находится в pipeline как 'mlp'
    # if hasattr(training_sample, 'columns'):
    #     feature_names = training_sample.columns
    # else:
    #     feature_names = list(range(len(training_sample[0])))
    feature_importances = pipeline.named_steps['mlp'].feature_importances_
    feat_imp_sorted = sorted(zip(feature_importances, feature_names), reverse=True)
    feat_vals, feat_names = zip(*feat_imp_sorted)

    # --- Создаём Figure ---
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("ROC-кривая", "Кросс-валидация", "", "Важность признаков"),
        specs=[[{"type": "xy"}, {"type": "xy"}],
               [{"colspan": 2}, None]],  # снизу один график на две ячейки
        vertical_spacing=0.15,
        row_heights=[0.5, 0.5]
    )

    # ROC
    fig.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', name=f'ROC (AUC = {roc_auc:.2f})',
                             line=dict(width=3, color='darkorange')),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', name='Random', line=dict(dash='dash', color='navy')),
                  row=1, col=1)

    fig.update_xaxes(title_text='False Positive Rate', row=1, col=1)
    fig.update_yaxes(title_text='True Positive Rate', row=1, col=1)

    # Cross-validation
    fig.add_trace(go.Bar(x=cv_x, y=cv_y, name='CV Score'), row=1, col=2)
    fig.update_xaxes(title_text='Fold', row=1, col=2)
    fig.update_yaxes(title_text='Accuracy', row=1, col=2)

    n_top = 150
    fig.add_trace(go.Bar(
        x=[str(x) for x in feat_names[:n_top]],  # имена признаков по оси X
        y=feat_vals[:n_top],  # значения важности по оси Y
        name='Feature Importances',
        orientation='v'  # можно опустить, это значение по умолчанию
    ), row=2, col=1)

    fig.update_xaxes(title_text='Признак', tickangle=60, row=2, col=1)
    fig.update_yaxes(title_text='Важность', row=2, col=1)

    fig.update_layout(
        showlegend=False,
        title_text=msg,
        margin=dict(t=150),
        title_font_size=12
    )

    path_model = 'control/control_model_new.pkl'
    with open(path_model, 'wb') as f:
        pickle.dump(pipeline, f)

    return fig.to_html(full_html=True, include_plotlyjs="cdn")


async def save_new_model():
    msg = ''
    admin_dir = '/home/vcb_admin/control/'
    bot_dir = '/home/vcb/'

    # admin_dir = '/home/idergunoff/PycharmProjects/VContexteAdminWeb/control/'
    # bot_dir = '/home/idergunoff/PycharmProjects/VContexteBot/'

    # Пути файлов
    new_model = os.path.join(admin_dir, 'control_model_new.pkl')
    old_model = os.path.join(admin_dir, 'control_model.pkl')
    bot_model = os.path.join(bot_dir, 'control_model.pkl')

    # 1. Заменить модель в папке администратора
    if os.path.exists(new_model):
        # Удаляем старую, если есть
        if os.path.exists(old_model):
            os.remove(old_model)
        # Переименовываем новую модель
        os.rename(new_model, old_model)
        msg += f'Обновлено: {old_model}\n'
    else:
        msg += f'Файл {new_model} не найден!\n'
    # 2. Скопировать свежую модель к боту
    if os.path.exists(old_model):
        shutil.copy2(old_model, bot_model)
        msg += f'Скопировано: {bot_model}'
    else:
        msg += f'Файл {old_model} не найден, копирование не выполнено.'

    return msg