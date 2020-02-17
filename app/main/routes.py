from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.main import bp
from app.main.forms import PatientForm
from app import db
from app.models import Patients, Users
from werkzeug.urls import url_parse
from hashlib import md5
from ..decorators import permission_required

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/testboot')
def testboot():
    return render_template('superbaseboot.html')


@bp.route('/patient_data_enter', methods = ['GET','POST'])
@login_required
@permission_required('HIST_W')
def patient_data_enter():
    #fio = None
    form = PatientForm()
    if form.validate_on_submit():
        patient = \
        Patients.query.filter_by(
                snils_hash = md5(
                form.snils.data.lower().encode('utf-8')).hexdigest()).first()
        if patient is None:
            patient = Patients(
            clinic_id = form.clinic_id.data,
            birthdate = form.birthdate.data,
            sex = form.sex.data
            )
            patient.get_snils_hash(form.snils.data)
            db.session.add(patient)
            db.session.commit()
            session['known'] = False
            flash('Данные сохранены', category='info')
        else:
            session['known'] = True
            flash('Пациент с указанным СНИЛС уже есть в базе', category='warning')
        return redirect(url_for('main.patient_data_enter'))

    return render_template('patient_data_enter.html', form = form, known = session.get('known',False))
