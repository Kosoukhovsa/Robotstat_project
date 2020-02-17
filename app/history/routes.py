from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from app import db
from app.history import bp
from sqlalchemy import and_, or_, not_
from app.history.forms import HistoryFilterForm, HistoryMainForm, IndicatorsForm, \
                              IndicatorItemForm, HistoryMainDiagnosForm, HistoryOtherDiagnosForm,\
                              AmbulanceMainForm, HistioryNewAmbulanceForm, ProsthesisForm,\
                              TelerentgenographyForm, PreoperativeForm
from app.models import Histories, Clinics, Diagnoses, Patients, Indicators, HistoryEvents,\
                       IndicatorValues, Events, DiagnosesItems, Prosthesis
from datetime import datetime
from hashlib import md5
from app.history.history_tools import CreateHistory, UpdateHistory, FillHistoryForm, \
                                    AddMainDiagnos, AddOtherDiagnos, CreateAmbulance, \
                                    FillAmbulanceForm, UpdateAmbulance



# Список историй болезни
@bp.route('/history_select', methods = ['GET','POST'])
def history_select():

    FilterForm = HistoryFilterForm()
    page = request.args.get('page',1,type=int)

    clinic_filter_id = session.get('clinic_filter_id')
    snils_filter_hash = session.get('snils_filter_hash')
    history_list = Histories.query
    if clinic_filter_id is not None:
        history_list = history_list.filter(Histories.clinic==clinic_filter_id)

    if snils_filter_hash is not None:
        patient = Patients.query.filter(Patients.snils_hash==snils_filter_hash).first()
        if patient is not None:
            history_list = history_list.filter(Histories.patient==patient.id)


    pagination =  history_list.paginate(page,5,error_out=False)
    histories = pagination.items

    if FilterForm.submit_filter.data and FilterForm.validate_on_submit():
# Фильтрация списка
        history_list = Histories.query
        if FilterForm.clinic_filter.data != 0:
# Выбрано значение ( не All)
            history_list = history_list.filter(Histories.clinic==FilterForm.clinic_filter.data)
            session['clinic_filter_id']= FilterForm.clinic_filter.data
# Выбрано значение ALL - снять фильтр
        if FilterForm.clinic_filter.data == 0:
            session['clinic_filter_id'] = None

        if FilterForm.snils_filter.data != '':
# Выбрано значение ( не All)
            digest = md5(FilterForm.snils_filter.data.lower().encode('utf-8')).hexdigest()
            patient = Patients.query.filter(Patients.snils_hash==digest).first()
            if patient != None:
                history_list = history_list.filter(Histories.patient==patient.id)
                session['snils_filter_hash']= digest
            else:
                flash('Пациента с указанным СНИЛС не существует', category='warning')
                session['snils_filter_hash'] = None


# Выбрано значение ALL - снять фильтр
        if FilterForm.snils_filter.data == '':
            session['snils_filter_hash'] = None

        pagination =  history_list.paginate(page,5,error_out=False)
        histories = pagination.items


    return render_template('history/history_select.html', HistoryFilterForm=FilterForm,
                            title='Поиск истории болезни', histories=histories, pagination=pagination)


# Редактирование истории болезни
@bp.route('/history_edit/<h>/<pill>', methods = ['GET','POST'])
# Параметры:
# h - Histories.id
# pill - номер закладки в форме

