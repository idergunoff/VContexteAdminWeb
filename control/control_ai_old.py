import random

import numpy as np
from scipy.stats import kurtosis, skew
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.manifold import TSNE
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_curve, auc
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from imblearn.over_sampling import SMOTE, ADASYN
from sqlalchemy.orm import joinedload

from control.model_control import *
from func import *
from func_list_update import update_list_user_by_word_id
from statistic import graph_vers


def get_control_params(trying, trying_versions=False):
    versions = session.query(Version).filter_by(trying_id=trying.id).order_by(Version.date_version).all()
    list_vers = [v.index for v in versions]
    list_times = [(versions[i+1].date_version - versions[i].date_version).total_seconds() for i in range(len(versions) - 1)]
    list_vers100 = json.dumps(interpolate_list(list_vers))
    list_times100 = json.dumps(interpolate_list(list_times)) if list_times else json.dumps([0 for _ in range(100)])
    distr_vers15 = json.dumps(get_distribution(list_vers, 5))
    distr_times15 = json.dumps(get_distribution(list_times, 5)) if list_times else json.dumps([0 for _ in range(5)])
    count_versions = len(versions)
    count_hint_step = trying.hint
    count_hint_allusion = session.query(HintMainVers).join(Version).filter(
        Version.trying_id == trying.id,
        HintMainVers.hint_type == 'allusion'
    ).count()
    count_hint_center = session.query(HintMainVers).join(Version).filter(
        Version.trying_id == trying.id,
        HintMainVers.hint_type == 'center'
    ).count()
    hint_pixel = session.query(HintMainWord).filter_by(trying_id=trying.id, hint_type='pixel').count()
    hint_bomb = session.query(HintMainWord).filter_by(trying_id=trying.id, hint_type='bomb').count()
    hint_tail = session.query(HintMainWord).filter_by(trying_id=trying.id, hint_type='tail').count()
    hint_metr = session.query(HintMainWord).filter_by(trying_id=trying.id, hint_type='metr').count()
    hint_crash = session.query(HintCrashTrying).filter_by(trying_id=trying.id).count()

    all_time = (trying.date_done - trying.date_trying).total_seconds()
    if not trying_versions:
        trying_versions = session.query(Trying).options(joinedload(Trying.versions)).filter(
            Trying.word_id == trying.word_id,
            Trying.done == True,
        ).all()
    user_trying = session.query(Trying).options(joinedload(Trying.versions)).filter(
        Trying.user_id == trying.user_id,
        Trying.done == True
    ).all()

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


    # mean_count_vers = 0 if np.isnan(mean_count_vers) else mean_count_vers
    # mean_time = 0 if np.isnan(mean_time) else mean_time

    # print('mean_count_vers', mean_count_vers)
    # print('mean_count_vers_user', mean_count_vers_user)
    # print('median_count_vers', median_count_vers)
    # print('median_count_vers_user', median_count_vers_user)
    # print('kurtosis_count_vers', kurtosis_count_vers)
    # print('kurtosis_count_vers_user', kurtosis_count_vers_user)
    # print('skewness_count_vers', skewness_count_vers)
    # print('skewness_count_vers_user', skewness_count_vers_user)
    # print('mean_time', mean_time)
    # print('mean_time_user', mean_time_user)
    # print('median_time', median_time)
    # print('median_time_user', median_time_user)
    # print('kurtosis_time', kurtosis_time)
    # print('kurtosis_time_user', kurtosis_time_user)
    # print('skewness_time', skewness_time)
    # print('skewness_time_user', skewness_time_user)

    return (list_vers100, list_times100, distr_vers15, distr_times15, count_versions, count_hint_step,
            count_hint_allusion, count_hint_center, hint_pixel, hint_bomb, hint_tail, hint_metr, hint_crash,
            mean_count_vers, mean_time, median_count_vers, median_time, kurtosis_count_vers, kurtosis_time,
            skewness_count_vers, skewness_time, mean_count_vers_user, mean_time_user, median_count_vers_user,
            median_time_user, kurtosis_count_vers_user, kurtosis_time_user, skewness_count_vers_user,
            skewness_time_user, all_time)


