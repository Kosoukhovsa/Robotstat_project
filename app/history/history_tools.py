from flask import render_template, redirect, url_for, flash, request, session
from app import db
from app.history import bp
from app.history.forms import HistoryFilterForm, HistoryMainForm, IndicatorsForm, IndicatorItemForm
from app.models import Histories, Clinics, Diagnoses, Patients, Indicators, HistoryEvents,\
                       IndicatorValues, DiagnosesItems, Events, Prosthesis, Operations
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
        # список диагнозов для отображения в форме
        diagnoses_items = history.get_diagnoses()[0]
        main_diagnose = history.get_diagnoses()[1]

        if main_diagnose is not None:
            MainDiagnosForm.diagnos.data = main_diagnose.diagnose
            MainDiagnosForm.side_damage.data = main_diagnose.side_damage
            MainDiagnosForm.date_created.data = main_diagnose.date_created

        # Добавление амбулаторных приемов
        ambulance_events = history.get_events(type=2)

        # Добавление госпитализаций
        hospital_events = history.get_events(type=3)


        return([MainForm, FirstForm, MainDiagnosForm, event, items, diagnoses_items, ambulance_events, hospital_events])

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
        # Показатели:
        # 11 - Физические параметры (самооценка при первичном опросе)
        # 3 - Телерентгенография
        # 4 - Предоперационные обследования
        indicators = Indicators.query.filter(Indicators.group in [11,3,4]).\
                                order_by(Indicators.group, Indicators.id).all()
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
        #indicators = IndicatorValues.query.filter(IndicatorValues.history==history.id, IndicatorValues.history_event==ambulance_event.id).all()
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

# Создание новой госпитализации
def CreateHospital(HospitalSubForm1_, history):
    hospital_event = HistoryEvents()
    hospital_event.clinic = history.clinic
    hospital_event.history = history.id
    hospital_event.patient = history.patient
    hospital_event.event = 3
    hospital_event.date_begin = HospitalSubForm1_.date_begin.data
    hospital_event.date_end = HospitalSubForm1_.date_end.data
    hospital_event.doctor = HospitalSubForm1_.doctor.data
    hospital_event.doctor_chief = HospitalSubForm1_.doctor_chief.data
    db.session.add(hospital_event)
    # Показатели:
    indicators = Indicators.query.filter(Indicators.group.in_([5,1,7,8])).order_by(Indicators.group,Indicators.id).all()
    #Рентгенография коленного сустава в двух проекциях
    indicators_2 = Indicators.query.filter(Indicators.group==2).order_by(Indicators.group,Indicators.id).all()
    #Телерентгенография нижних конечностей
    indicators_3 = Indicators.query.filter(Indicators.group==3).order_by(Indicators.group,Indicators.id).all()

    for i in indicators:
        new_i = IndicatorValues()
        new_i.clinic = hospital_event.clinic
        new_i.history = hospital_event.history
        new_i.patient = hospital_event.patient
        new_i.history_event = hospital_event.id
        new_i.indicator = i.id
        db.session.add(new_i)

    # Показатели: Телерентгенография
    for i in indicators_3:
        new_i = IndicatorValues()
        new_i.clinic = hospital_event.clinic
        new_i.history = hospital_event.history
        new_i.patient = hospital_event.patient
        new_i.history_event = hospital_event.id
        new_i.indicator = i.id
        new_i.slice = 'Значение'
        db.session.add(new_i)
        new_i = IndicatorValues()
        new_i.clinic = hospital_event.clinic
        new_i.history = hospital_event.history
        new_i.patient = hospital_event.patient
        new_i.history_event = hospital_event.id
        new_i.indicator = i.id
        new_i.slice = 'План операции'
        db.session.add(new_i)

    # Показатели: Рентгенография коленного сустава в двух проекциях
    for i in indicators_2:
        new_i = IndicatorValues()
        new_i.clinic = hospital_event.clinic
        new_i.history = hospital_event.history
        new_i.patient = hospital_event.patient
        new_i.history_event = hospital_event.id
        new_i.indicator = i.id
        new_i.slice = 'Передне-задняя проекция'
        db.session.add(new_i)
        new_i = IndicatorValues()
        new_i.clinic = hospital_event.clinic
        new_i.history = hospital_event.history
        new_i.patient = hospital_event.patient
        new_i.history_event = hospital_event.id
        new_i.indicator = i.id
        new_i.slice = 'Боковая проекция'
        db.session.add(new_i)
        new_i = IndicatorValues()
        new_i.clinic = hospital_event.clinic
        new_i.history = hospital_event.history
        new_i.patient = hospital_event.patient
        new_i.history_event = hospital_event.id
        new_i.indicator = i.id
        new_i.slice = 'Планируемое значение'
        db.session.add(new_i)
        new_i = IndicatorValues()
        new_i.clinic = hospital_event.clinic
        new_i.history = hospital_event.history
        new_i.patient = hospital_event.patient
        new_i.history_event = hospital_event.id
        new_i.indicator = i.id
        new_i.slice = 'Фактическое значение'
        db.session.add(new_i)
        new_i = IndicatorValues()
        new_i.clinic = hospital_event.clinic
        new_i.history = hospital_event.history
        new_i.patient = hospital_event.patient
        new_i.history_event = hospital_event.id
        new_i.indicator = i.id
        new_i.slice = 'Совпадение'
        db.session.add(new_i)

    db.session.commit()
    return(hospital_event)


