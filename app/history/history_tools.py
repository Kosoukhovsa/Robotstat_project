from flask import render_template, redirect, url_for, flash, request, session
from app import db
from app.history import bp
from app.history.forms import HistoryFilterForm, HistoryMainForm, IndicatorsForm, IndicatorItemForm
from app.models import Histories, Clinics, Diagnoses, Patients, Indicators, HistoryEvents,\
                       IndicatorValues, DiagnosesItems, Events, Prosthesis
from datetime import datetime
from hashlib import md5
from sqlalchemy import and_, or_, not_

# Создание новой истории болезни
def CreateHistory(MainForm):
    digest = md5(MainForm.snils.data.lower().encode('utf-8')).hexdigest()
    if Patients.get_patient_by_snils(digest) is None:
        # Новый пациент
        new_patient = Patients()
        new_patient.birthdate = MainForm.birthdate.data
        new_patient.sex = MainForm.sex.data
        new_patient.snils_hash = digest
        db.session.add(new_patient)
        db.session.commit()
        # Новая история болезни
        new_hist = Histories()
        new_hist.clinic = MainForm.clinic.data
        new_hist.hist_number = MainForm.hist_number.data
        new_hist.date_in = MainForm.date_in.data
        new_hist.patient = new_patient.id
        new_hist.research_group = MainForm.research_group.data
        new_hist.doctor_researcher = MainForm.doctor_researcher.data
        new_hist.date_research_in = MainForm.date_research_in.data
        new_hist.date_research_out = MainForm.date_research_out.data
        new_hist.reason = MainForm.reason.data
        db.session.add(new_hist)
        db.session.commit()
        # Пустое первичное обращение
        new_event = HistoryEvents()
        new_event.clinic = MainForm.clinic.data
        new_event.history = new_hist.id
        new_event.patient = new_patient.id
        new_event.date_begin = new_hist.date_in
        new_event.event = 1
        db.session.add(new_event)
        db.session.commit()
        # Показатели: Физические параметры (самооценка при первичном опросе)
        indicators = Indicators.query.filter(Indicators.group==11).all()
        for i in indicators:
            new_i = IndicatorValues()
            new_i.clinic = MainForm.clinic.data
            new_i.history = new_hist.id
            new_i.patient = new_patient.id
            new_i.history_event = new_event.id
            new_i.indicator = i.id
            db.session.add(new_i)
            db.session.commit()
        return(new_hist)

    else:
        flash('Пациент с указанным СНИЛС уже есть в базе', category='warning')
        return(None)

# Обновление истории болезни
def UpdateHistory(MainForm, h):
        history = Histories.query.get(h)
        if history is None:
            return(None)
        else:
            patient =  Patients.query.get(history.patient)
            if patient is not None:
                patient.birthdate = MainForm.birthdate.data
                patient.sex = MainForm.sex.data
                db.session.add(patient)
                db.session.commit()
            # Новая история болезни
            history.clinic = MainForm.clinic.data
            history.hist_number = MainForm.hist_number.data
            history.date_in = MainForm.date_in.data
            history.patient = patient.id
            history.research_group = MainForm.research_group.data
            history.doctor_researcher = MainForm.doctor_researcher.data
            history.date_research_in = MainForm.date_research_in.data
            history.date_research_out = MainForm.date_research_out.data
            history.reason = MainForm.reason.data
            db.session.add(history)
            db.session.commit()
            return(history)

# Заполнение формы истории болезни
def FillHistoryForm(MainForm, FirstForm, MainDiagnosForm, history):
    #MainForm = HistoryMainForm()

    if history != None:
        patient = Patients.query.get(history.patient)
        MainForm.clinic.data = history.clinic
        MainForm.hist_number.data = history.hist_number
        MainForm.snils.data = patient.snils_hash
        MainForm.birthdate.data = patient.birthdate
        MainForm.sex.data = patient.sex
        MainForm.date_in.data = history.date_in
        MainForm.research_group.data = history.research_group
        MainForm.doctor_researcher.data = history.doctor_researcher
        MainForm.date_research_in.data = history.date_research_in
        MainForm.date_research_out.data = history.date_research_out
        MainForm.reason.data = history.reason
        # Список показателей первичного обращения
        event = HistoryEvents.query.filter(HistoryEvents.history==history.id, HistoryEvents.event==1 ).first()
        FirstForm.date_begin.data = event.date_begin
        # Добавление показателей первичного обращения
        items = event.get_indicators_values(11)

        # список сопутствующих диагнозов для отображения в форме
        diagnoses = Diagnoses.query.filter(Diagnoses.history==history.id).all()
        diagnoses_items = []
        main_diagnos = None
        for d in diagnoses:
            diagnose_item = DiagnosesItems.query.get(d.diagnose)
            if diagnose_item.type == 'Основной':
                main_diagnos = d
            else:
                item = {}
                item['id'] = d.id
                item['description'] = diagnose_item.description
                item['mkb10'] = diagnose_item.mkb10
                item['date_created'] = d.date_created
                diagnoses_items.append(item)

        if main_diagnos is not None:
            MainDiagnosForm.diagnos.data = main_diagnos.diagnose
            MainDiagnosForm.side_damage.data = main_diagnos.side_damage
            MainDiagnosForm.date_created.data = main_diagnos.date_created

        # Добавление амбулаторных приемов
        ambulances = HistoryEvents.query.join(Events, Events.id==HistoryEvents.event).\
                            filter(and_(HistoryEvents.history==history.id,  Events.type=='2')).all()
        ambulance_events = []
        for a in ambulances:
            ambulance_item = Events.query.get(a.event)
            item = {}
            item['event_id'] = a.id
            item['event_date'] = a.date_begin
            item['event_name'] = ambulance_item.description
            item['event_type'] = ambulance_item.id
            ambulance_events.append(item)

        return([MainForm, FirstForm, MainDiagnosForm, event, items, diagnoses_items, ambulance_events])

    else:
        # История не найдена
        return(None)

