from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp
from app.models import Users, Clinics


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(),
    Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
    'Usernames must have only letters, numbers, dots or ''underscores')])
    email = StringField('Электронная почта', validators=[DataRequired(), Email()])
    clinic = SelectField('Клиника', coerce=int)
    password1 = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField('Зарегистрироваться')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.clinic.choices=[(clinic.id, clinic.description)
                              for clinic in Clinics.query.order_by(Clinics.id).all()]


    def validate_username(self, username):
        user = Users.query.filter_by(username = username.data).first()
        if user is not None:
            raise ValidationError(f'User: {username.data} already exists!')

    def validate_email(self, email):
        user = Users.query.filter_by(email = email.data).first()
        if user is not None:
            raise ValidationError(f'User with this email: {email.data} already exists!')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request password reset')

class ResetPasswordForm(FlaskForm):
    password=PasswordField('Password', validators=[DataRequired()])
    password2=PasswordField('Repeat password', validators=[DataRequired(),
                            EqualTo('password')])
    submit=SubmitField('Password reset')