def history_edit(h, pill):
    history = Histories.query.get(h)

    MainForm = HistoryMainForm()
    FirstForm = IndicatorsForm()
    MainDiagnosForm = HistoryMainDiagnosForm()
    OtherDiagnosForm = HistoryOtherDiagnosForm()
    NewAmbulanceForm = HistioryNewAmbulanceForm()

        # сохранение истории болезни
    if MainForm.submit.data and MainForm.validate_on_submit():
        pill = 1
        if history is None:
            # Это ввод новой истории
            history = CreateHistory(MainForm)
        else:
            # Обновление истории
            history = UpdateHistory(MainForm, h)

        if  history is not None:
            flash('Данные сохранены', category='info')
            return redirect(url_for('history.history_edit', h=history.id, pill=pill))

    if MainDiagnosForm.submit.data and MainDiagnosForm.validate_on_submit():
        pill = 3
        main_diagnose = AddMainDiagnos(MainDiagnosForm, history)
        if main_diagnose is not None:
            flash('Данные сохранены', category='info')

        return redirect(url_for('history.history_edit', h=history.id, pill=pill))

    if OtherDiagnosForm.submit.data and OtherDiagnosForm.validate_on_submit():
        pill = 3
        other_diagnose = AddOtherDiagnos(OtherDiagnosForm, history)
        if other_diagnose is not None:
            flash('Данные сохранены', category='info')

        return redirect(url_for('history.history_edit', h=history.id, pill=pill))

    if NewAmbulanceForm.submit.data and NewAmbulanceForm.validate_on_submit():
        pill = 4
        # Проверка существования такого типа приема
        hisory_event = HistoryEvents.query.filter(HistoryEvents.history==h, HistoryEvents.event==NewAmbulanceForm.event.data).first()
        if hisory_event is not None:
            flash('Амбулаторный прием такого типа уже существует', category='warning')
            return redirect(url_for('history.history_edit', h=history.id, pill=pill))
        else:
            # Переход в форму амбулаторного приема
            return redirect(url_for('history.ambulance_edit', h=history.id, h_e='0', e_type=NewAmbulanceForm.event.data, pill=1))

    if history is not None:
        # Заполнение формы данными из базы
        form_list = FillHistoryForm(MainForm, FirstForm, MainDiagnosForm, history)
        MainForm = form_list[0]
        FirstForm = form_list[1]
        MainDiagnosForm = form_list[2]
        history_event_id = form_list[3].id
        items = form_list[4]
        diagnoses_items = form_list[5]
        ambulance_events = form_list[6]
    else:
        items = []
        history_event_id = 0
        diagnoses_items = []
        ambulance_events = []
    return render_template('history/history_edit.html', HistoryMainForm=MainForm,
                            h=h, items = items, FirstForm=FirstForm,
                            MainDiagnosForm = MainDiagnosForm,
                            OtherDiagnosForm = OtherDiagnosForm,
                            NewAmbulanceForm = NewAmbulanceForm,
                            history_event_id = history_event_id,
                            diagnoses_items = diagnoses_items,
                            ambulance_events = ambulance_events,
                            pill=pill)


# Сохранение показателей первичного обращения
@bp.route('/save_indicators/<h>/<h_e>/<pill>', methods = ['GET','POST'])
# Параметры:
# h - Histories.id
# h_e - HistoryEvents.id
# pill - номер закладки в форме
def save_indicators(h, h_e, pill):
    history_event = HistoryEvents.query.get(h_e)
    event = Events.query.get(history_event.event)
    event_type = event.type
    if 'save_indicators' in request.form: #and FirstForm.validate_on_submit():

        # Группа показателей
        indicator_group = request.form.get('indicator_group')
        if indicator_group == '2':
            # Это Рентгенография коленного сустава в двух проекциях
            text_values_1 = request.form.getlist('text_value_1')
            text_values_2 = request.form.getlist('text_value_2')
            text_values_3 = request.form.getlist('text_value_3')
            ids = request.form.getlist('indicator')
            for i, id in enumerate(ids):

                indicator_pzp = IndicatorValues.query.filter(IndicatorValues.history_event==h_e, IndicatorValues.slice=='Передне-задняя проекция',
                                                            IndicatorValues.indicator==id).first()
                if indicator_pzp:
                    indicator_pzp.text_value = text_values_1[i]
                    db.session.add(indicator_pzp)

                indicator_bp = IndicatorValues.query.filter(IndicatorValues.history_event==h_e, IndicatorValues.slice=='Боковая проекция',
                                                            IndicatorValues.indicator==id).first()
                if indicator_bp:
                    indicator_bp.text_value = text_values_2[i]
                    db.session.add(indicator_bp)

                indicator_r = IndicatorValues.query.filter(IndicatorValues.history_event==h_e, IndicatorValues.slice=='Результат',
                                                            IndicatorValues.indicator==id).first()
                if indicator_r:
                    indicator_r.text_value = text_values_3[i]
                    db.session.add(indicator_r)

            db.session.commit()
            flash('Данные сохранены', category='info')

        elif indicator_group == '4':
            # Это предоперационные обследования
            select_values = request.form.getlist('select_value')
            ids = request.form.getlist('indicator_id')
            # Получим список всех показателей
            for i, id in enumerate(ids):
                indicator_value = IndicatorValues.query.get(id)
                if indicator_value:
                    if len(select_values) > i:
                        indicator_value.text_value = select_values[i]
                    db.session.add(indicator_value)
            db.session.commit()
            flash('Данные сохранены', category='info')

        elif indicator_group in ['11','3']:
            # Дата ввода показателей
            #print(indicator_group)
            if request.form.get('date_begin'):
                history_event.date_begin = datetime.strptime(request.form.get('date_begin'), '%Y-%m-%d').date()
                db.session.add(history_event)
                db.session.commit()
            # Это физические параметры
            num_values = request.form.getlist('num_value')
            comments = request.form.getlist('comment')
            ids = request.form.getlist('indicator_id')
            # Получим список всех показателей физ параметров истории болезни
            for i, id in enumerate(ids):
                indicator_value = IndicatorValues.query.get(id)


                if indicator_value:
                    # Сохранить дату показаний
                    if request.form.get('date_begin'):
                        indicator_value.date_value = datetime.strptime(request.form.get('date_begin'), '%Y-%m-%d').date()

                    if len(num_values) > i:
                        if num_values[i] == '':
                            num_values[i] = 0
                        indicator_value.num_value = int(num_values[i])
                    #print(len(comments))
                    if len(comments) > i:
                        indicator_value.comment = comments[i]
                    if indicator_group == '11':
                        # Расчет ИМТ
                        if i == 2 and int(num_values[0]) != 0:
                            indicator_value.num_value = int(num_values[1])/(int(num_values[0])/100)**2
                    db.session.add(indicator_value)

            db.session.commit()
            flash('Данные сохранены', category='info')


    if event_type == '1':
        # Сохранение выполнено из первичного приема
        return redirect(url_for('history.history_edit', h=h, pill=pill))
    elif event_type == '2':
        # Сохранение выполнено из амбулаторного  приема
        return redirect(url_for('history.ambulance_edit', h=h, h_e=h_e, e_type = event.id, pill=pill))