# Добавление основного диагноза
def AddMainDiagnos(MainDiagnosForm, history):

    main_diagnose = None
    if history is not None:
        # Создать или обновить основной диагноз
        # Основной диагноз может быть только один
        main_diagnose = Diagnoses.query.filter(Diagnoses.history==history.id,Diagnoses.diagnose==MainDiagnosForm.diagnos.data).first()
        if main_diagnose is not None:
            # Такой диагноз уже есть
            # Обновить атрибуты
            main_diagnose.side_damage = MainDiagnosForm.side_damage.data
            main_diagnose.date_created = MainDiagnosForm.date_created.data
        else:
            # Такой основной диагноз еще отсутствует
            diagnoses = Diagnoses.query.filter(Diagnoses.history==history.id).all()
            for d  in diagnoses:
                diagnose_item = DiagnosesItems.query.get(d.diagnose)
                if diagnose_item.type == 'Основной':
                    # Уже есть основной диагноз но другой: будет перезаписан
                    main_diagnose = d
                    main_diagnose.diagnose = MainDiagnosForm.diagnos.data
                    main_diagnose.side_damage = MainDiagnosForm.side_damage.data
                    main_diagnose.date_created = MainDiagnosForm.date_created.data

            if main_diagnose is None:
                # Создаем основной диагноз
                main_diagnose = Diagnoses()
                main_diagnose.history = history.id
                main_diagnose.clinic = history.clinic
                main_diagnose.patient = history.patient
                main_diagnose.diagnose = MainDiagnosForm.diagnos.data
                main_diagnose.side_damage = MainDiagnosForm.side_damage.data
                main_diagnose.date_created = MainDiagnosForm.date_created.data

        db.session.add(main_diagnose)
        db.session.commit()

    return(main_diagnose)


# Добавление основного диагноза
def AddOtherDiagnos(OtherDiagnosForm, history):
    other_diagnose = None
    # Если диагноз уже добавлен - предупреждение
    other_diagnose = Diagnoses.query.filter(Diagnoses.history==history.id,Diagnoses.diagnose==OtherDiagnosForm.diagnos.data).first()
    if other_diagnose is not None:
        flash('Такой диагноз уже есть', category='warning')
        return(None)

    # Создаем новый диагноз

    other_diagnose = Diagnoses()
    other_diagnose.history = history.id
    other_diagnose.clinic = history.clinic
    other_diagnose.patient = history.patient
    other_diagnose.diagnose = OtherDiagnosForm.diagnos.data
    #other_diagnose.side_damage = MainDiagnosForm.side_damage.data
    other_diagnose.date_created = OtherDiagnosForm.date_created.data
    db.session.add(other_diagnose)
    db.session.commit()
    return(other_diagnose)