def build_table_train(model_id):
    """ Построение таблицы модели контроля """
    list_param, list_mark = [], []
    print(model_id)
    for t in session_ctrl_ai.query(TryingTrainControl).filter_by(model_id=model_id).all():
        print(t.id)
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
    return np.array(list_param), np.array(list_mark)


def start_train():
    """ Запуск обучения модели контроля """
    TrainControl = QtWidgets.QDialog()
    ui_tc = Ui_FormTrainControl()
    ui_tc.setupUi(TrainControl)
    TrainControl.show()

    m_width, m_height = get_width_height_monitor()
    TrainControl.resize(int(m_width / 3), int(m_height / 3))

    TrainControl.setAttribute(Qt.WA_DeleteOnClose)

    def update_list_model():
        """ Обновляет список моделей контроля """
        ui_tc.comboBox_model.clear()
        for i in session_ctrl_ai.query(ModelControl).all():
            ui_tc.comboBox_model.addItem(f'{i.title} id {i.id}')


    def add_new_model():
        """ Добавляет новую модель контроля в базу данных """
        new_model = ModelControl(title=datetime.datetime.now().strftime('%d.%m.%Y'))
        session_ctrl_ai.add(new_model)
        session_ctrl_ai.commit()
        update_list_model()
        update_list_trying_train()


    def rm_model():
        """ Удаляет модель контроля из базы данных """
        all_traing = session_ctrl_ai.query(TryingTrainControl).filter_by(model_id=get_model_id()).all()
        for t in all_traing:
            session_ctrl_ai.query(ParamControl).filter_by(trying_train_id=t.id).delete()
            session_ctrl_ai.delete(t)
        session_ctrl_ai.query(ModelControl).filter_by(id=get_model_id()).delete()
        session_ctrl_ai.commit()
        update_list_model()
        update_list_trying_train()


    def get_model_id():
        """ Возвращает id выбранной модели контроля """
        return ui_tc.comboBox_model.currentText().split(' id')[-1]

    def update_list_trying_train():
        """ Обновляет список тренировочных попыток """
        trying_true = session_ctrl_ai.query(TryingTrainControl).filter_by(honestly=True, model_id=get_model_id()).all()
        trying_false = session_ctrl_ai.query(TryingTrainControl).filter_by(honestly=False, model_id=get_model_id()).all()
        ui_tc.listWidget_true.clear()
        ui_tc.listWidget_false.clear()
        ui_tc.label_true.setText(f'count TRUE: {len(trying_true)}')
        ui_tc.label_false.setText(f'count FALSE: {len(trying_false)}')
        for i in trying_true:
            ui_tc.listWidget_true.addItem(f'{i.username} {i.word} {i.date_trying.strftime("%d.%m.%Y %H:%M:%S")} id {i.trying_id}')
        for i in trying_false:
            ui_tc.listWidget_false.addItem(f'{i.username} {i.word} {i.date_trying.strftime("%d.%m.%Y %H:%M:%S")} id {i.trying_id}')


    def add_trying_true():
        add_trying_to_model(True)


    def add_trying_false():
        add_trying_to_model(False)


    def add_trying_to_model(honestly):
        """ Добавляет новую тренировочную попытку """
        try:
            curr_user = session.query(User).filter_by(id=ui.listWidget_user.currentItem().text().split(' id')[-1]).first()
        except AttributeError:
            return
        word_id = get_word_id()
        curr_word = session.query(Word.word).filter_by(id=word_id).first()[0]
        curr_trying = session.query(Trying).filter_by(user_id=curr_user.id, word_id=word_id).first()
        trying_ctrl = session_ctrl_ai.query(TryingTrainControl).filter_by(model_id=get_model_id(), trying_id=curr_trying.id).first()
        if trying_ctrl:
            if trying_ctrl.honestly == True and honestly == False:
                session_ctrl_ai.query(ParamControl).filter_by(trying_train_id=trying_ctrl.id).delete()
                session_ctrl_ai.delete(trying_ctrl)
                session_ctrl_ai.commit()
                print('Попытка удалена из класса TRUE')
            else:
                QMessageBox.critical(TrainControl, 'Error', 'Такая попытка уже есть в этой модели')
                return
        new_trying = TryingTrainControl(
            model_id=get_model_id(),
            honestly=honestly,
            trying_id=curr_trying.id,
            date_trying=curr_trying.date_done,
            word=curr_word,
            username=curr_user.username
        )
        session_ctrl_ai.add(new_trying)
        session_ctrl_ai.commit()
        (list_vers100, list_times100, distr_vers15, distr_times15, count_versions, count_hint_step,
            count_hint_allusion, count_hint_center, hint_pixel, hint_bomb, hint_tail, hint_metr, hint_crash,
            mean_count_vers, mean_time, median_count_vers, median_time, kurtosis_count_vers, kurtosis_time,
            skewness_count_vers, skewness_time, mean_count_vers_user, mean_time_user, median_count_vers_user,
            median_time_user, kurtosis_count_vers_user, kurtosis_time_user, skewness_count_vers_user,
            skewness_time_user, all_time) = get_control_params(curr_trying)

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
        update_list_trying_train()


    def rm_trying_true():
        try:
            trying_train = session_ctrl_ai.query(TryingTrainControl).filter_by(
                model_id=get_model_id(),
                trying_id=ui_tc.listWidget_true.currentItem().text().split(' id')[-1]
            ).first()
            session_ctrl_ai.query(ParamControl).filter_by(trying_train_id=trying_train.id).delete()
            session_ctrl_ai.delete(trying_train)
            session_ctrl_ai.commit()
            update_list_trying_train()
        except AttributeError:
            return


    def rm_trying_false():
        try:
            trying_train = session_ctrl_ai.query(TryingTrainControl).filter_by(
                model_id=get_model_id(),
                trying_id=ui_tc.listWidget_false.currentItem().text().split(' id')[-1]
            ).first()
            session_ctrl_ai.query(ParamControl).filter_by(trying_train_id=trying_train.id).delete()
            session_ctrl_ai.delete(trying_train)
            session_ctrl_ai.commit()
            update_list_trying_train()
        except AttributeError:
            return


    def show_trying_true():
        ui.listWidget_vers.clear()
        trying = session.query(Trying).filter_by(id=ui_tc.listWidget_true.currentItem().text().split(' id')[-1]).first()
        if ui.checkBox_sort_vers.isChecked():
            versions = session.query(Version).filter_by(trying_id=trying.id).order_by(Version.index).all()
            v_hints = session.query(Version).join(Hint).filter(Version.trying_id == trying.id).order_by(
                Version.index).all()
        else:
            versions = session.query(Version).filter_by(trying_id=trying.id).order_by(Version.date_version).all()
            v_hints = session.query(Version).join(Hint).filter(Version.trying_id == trying.id).order_by(
                Version.date_version).all()
        ui.label_vers.setText(f'🧿{trying.hint}/📦{len(versions)}')
        for v in versions:
            hint = '🧿' if v in v_hints else ''
            item = QListWidgetItem(f'{hint}{v.index} {v.text} {v.date_version.strftime("%H:%M:%S")}')
            set_bg_item(v.index, item)

            ui.listWidget_vers.addItem(item)
        graph_vers(trying)


    def show_trying_false():
        ui.listWidget_vers.clear()
        trying = session.query(Trying).filter_by(id=ui_tc.listWidget_false.currentItem().text().split(' id')[-1]).first()
        if ui.checkBox_sort_vers.isChecked():
            versions = session.query(Version).filter_by(trying_id=trying.id).order_by(Version.index).all()
            v_hints = session.query(Version).join(Hint).filter(Version.trying_id == trying.id).order_by(Version.index).all()
        else:
            versions = session.query(Version).filter_by(trying_id=trying.id).order_by(Version.date_version).all()
            v_hints = session.query(Version).join(Hint).filter(Version.trying_id == trying.id).order_by(Version.date_version).all()
        ui.label_vers.setText(f'🧿{trying.hint}/📦{len(versions)}')
        for v in versions:
            hint = '🧿' if v in v_hints else ''
            item = QListWidgetItem(f'{hint}{v.index} {v.text} {v.date_version.strftime("%H:%M:%S")}')
            set_bg_item(v.index, item)

            ui.listWidget_vers.addItem(item)
        graph_vers(trying)


    def train_model():
        training_sample, mark = build_table_train(get_model_id())
        training_sample_train, training_sample_test, markup_train, markup_test = train_test_split(
            training_sample, mark, test_size=0.20, random_state=0, stratify=mark)
        smote = SMOTE(random_state=0)
        training_sample_train, markup_train = smote.fit_resample(training_sample_train, markup_train)
        pipe_steps = []
        std_scaler = StandardScaler()
        pipe_steps.append(('std_scaler', std_scaler))
        if ui_tc.checkBox_gbc.isChecked():
            # model_class = GradientBoostingClassifier(n_estimators=1000, learning_rate=0.1, random_state=0)

            model_class = XGBClassifier(n_estimators=1000, learning_rate=0.1, random_state=0)
        else:
            model_class = MLPClassifier(
                hidden_layer_sizes=tuple(map(int, ui_tc.lineEdit_layer_mlp.text().split())),
                activation=ui_tc.comboBox_activation_mlp.currentText(),
                solver=ui_tc.comboBox_solvar_mlp.currentText(),
                alpha=ui_tc.doubleSpinBox_alpha_mlp.value(),
                max_iter=5000,
                early_stopping=True,
                validation_fraction=0.2,
                random_state=0
            )
        # model_class = RandomForestClassifier(n_estimators=1000, random_state=0)
        # model_class = SVC(kernel='rbf', C=25, probability=True, random_state=0)
        # model_class = QuadraticDiscriminantAnalysis(reg_param=0.01)
        # model_class = KNeighborsClassifier(n_neighbors=25, weights='distance')
        pipe_steps.append(('mlp', model_class))
        pipeline = Pipeline(pipe_steps)
        pipeline.fit(training_sample_train, markup_train)
        print(f'Score on test: {pipeline.score(training_sample_test, markup_test)}')
        print(f'Score on train: {pipeline.score(training_sample_train, markup_train)}')
        kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

        scores_cv = cross_val_score(pipeline, training_sample, mark, cv=kf, n_jobs=-1)

        print(f'CV score: {round(np.mean(scores_cv), 3)} +/- {round(np.std(scores_cv), 3)}')
        print(scores_cv)

        preds_train = pipeline.predict(training_sample)
        preds_t = pipeline.predict(training_sample_test)
        print("accuracy", accuracy_score(markup_test, preds_t, normalize=True))
        print("precision", precision_score(markup_test, preds_t, average='binary'))
        print("recall", recall_score(markup_test, preds_t, average='binary'))
        print("f1", f1_score(markup_test, preds_t, average='binary'))

        preds_proba_train = pipeline.predict_proba(training_sample)
        tsne = TSNE(n_components=2, perplexity=30, learning_rate=200, random_state=42)
        train_tsne = tsne.fit_transform(preds_proba_train)
        data_tsne = pd.DataFrame(train_tsne)
        data_tsne['mark'] = preds_train

        (fig_train, axes) = plt.subplots(nrows=1, ncols=3)
        fig_train.set_size_inches(25, 10)

        sns.scatterplot(data=data_tsne, x=0, y=1, hue='mark', s=200, ax=axes[0])
        axes[0].grid()
        axes[0].xaxis.grid(True, "minor", linewidth=.25)
        axes[0].yaxis.grid(True, "minor", linewidth=.25)

        # Вычисляем ROC-кривую и AUC
        preds_test = pipeline.predict_proba(training_sample_test)[:, 1]
        fpr, tpr, thresholds = roc_curve(markup_test, preds_test, pos_label=1)
        roc_auc = auc(fpr, tpr)

        # Строим ROC-кривую
        axes[1].plot(fpr, tpr, color='darkorange', lw=2, label='ROC curve (area = %0.2f)' % roc_auc)
        axes[1].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        axes[1].set_xlim([0.0, 1.0])
        axes[1].set_ylim([0.0, 1.05])
        axes[1].set_xlabel('False Positive Rate')
        axes[1].set_ylabel('True Positive Rate')
        axes[1].set_title('ROC-кривая')
        axes[1].legend(loc="lower right")


        axes[2].bar(range(len(scores_cv)), scores_cv)
        axes[2].set_title('Кросс-валидация')

        fig_train.tight_layout()
        fig_train.show()

        if ui_tc.checkBox_save_model.isChecked():
            path_model = 'control/control_model.pkl'
            with open(path_model, 'wb') as f:
                pickle.dump(pipeline, f)

    def add_trying_to_model_to_auto(model_id, trying, honestly):
        """ Добавляет новую тренировочную попытку в автоматический набор"""
        curr_user = session.query(User).filter_by(id=trying.user_id).first()
        curr_word = session.query(Word.word).filter_by(id=trying.word_id).first()[0]

        new_trying = TryingTrainControl(
            model_id=model_id,
            honestly=honestly,
            trying_id=trying.id,
            date_trying=trying.date_done,
            word=curr_word,
            username=curr_user.username
        )
        session_ctrl_ai.add(new_trying)
        session_ctrl_ai.commit()
        (list_vers100, list_times100, distr_vers15, distr_times15, count_versions, count_hint_step,
            count_hint_allusion, count_hint_center, hint_pixel, hint_bomb, hint_tail, hint_metr, hint_crash,
            mean_count_vers, mean_time, median_count_vers, median_time, kurtosis_count_vers, kurtosis_time,
            skewness_count_vers, skewness_time, mean_count_vers_user, mean_time_user, median_count_vers_user,
            median_time_user, kurtosis_count_vers_user, kurtosis_time_user, skewness_count_vers_user,
            skewness_time_user, all_time) = get_control_params(trying)
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


    def auto_train_set():

        new_model = ModelControl(title=f'auto_{datetime.datetime.now().strftime("%d.%m.%Y")}')
        session_ctrl_ai.add(new_model)
        session_ctrl_ai.commit()

        false_tryings = session.query(Trying).filter(Trying.skip == True).all()
        count_false = 0
        for f in tqdm(false_tryings):
            if len(f.versions) != 1 and  len(f.versions) < 200:
                add_trying_to_model_to_auto(new_model.id, f, False)
                count_false += 1
        true_tryings = session.query(Trying).filter(Trying.skip == False, Trying.done == True).all()
        new_true_tryings = random.sample(true_tryings, count_false)
        for t in tqdm(new_true_tryings):
            add_trying_to_model_to_auto(new_model.id, t, True)

        update_list_model()
        update_list_trying_train()


    def auto_add_false():
        false_tryings = session.query(Trying).filter(Trying.skip == True).all()
        new_false_tryings = random.sample(false_tryings, ui_tc.spinBox_auto_add.value())
        count_add_trying = 0
        for f in tqdm(new_false_tryings):
            if len(f.versions) != 1 and  len(f.versions) < 200:
                trying_ctrl = session_ctrl_ai.query(TryingTrainControl).filter_by(model_id=get_model_id(), trying_id=f.id).first()
                if trying_ctrl:
                    if trying_ctrl.honestly == True:
                        session_ctrl_ai.query(ParamControl).filter_by(trying_train_id=trying_ctrl.id).delete()
                        session_ctrl_ai.delete(trying_ctrl)
                        session_ctrl_ai.commit()
                        print('Попытка удалена из класса TRUE')
                    else:
                        continue
                add_trying_to_model_to_auto(get_model_id(), f, False)
                count_add_trying += 1
        print(f'Добавлено {count_add_trying} попыток')
        update_list_trying_train()



    def auto_add_true():
        true_tryings = session.query(Trying).filter(Trying.skip == False, Trying.done == True).all()
        new_true_tryings = random.sample(true_tryings, ui_tc.spinBox_auto_add.value())
        count_add_trying = 0
        for t in tqdm(new_true_tryings):
            if session_ctrl_ai.query(TryingTrainControl).filter_by(model_id=get_model_id(), trying_id=t.id).count() > 0:
                continue
            add_trying_to_model_to_auto(get_model_id(), t, True)
            count_add_trying += 1
        print(f'Добавлено {count_add_trying} попыток')
        update_list_trying_train()


    update_list_model()
    update_list_trying_train()

    ui_tc.toolButton_add_model.clicked.connect(add_new_model)
    ui_tc.toolButton_rm_model.clicked.connect(rm_model)
    ui_tc.comboBox_model.currentTextChanged.connect(update_list_trying_train)
    ui_tc.pushButton_add_true.clicked.connect(add_trying_true)
    ui_tc.pushButton_add_false.clicked.connect(add_trying_false)
    ui_tc.pushButton_rm_true.clicked.connect(rm_trying_true)
    ui_tc.pushButton_rm_false.clicked.connect(rm_trying_false)
    ui_tc.listWidget_true.doubleClicked.connect(show_trying_true)
    ui_tc.listWidget_false.doubleClicked.connect(show_trying_false)
    ui_tc.pushButton_train.clicked.connect(train_model)
    ui_tc.toolButton_auto.clicked.connect(auto_train_set)
    ui_tc.pushButton_auto_add_false.clicked.connect(auto_add_false)
    ui_tc.pushButton_auto_add_true.clicked.connect(auto_add_true)

    TrainControl.exec_()

