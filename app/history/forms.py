from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField,\
                    RadioField, DecimalField, FieldList, FormField, IntegerField,\
                    TextField

from wtforms.fields.html5 import DateField
from wtforms.fields import TextField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length, Regexp
from app.models import Patients, Clinics, ResearchGroups, Reasons, DiagnosesItems, Doctors, Events, Prosthesis



# -- Форма фильтрации историй болезни
class HistoryFilterForm(FlaskForm):
    snils_filter = StringField('СНИЛС пациента', validators=[DataRequired()])
    clinic_filter = SelectField('Клиника', coerce = int, validators=[DataRequired()])
    submit_filter = SubmitField('Фильтр')

    def __init__(self, *args, **kwargs):
        super(HistoryFilterForm, self).__init__(*args, **kwargs)
        self.clinic_filter.choices=[(clinic.id, clinic.description)
                              for clinic in Clinics.query.order_by(Clinics.id).all()]



# -- Форма фильтрации историй болезни
class HistoryMainForm(FlaskForm):
    hist_number = StringField('Номер истории болезни', validators=[DataRequired()])
    date_in = DateField('Дата открытия', validators=[DataRequired()])
    clinic = SelectField('Клиника', coerce = int, validators=[DataRequired()])
    snils = StringField('СНИЛС', validators=[DataRequired()])
    birthdate = DateField('Дата рождения', validators=[DataRequired()])
    sex = SelectField('Пол', coerce = str, validators=[DataRequired()])
    research_group = SelectField('Группа исследования', coerce = int, validators=[DataRequired()])
    doctor_researcher = SelectField('Врач-исследователь', coerce = int, validators=[DataRequired()])
    date_research_in = DateField('Дата включения в исследование',validators=[Optional()])
    date_research_out = DateField('Дата исключения из исследования',validators=[Optional()])
    reason = SelectField('Причина исключения из исследования', coerce = int, validators=[Optional()])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(HistoryMainForm, self).__init__(*args, **kwargs)
        self.clinic.choices=[(clinic.id, clinic.description)
                              for clinic in Clinics.query.order_by(Clinics.id).all()]
        self.research_group.choices=[(rg.id, rg.description)
                              for rg  in ResearchGroups.query.order_by(ResearchGroups.id).all()]
        self.reason.choices=[(r.id, r.description)
                              for r  in Reasons.query.order_by(Reasons.id).all()]
        self.sex.choices=[('1','Male'),('2','Female')]
        self.doctor_researcher.choices=[(doctor.id, doctor.fio)
                              for doctor in Doctors.query.order_by(Doctors.fio).all()]

# -- Форма для значений показателей
class IndicatorItemForm(FlaskForm):
    num_value = IntegerField('Число', validators=[DataRequired()])
    comment = StringField('СНИЛС', validators=[DataRequired()])


class IndicatorsForm(FlaskForm):
    #hist_number = StringField('Номер истории болезни', validators=[DataRequired())
    date_begin = DateField('Дата')

class TelerentgenographyForm(FlaskForm):
    #hist_number = StringField('Номер истории болезни', validators=[DataRequired())
    date_begin = DateField('Дата')

class PreoperativeForm(FlaskForm):
    #hist_number = StringField('Номер истории болезни', validators=[DataRequired())
    date_begin = DateField('Дата')

# -- Основной диагноз
class HistoryMainDiagnosForm(FlaskForm):
    diagnos = SelectField('Диагноз', coerce = int, validators=[DataRequired()])
    side_damage = SelectField('Сторона поражения', coerce = str, validators=[DataRequired()])
    date_created = DateField('Дата назначения', validators=[DataRequired()])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(HistoryMainDiagnosForm, self).__init__(*args, **kwargs)
        self.diagnos.choices=[(diagnos.id, diagnos.description)
                              for diagnos in DiagnosesItems.query.filter(DiagnosesItems.type=='Основной').order_by(DiagnosesItems.id).all()]
        self.side_damage.choices=[('Левая','Левая'),('Правая','Правая')]

# -- Сопутствующий диагноз
class HistoryOtherDiagnosForm(FlaskForm):
    diagnos = SelectField('Диагноз', coerce = int, validators=[DataRequired()])
    date_created = DateField('Дата назначения', validators=[DataRequired()])
    submit = SubmitField('Добавить')

    def __init__(self, *args, **kwargs):
        super(HistoryOtherDiagnosForm, self).__init__(*args, **kwargs)
        self.diagnos.choices=[(diagnos.id, diagnos.description)
                              for diagnos in DiagnosesItems.query.filter(DiagnosesItems.type=='Сопутствующий').order_by(DiagnosesItems.id).all()]