# Создание нового амбулаторного приема
def CreateAmbulance(AmbulanceForm, history, event):

    ambulance_event = HistoryEvents.query.filter(HistoryEvents.history==history.id,HistoryEvents.event==event.id).first()
    if ambulance_event is None:
        # Создаем амбулаторный прием
        ambulance_event = HistoryEvents()
        ambulance_event.clinic = history.clinic
        ambulance_event.history = history.id
        ambulance_event.patient = history.patient
        ambulance_event.event = event.id
        ambulance_event.date_begin = AmbulanceForm.date_begin.data
        ambulance_event.doctor = AmbulanceForm.doctor.data
        db.session.add(ambulance_event)
        # Показатели: Физические параметры (самооценка при первичном опросе)
        indicators = Indicators.query.filter(Indicators.group==11).all()
        for i in indicators:
            new_i = IndicatorValues()
            new_i.clinic = ambulance_event.clinic
            new_i.history = ambulance_event.history
            new_i.patient = ambulance_event.patient
            new_i.history_event = ambulance_event.id
            new_i.indicator = i.id
            db.session.add(new_i)
        # Показатели: Телерентгенография
        indicators = Indicators.query.filter(Indicators.group==3).all()
        for i in indicators:
            new_i = IndicatorValues()
            new_i.clinic = ambulance_event.clinic
            new_i.history = ambulance_event.history
            new_i.patient = ambulance_event.patient
            new_i.history_event = ambulance_event.id
            new_i.indicator = i.id
            db.session.add(new_i)
        # Показатели: Рентгенография коленного сустава в двух проекциях
        indicators = Indicators.query.filter(Indicators.group==2).all()
        for i in indicators:
            new_i = IndicatorValues()
            new_i.clinic = ambulance_event.clinic
            new_i.history = ambulance_event.history
            new_i.patient = ambulance_event.patient
            new_i.history_event = ambulance_event.id
            new_i.indicator = i.id
            new_i.slice = 'Передне-задняя проекция'
            db.session.add(new_i)
            new_i = IndicatorValues()
            new_i.clinic = ambulance_event.clinic
            new_i.history = ambulance_event.history
            new_i.patient = ambulance_event.patient
            new_i.history_event = ambulance_event.id
            new_i.indicator = i.id
            new_i.slice = 'Боковая проекция'
            db.session.add(new_i)
            new_i = IndicatorValues()
            new_i.clinic = ambulance_event.clinic
            new_i.history = ambulance_event.history
            new_i.patient = ambulance_event.patient
            new_i.history_event = ambulance_event.id
            new_i.indicator = i.id
            new_i.slice = 'Результат'
            db.session.add(new_i)
        # Показатели: Предоперационные обследования
        indicators = Indicators.query.filter(Indicators.group==4).all()
        for i in indicators:
            new_i = IndicatorValues()
            new_i.clinic = ambulance_event.clinic
            new_i.history = ambulance_event.history
            new_i.patient = ambulance_event.patient
            new_i.history_event = ambulance_event.id
            new_i.indicator = i.id
            db.session.add(new_i)

        db.session.commit()
        return(ambulance_event)
    else:
        flash('Амбулаторный прием такого типа уже существует', category='warning')
        return(None)

# Обновление амбулаторного приема
def UpdateAmbulance(AmbulanceForm, ambulance_event):

        ambulance_event.doctor = AmbulanceForm.doctor.data
        ambulance_event.date_begin = AmbulanceForm.date_begin.data
        db.session.add(ambulance_event)
        db.session.commit()
        return(ambulance_event)


# Заполнение формы амбулаторного посещения
def FillAmbulanceForm(AmbulanceForm, IndicatorsForm_, ProsthesisForm_, history, ambulance_event):
    #MainForm = HistoryMainForm()
    if ambulance_event != None:
        AmbulanceForm.doctor.data = ambulance_event.doctor
        AmbulanceForm.date_begin.data = ambulance_event.date_begin
        IndicatorsForm_.date_begin.data = ambulance_event.date_begin
        indicators = IndicatorValues.query.filter(IndicatorValues.history==history.id, IndicatorValues.history_event==ambulance_event.id).all()
        # Физические параметры
        items_11 = ambulance_event.get_indicators_values(11)
        # Телерентгенография нижних конечностей
        items_3 = ambulance_event.get_indicators_values(3)
        # Список предоперационных обследований
        items_4 = ambulance_event.get_indicators_values(4)        
        # Рентгенография коленного сустава в двух проекциях
        indicators_sliced_values = ambulance_event.get_indicators_values(2, indicators_list=[11,12,13])

        # Рентгенография коленного сустава в двух проекциях: транспонирование списка
        item = {}
        items_2 = []
        current_indicator = 11
        for indicator_value in indicators_sliced_values:
            #item['id'] = indicator_value.get('id')
            if current_indicator != indicator_value.get('indicator'):
                items_2.append(item)
                current_indicator = indicator_value.get('indicator')
                item = {}
            item['indicator'] = indicator_value.get('indicator')
            item['description'] = indicator_value.get('description')
            slice = indicator_value.get('slice')
            if slice == 'Передне-задняя проекция':
                item['text_value_1'] = indicator_value.get('text_value')
            if slice == 'Боковая проекция':
                item['text_value_2'] = indicator_value.get('text_value')
            if slice == 'Результат':
                item['text_value_3'] = indicator_value.get('text_value')

        items_2.append(item)

        # Протезы
        diagnosis = Diagnoses.query.join(DiagnosesItems, Diagnoses.diagnose==DiagnosesItems.id).\
                                    filter(and_(Diagnoses.history==history.id, DiagnosesItems.type=='Основной')).first()

        if diagnosis is not None:
            ProsthesisForm_.prosthesis.data = diagnosis.prothes

        return([AmbulanceForm, items_11, items_2, items_3, items_4])

    else:
        # История не найдена
        return(None)