def control_ai():
    try:
        curr_user = session.query(User).filter_by(id=ui.listWidget_user.currentItem().text().split(' id')[-1]).first()
    except AttributeError:
        return
    word_id = get_word_id()
    curr_trying = session.query(Trying).filter_by(user_id=curr_user.id, word_id=word_id).first()

    with open('control/control_model.pkl', 'rb') as f:
        model = pickle.load(f)

    mark, probability = check_control_al(curr_trying, model)
    print('MARK: ', mark)
    print('PROBABILITY: ', probability)


def check_control_al(curr_trying, model, trying_versions=False):
    (list_vers100, list_times100, distr_vers15, distr_times15, count_versions, count_hint_step,
            count_hint_allusion, count_hint_center, hint_pixel, hint_bomb, hint_tail, hint_metr, hint_crash,
            mean_count_vers, mean_time, median_count_vers, median_time, kurtosis_count_vers, kurtosis_time,
            skewness_count_vers, skewness_time, mean_count_vers_user, mean_time_user, median_count_vers_user,
            median_time_user, kurtosis_count_vers_user, kurtosis_time_user, skewness_count_vers_user,
            skewness_time_user, all_time) = get_control_params(curr_trying, trying_versions)
    param = json.loads(list_vers100) + json.loads(list_times100) + json.loads(distr_vers15) + json.loads(distr_times15)
    param.append(count_versions)
    param.append(count_hint_step)
    param.append(count_hint_allusion)
    param.append(count_hint_center)
    param.append(hint_pixel)
    param.append(hint_bomb)
    param.append(hint_tail)
    param.append(hint_metr)
    param.append(hint_crash)
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


def update_param():
    for t in tqdm(session_ctrl_ai.query(TryingTrain).all()):
        curr_trying = session.query(Trying).filter_by(id=t.trying_id).first()
        (list_vers100, list_times100, distr_vers15, distr_times15, count_versions, count_hint_step,
            count_hint_allusion, count_hint_center, hint_pixel, hint_bomb, hint_tail, hint_metr, hint_crash,
            mean_count_vers, mean_time, median_count_vers, median_time, kurtosis_count_vers, kurtosis_time,
            skewness_count_vers, skewness_time, mean_count_vers_user, mean_time_user, median_count_vers_user,
            median_time_user, kurtosis_count_vers_user, kurtosis_time_user, skewness_count_vers_user,
            skewness_time_user, all_time) = get_control_params(curr_trying)
        new_param = ParamControl(
            trying_train_id=t.id,
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


# update_param()


