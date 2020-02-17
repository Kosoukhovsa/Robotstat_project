from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import Users


class PatientForm(FlaskForm):
    snils = StringField('СНИЛС')
    #ClinicID_field = SelectField('Клиника', coerce=int)
    clinic_id = SelectField('Клиника', choices=[('1','Клиника 1'),('2','Клиника 2')],
                                    validators=[DataRequired()])
    birthdate = DateField('Дата рождения', format='%d-%m-%Y')
    sex = SelectField('Пол',choices=[('M','М'),('F','Ж')],
                                    validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('Сохранить')