# Обновление госпитализации
def UpdateHospital(HospitalSubForm1_, hospital_event):
        hospital_event.date_begin = HospitalSubForm1_.date_begin.data
        hospital_event.date_end = HospitalSubForm1_.date_end.data
        hospital_event.doctor = HospitalSubForm1_.doctor.data
        hospital_event.doctor_chief = HospitalSubForm1_.doctor_chief.data
        # Расчет койко-дней

        if hospital_event.date_end is not None:
            delta = hospital_event.date_end - hospital_event.date_begin
            hospital_event.days1 = delta.days
        if hospital_event.date_end is None:
            hospital_event.days1 = 0
        # Если есть операция, то находим дату
        operation = Operations.query.filter(Operations.history==hospital_event.history).first()
        if operation is not None and hospital_event.date_end is not None:
            # Послеоперационный койко-день
            delta = hospital_event.date_end - operation.time_begin.date
            hospital_event.days3 = delta.days
        if operation is not None:
            # Предоперационный койко-день
            delta = operation.time_begin.date - hospital_event.date_begin
            hospital_event.days2 = delta.days
        if operation is None:
            hospital_event.days2 = 0
            hospital_event.days3 = 0

        #print(type(hospital_event.date_end))
        db.session.add(hospital_event)
        db.session.commit()
        return(hospital_event)

# Заполнение формы госпитализации
def FillHospitalForm(HospitalSubForm1_, HospitalSubForm2_, history, hospital_event):
    HospitalSubForm1_.date_begin.data = hospital_event.date_begin
    HospitalSubForm1_.date_end.data = hospital_event.date_end
    HospitalSubForm1_.doctor.data = hospital_event.doctor
    HospitalSubForm1_.doctor_chief.data = hospital_event.doctor_chief
    HospitalSubForm1_.days1.data = hospital_event.days1
    HospitalSubForm1_.days2.data = hospital_event.days2
    HospitalSubForm1_.days3.data = hospital_event.days3

    # Общие данные о пациенте
    items_5 = hospital_event.get_indicators_values(5)
    # Заполнить форму
    for item in items_5:
        indicator_id = item.get('indicator')
        HospitalSubForm2_.date_begin.data = item.get('date_value')
        if indicator_id == 49:
            HospitalSubForm2_.claims.data = item.get('text_value')
        if indicator_id == 50:
            HospitalSubForm2_.claims_time.data = item.get('text_value')
        if indicator_id == 51:
            HospitalSubForm2_.diseases.data = item.get('text_value')
        if indicator_id == 52:
            HospitalSubForm2_.traumas.data = item.get('text_value')
        if indicator_id == 53:
            HospitalSubForm2_.smoking.data = item.get('text_value')
        if indicator_id == 54:
            HospitalSubForm2_.alcohol.data = item.get('text_value')
        if indicator_id == 55:
            HospitalSubForm2_.allergy.data = item.get('text_value')
        if indicator_id == 56:
            HospitalSubForm2_.genetic.data = item.get('text_value')

    # Данные объективного осмотра
    items_1 = hospital_event.get_indicators_values(1)
    # Оценка функции сустава и качества жизни по шкалам
    items_7 = hospital_event.get_indicators_values(7)
    # Результаты лабораторных исследований
    items_8 = hospital_event.get_indicators_values(8)
    # Рентгенография коленного сустава в двух проекциях
    indicators_sliced_values_2 = hospital_event.get_indicators_values(2, indicators_list=[11,12,13])
    # Телерентгенография
    indicators_sliced_values_3 = hospital_event.get_indicators_values(3)

    # Рентгенография коленного сустава в двух проекциях: транспонирование списка
    item = {}
    items_2 = []
    current_indicator = 11
    for indicator_value in indicators_sliced_values_2:
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
        if slice == 'Планируемое значение':
            item['text_value_3'] = indicator_value.get('text_value')
        if slice == 'Фактическое значение':
            item['text_value_4'] = indicator_value.get('text_value')
        if slice == 'Результат':
            item['text_value_5'] = indicator_value.get('text_value')

    items_2.append(item)

    # Телерентгенография: транспонирование списка
    item = {}
    items_3 = []
    current_indicator = 16
    for indicator_value in indicators_sliced_values_3:
        #item['id'] = indicator_value.get('id')
        if current_indicator != indicator_value.get('indicator'):
            items_3.append(item)
            current_indicator = indicator_value.get('indicator')
            item = {}
        item['indicator'] = indicator_value.get('indicator')
        item['description'] = indicator_value.get('description')
        slice = indicator_value.get('slice')
        if slice == 'Значение':
            item['text_value_1'] = indicator_value.get('text_value')
        if slice == 'План операции':
            item['text_value_2'] = indicator_value.get('text_value')

    items_3.append(item)

    return(HospitalSubForm1_, HospitalSubForm2_, [items_1, items_2, items_3, items_5, items_7, items_8])
