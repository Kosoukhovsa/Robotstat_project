from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField,\
                    RadioField, DecimalField, FieldList, FormField, IntegerField
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