# -- Амбулаторный прием - заголовок
class AmbulanceMainForm(FlaskForm):
    doctor = SelectField('Доктор', coerce = int, validators=[DataRequired()])
    event = SelectField('Вид амбулаторного приема', coerce = int, validators=[DataRequired()])
    date_begin = DateField('Дата приема', validators=[DataRequired()])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(AmbulanceMainForm, self).__init__(*args, **kwargs)
        self.doctor.choices=[(doctor.id, doctor.fio)
                              for doctor in Doctors.query.order_by(Doctors.fio).all()]
        self.event.choices=[(event.id, event.description)
                              for event in Events.query.filter(Events.type=='2').order_by(Events.id).all()]


# -- История болезни: список амбулаторных приемов. Создание нового
class HistioryNewAmbulanceForm(FlaskForm):
    event = SelectField('Вид амбулаторного приема', coerce = int, validators=[DataRequired()])
    submit = SubmitField('Создать')

    def __init__(self, *args, **kwargs):
        super(HistioryNewAmbulanceForm, self).__init__(*args, **kwargs)
        self.event.choices=[(event.id, event.description)
                              for event in Events.query.filter(Events.type=='2').order_by(Events.id).all()]

class ProsthesisForm(FlaskForm):
    prosthesis = SelectField('Протез', coerce = int, validators=[DataRequired()])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(ProsthesisForm, self).__init__(*args, **kwargs)
        self.prosthesis.choices=[(prosthesis.id, prosthesis.description)
                              for prosthesis in Prosthesis.query.all()]

# Общие сведения о госпитализации
class HospitalSubForm1(FlaskForm):
    date_begin = DateField('Дата госпитализации', validators=[DataRequired()])
    date_end = DateField('Дата выписки')
    doctor = SelectField('Лечащий врач', coerce = int, validators=[DataRequired()])
    doctor_chief = SelectField('Заведующий отделением', coerce = int, validators=[DataRequired()])
    days1 = IntegerField('Койко-день')
    days2 = IntegerField('Предоперационный койко-день ')
    days3 = IntegerField('Послеоперационный койко-день ')
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(HospitalSubForm1, self).__init__(*args, **kwargs)
        self.doctor.choices=[(doctor.id, doctor.fio)
                              for doctor in Doctors.query.order_by(Doctors.fio).all()]
        self.doctor_chief.choices=[(doctor.id, doctor.fio)
                              for doctor in Doctors.query.order_by(Doctors.fio).all()]

# -- История болезни: список госпитализаций. Создание новой
class NewHospitalForm(FlaskForm):
    submit = SubmitField('Создать')

# -- Госпитализация: общие сведения о пациенте
class HospitalSubForm2(FlaskForm):
    date_begin = DateField('Дата', validators=[DataRequired])
    claims = SelectField('Жалобы', coerce = str, validators=[DataRequired])
    claims_time = SelectField('Анамнез заболевания: жалобы в течение ', coerce = str, validators=[DataRequired])
    diseases = SelectField('Перенесенные заболевания', coerce = str, validators=[DataRequired])
    traumas = SelectField('Операции, травмы', coerce = str, validators=[DataRequired])
    smoking = SelectField('Курение', coerce = str, validators=[DataRequired])
    alcohol = SelectField('Алкоголь', coerce = str, validators=[DataRequired])
    allergy = SelectField('Аллергологический анамнез', coerce = str, validators=[DataRequired])
    genetic = SelectField('Наследственные заболевания', coerce = str, validators=[DataRequired])
    save_indicators = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(HospitalSubForm2, self).__init__(*args, **kwargs)
        self.claims.choices=[('Да','Да'),('Нет','Нет')]
        self.claims_time.choices=[('до 1 года','до 1 года'),('от 1 до 3 лет','от 1 до 3 лет'),\
                                  ('от 3 до 5 лет','от 3 до 5 лет'),\
                                  ('более 5 лет','более 5 лет')]
        self.traumas.choices=[('Да','Да'),('Нет','Нет')]
        self.diseases.choices=[('Да','Да'),('Нет','Нет')]
        self.smoking.choices=[('Да','Да'),('Нет','Нет')]
        self.alcohol.choices=[('Часто','Часто'),('Редко','Редко')]
        self.allergy.choices=[('Да','Да'),('Нет','Нет')]
        self.genetic.choices=[('Да','Да'),('Нет','Нет')]