# История болезни / Диагнозы
@bp.route('/diagnose_delete/<h>/<d>/<pill>', methods = ['GET','POST'])
# Параметры:
# h - Histories.id
# d - Diagnoses.id
# pill - номер закладки в форме
def diagnose_delete(h,d,pill):
    diagnose = Diagnoses.query.get(d)
    db.session.delete(diagnose)
    db.session.commit()

    return redirect(url_for('history.history_edit', h=h, pill=pill))


# Редактирование амбулаторного приема
@bp.route('/ambulance_edit/<h>/<h_e>/<e_type>/<pill>', methods = ['GET','POST'])
# Параметры:
# h - Histories.id
# h_e - HistoryEvents.id
# e_type - Тип события
# pill - номер закладки в форме
def ambulance_edit(h, h_e, e_type, pill):
    history = Histories.query.get(h)
    AmbulanceForm = AmbulanceMainForm()
    IndicatorsForm_ = IndicatorsForm()
    ProsthesisForm_ = ProsthesisForm()
    PreoperativeForm_ = PreoperativeForm()
    TelerentgenographyForm_ = TelerentgenographyForm()
    event = Events.query.get(e_type)
    AmbulanceForm.event.data = event.id
    ambulance_event = HistoryEvents.query.get(h_e)


    if AmbulanceForm.submit.data and AmbulanceForm.validate_on_submit():
        pill = 1
        ambulance_created = False
        if ambulance_event is None:
            # Это ввод нового амбулаторного приема
            ambulance_event = CreateAmbulance(AmbulanceForm, history, event)

        else:
            # Обновление амбулаторного приема
            ambulance_event = HistoryEvents.query.get(h_e)
            UpdateAmbulance(AmbulanceForm, ambulance_event)

        if ambulance_event is not None:
            flash('Данные сохранены', category='info')
            return redirect(url_for('history.ambulance_edit', h=h, h_e=ambulance_event.id, e_type=e_type, pill=pill))

        else:
            # Ввод не выполнен. Сохранение новой формы не завершено.
            return redirect(url_for('history.ambulance_edit', h=h, h_e='0', e_type=e_type, pill=pill))

    if ProsthesisForm_.submit.data and ProsthesisForm_.validate_on_submit():
        pill = 3
        # Сохраняем протез с привязкой к основному диагнозу
        diagnosis = Diagnoses.query.join(DiagnosesItems, Diagnoses.diagnose==DiagnosesItems.id).\
                                    filter(and_(Diagnoses.history==history.id, DiagnosesItems.type=='Основной')).first()
        prothesis = Prosthesis.query.get(ProsthesisForm_.prosthesis.data)

        if diagnosis:
            diagnosis.prothes = ProsthesisForm_.prosthesis.data
            db.session.add(diagnosis)
            db.session.commit()
            flash('Данные сохранены', category='info')
        else:
            flash('Отсутствует основной диагноз', category='danger')

        return redirect(url_for('history.ambulance_edit', h=h, h_e=ambulance_event.id, e_type=e_type, pill=pill))


    if ambulance_event is not None:
        # Открываем уже сущестующее посещение
        # Заполнение формы данными из базы
        form_list = FillAmbulanceForm(AmbulanceForm, IndicatorsForm_, ProsthesisForm_, history, ambulance_event)
        AmbulanceForm = form_list[0]
        items = form_list[1]
        items_2 = form_list[2]
        items_3 = form_list[3]
        items_4 = form_list[4]

    else:
        items = []
        items_2 = []
        items_3 = []
        items_4 = []

    return render_template('history/ambulance.html', AmbulanceMainForm = AmbulanceForm,
                            IndicatorsForm=IndicatorsForm_, ProsthesisForm = ProsthesisForm_,
                            TelerentgenographyForm=TelerentgenographyForm_,
                            PreoperativeForm = PreoperativeForm_,
                            h=h, history_event_id = h_e,
                            event=event, history=history, items = items,
                            items_2=items_2, items_3 = items_3,
                            items_4 = items_4, pill=pill)
