from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp
from app.models import Users, Clinics, Roles, UserRoles

# -- Клиники
class ClinicsForm(FlaskForm):
    clinic = StringField('Клиника', validators=[DataRequired()])
    action = RadioField('Действие', choices=[(1,'Добавить'),(2,'Удалить')], default=1, coerce=int)
    submit_ok = SubmitField('Ok')

# -- Группы обследования
class ResearchGroupForm(FlaskForm):
    description = StringField('Наименование', validators=[DataRequired()])
    clinic = SelectField('Клиника', coerce = int, validators=[DataRequired()])    
    submit_ok = SubmitField('Добавить')

    def __init__(self, *args, **kwargs):
        super(ResearchGroupForm, self).__init__(*args, **kwargs)
        self.clinic.choices=[(clinic.id, clinic.description)
                              for clinic in Clinics.query.order_by(Clinics.id).all()]

class ResearchGroupFilterForm(FlaskForm):
    clinic_filter = SelectField('Клиника', coerce = int)
    submit_filter = SubmitField('Фильтр')

    def __init__(self, *args, **kwargs):
        super(ResearchGroupFilterForm, self).__init__(*args, **kwargs)
        self.clinic_filter.choices=[(clinic.id, clinic.description)
                              for clinic in Clinics.query.order_by(Clinics.id).all()]
        self.clinic_filter.choices.insert(0,(0,'All'))



# -- Роли пользователей
class UserRoleForm(FlaskForm):
    user = SelectField('Имя пользователя', coerce = int, validators=[DataRequired()])
    role = SelectField('Роль', coerce = int, validators=[DataRequired()])
    action = RadioField('Действие', choices=[(1,'Добавить'),(2,'Удалить')], default=1, coerce=int)
    submit_ok = SubmitField('Ok')

    def __init__(self, *args, **kwargs):
        super(UserRoleForm, self).__init__(*args, **kwargs)
        self.user.choices=[(user.id, user.username)
                              for user in Users.query.order_by(Users.id).all()]
        self.role.choices=[(role.id, role.description)
                              for role in Roles.query.order_by(Roles.id).all()]


class UserRoleFilterForm(FlaskForm):
    user_filter = SelectField('Пользователи', coerce = int)
    role_filter = SelectField('Роли', coerce = int)
    submit_filter = SubmitField('Фильтр')

    def __init__(self, *args, **kwargs):
        super(UserRoleFilterForm, self).__init__(*args, **kwargs)
        self.user_filter.choices=[(user.id, user.username)
                              for user in Users.query.order_by(Users.id).all()]
        self.user_filter.choices.insert(0,(0,'All'))
        self.role_filter.choices=[(role.id, role.description)
                              for role in Roles.query.order_by(Roles.id).all()]
        self.role_filter.choices.insert(0,(0,'All'))
