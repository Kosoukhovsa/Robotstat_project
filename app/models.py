from app import db, login_manager
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from hashlib import md5
#from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import jwt
from time import time
from datetime import datetime


@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))

# Роли пользователей
class UserRoles(db.Model):
    __tablename__= 'UserRoles'
    id = db.Column(db.Integer(), primary_key = True)
    user = db.Column(db.Integer(), db.ForeignKey('Users.id'))
    role = db.Column(db.Integer(), db.ForeignKey('Roles.id'))
    time_created = db.Column(db.DateTime(), default=datetime.utcnow())

    @staticmethod
    def insert_user_roles(user_roles):
        if user_roles is None:
            user_roles = {"admin":"ADMIN",
                "doctor":"HIST_W",
                "researcher":"DATA_R",
                "researcher":"DATA_D"}
        for (k,v) in user_roles.items():
            user_role=UserRoles()
            user_role.user=Users.query.filter_by(username=k).first().id
            user_role.role=Roles.query.filter_by(permissions=v).first().id
            user_role.time_created = datetime.utcnow()
            db.session.add(user_role)
        db.session.commit()

# Пользователи
class Users(db.Model, UserMixin):
    __tablename__ = 'Users'
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100),index=True, unique=True)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'))
    time_create = db.Column(db.DateTime(), default=datetime.utcnow())
    password=db.Column(db.String(100))
    password_hash=db.Column(db.String(128))
    last_visit = db.Column(db.DateTime(), default=datetime.utcnow())
    confirmed=db.Column(db.Boolean(), default=False)
    roles = db.relationship('UserRoles', foreign_keys=[UserRoles.user],
                            backref=db.backref('users', lazy='joined'),
                            lazy='dynamic')

    def __repr__(self):
        return f'Пользователь {self.username}'

    #@property
    #def password(self):
    #    raise AttributeError('password is not a readable attribute')

    #@password.setter
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return(check_password_hash(self.password_hash, password))

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password':self.id, 'exp':time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id= jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return Users.query.get(id)


    @staticmethod
    def insert_users():
        users = {"admin":{"username":"admin","email":"ikpservicemail@gmail.com","password":"admin","clinic":"1"},
                "doctor":{"username":"doctor","email":"ikp_doctor@gmail.com","password":"doctor","clinic":"1"},
            "researcher":{"username":"researcher","email":"ikp_researcher@gmail.com","password":"researcher","clinic":"1"}}
        for (k,v) in users.items():
            user=Users(username=v['username'],email=v['email'],password=v['password'])
            user.set_password(v["password"])
            user.time_create = datetime.utcnow()
            user.clinic = Clinics.query.get(v["clinic"]).id
            db.session.add(user)
        db.session.commit()

    def has_permissions(self, permission):
        if self.is_admin():
            return True
        user_role = UserRoles.query.filter_by(user=current_user.id, role=Roles.query.filter_by(permissions=permission).first().id).first()
        if user_role is None:
            return False
        return True

    def is_admin(self):
        current_user_is_admin = UserRoles.query.filter_by(user=current_user.id, role = Roles.query.filter_by(is_admin = True).first().id).first()
        if current_user_is_admin is None:
            return False
        return True

    def ping(self):
        self.last_visit = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

# Роли
class Roles(db.Model):
    __tablename__ = 'Roles'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=True)
    permissions = db.Column(db.String(10), index=True)
    is_admin = db.Column(db.Boolean(), index=True)
    users = db.relationship('UserRoles', foreign_keys=[UserRoles.role],
                            backref=db.backref('roles', lazy='joined'),
                            lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles={'Ведение справочников':{'permission':'REF_W', 'is_admin':False},
               'Просмотр справочников':{'permission':'REF_R', 'is_admin':False},
               'Ведение истории болезни':{'permission':'HIST_W', 'is_admin':False},
               'Чтение истории болезни':{'permission':'HIST_R', 'is_admin':False},
               'Отчеты просмотр':{'permission':'REP_R', 'is_admin':False},
               'Отчеты выгрузка':{'permission':'REP_D', 'is_admin':False},
               'Анализ данных просмотр':{'permission':'DATA_R', 'is_admin':False},
               'Анализ данных выгрузка':{'permission':'DATA_D', 'is_admin':False},
               'Администрирование':{'permission':'ADMIN', 'is_admin':True}}

        for (k,v) in roles.items():
            role = Roles.query.filter_by(description=k).first()
            if role is None:
                role = Roles(description=k, permissions=v['permission'],is_admin=v['is_admin'])
                db.session.add(role)
        db.session.commit()

# Клиники
class Clinics(db.Model):
    __tablename__ = 'Clinics'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100))
    users = db.relationship('Users',backref='clinic_of_users',lazy='dynamic')
    research_groups = db.relationship('ResearchGroups',backref='clinic_of_re_groups', lazy='dynamic')

    def __repr__(self):
        return f'Клиника {self.description}'


    @staticmethod
    def insert_clinics(dict_clinics):

        # Заполнение справочника групп из словаря
        # Сначала удаление значений справочника
        Clinics.query.delete()
        for i in dict_clinics:
            new_c = Clinics(id=i['id'],
                             description=i['description'])
            db.session.add(new_c)
        db.session.commit()


# Группы исследования

class ResearchGroups(db.Model):
    __tablename__ = 'ResearchGroups'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=False)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'))

    @staticmethod
    def insert_ResearchGroups(dict_rgroups):
    # Заполнение справочника групп из словаря
    # Сначала удаление значений справочника
        ResearchGroups.query.delete()
        for i in dict_rgroups:
            new_group = ResearchGroups(id=i['id'],
                                        description=i['description'],
                                        clinic=i['clinic'])
            db.session.add(new_group)
        db.session.commit()



# Причины исключения из исследования
class Reasons(db.Model):
    __tablename__ = 'Reasons'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(300), unique=True)

# Диагнозы

class DiagnosesItems(db.Model):
    __tablename__ = 'DiagnosesItems'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=True)
    mkb10 = db.Column(db.String(20), unique=False)
    type = db.Column(db.String(30), unique=False, index = True)


# Врачи
class Doctors(db.Model):
    __tablename__ = 'Doctors'
    id = db.Column(db.Integer(), primary_key=True)
    first_name = db.Column(db.String(100), unique=False)
    second_name = db.Column(db.String(100), unique=False)
    fio = db.Column(db.String(100), unique=False)

# Протезы
class Prosthesis(db.Model):
    __tablename__ = 'Prosthesis'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=False)
    firm = db.Column(db.String(100), unique=False)
    type = db.Column(db.String(100), unique=False)

# Осложнения
class Complications(db.Model):
    __tablename__ = 'Complications'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=False)
    type = db.Column(db.String(100), unique=False, index = True)

"""
# Справочник исключен
# Виды операций
class OperationTypes(db.Model):
    __tablename__ = 'OperationTypes'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=False)
"""

# Этапы операций
class OperationSteps(db.Model):
    __tablename__ = 'OperationSteps'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=False)
    order = db.Column(db.Integer(), unique=True)

# Наблюдения
class Events(db.Model):
    __tablename__ = 'Events'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=False)
    type = db.Column(db.String(100), unique=False, index = True)

"""
# Справочник исключен
# Список обследований
class Checkups(db.Model):
    __tablename__ = 'Checkups'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=False)
    is_mandatory = db.Column(db.Boolean(), unique=False, index = True)
"""


# Группы Показателей
class IndicatorsGroups(db.Model):
    __tablename__ = 'IndicatorsGroups'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=False)
    indicators = db.relationship('Indicators', backref='groups', lazy='dynamic')

# Показатели
class Indicators(db.Model):
    __tablename__ = 'Indicators'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(300), unique=False)
    is_calculated = db.Column(db.Boolean)
    group = db.Column(db.Integer(), db.ForeignKey('IndicatorsGroups.id'), index = True)
    unit = db.Column(db.String(20), unique=False)
    type = db.Column(db.String(20), unique=False)
    def_values = db.relationship('IndicatorsDefs', backref='def_indicators')
    norm_values = db.relationship('IndicatorsNorms', backref='norm_indicators')

    #def __init__(self):
        # Здесь нужно прописать формулы для расчета показателей
    #    pass


# Допустимые значения показателей
class IndicatorsDefs(db.Model):
    __tablename__='IndicatorsDefs'
    id=db.Column(db.Integer(), primary_key=True)
    indicator = db.Column(db.Integer(), db.ForeignKey('Indicators.id'), index = True)
    text_value = db.Column(db.String(100), unique=False)
    num_value = db.Column(db.Numeric())
    id_value =db.Column(db.Integer(), unique=False)

# Нормативные значения показателей
class IndicatorsNorms(db.Model):
    __tablename__='IndicatorsNorms'
    id=db.Column(db.Integer(), primary_key=True)
    indicator = db.Column(db.Integer(), db.ForeignKey('Indicators.id'), index = True)
    nvalue_from = db.Column(db.Numeric())
    nvalue_to = db.Column(db.Numeric())

# Пациенты
class Patients(db.Model):
    __tablename__ = 'Patients'
    id = db.Column(db.Integer(), primary_key=True)
    snils_hash =db.Column(db.String(128), unique=False)
#     clinic_id = db.Column(db.Integer(), db.ForeignKey('Clinics.id'))
#     patient_snils = db.Column(db.String(11))
#     #fio = db.Column(db.String(100))
    birthdate = db.Column(db.Date())
    sex = db.Column(db.String(1), index=True)
    histories = db.relationship('Histories', backref='patients')

#  Создание хэш-значения для СНИЛС
    @staticmethod
    def get_snils_hash(snils):
        digest = md5(snils.lower().encode('utf-8')).hexdigest()
        return digest

#  Проверка наличия пациента в базе
    @staticmethod
    def get_patient_by_snils(digest):
        f_patient = Patients.query.filter(Patients.snils_hash==digest).first()
        if f_patient is None:
            return(None)
        else:
            return(f_patient)


# Анкеты
class Profiles(db.Model):
    __tablename__ = 'Profiles'
    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(100), unique=False)
    items = db.relationship('ProfileItems', backref='profiles', lazy='dynamic')

# Вопросы анкет
class ProfileItems(db.Model):
    __tablename__ = 'ProfileItems'
    id = db.Column(db.Integer(), primary_key=True)
    profile= db.Column(db.Integer(), db.ForeignKey('Profiles.id'), index = True)
    description = db.Column(db.String(100), unique=False)
    answers = db.relationship('ProfilesAnswers', backref='items', lazy='dynamic')
    item_group = db.Column(db.String(100))

# Возможные Ответы на вопросы анкет
class ProfilesAnswers(db.Model):
    __tablename__ = 'ProfilesAnswers'
    id = db.Column(db.Integer(), primary_key=True)
    profile= db.Column(db.Integer(), db.ForeignKey('Profiles.id'), index = True)
    profile_item= db.Column(db.Integer(), db.ForeignKey('ProfileItems.id'))
    response = db.Column(db.String(100), unique=False)
    response_value = db.Column(db.Numeric())

# Транзакционные таблицы
# Истории болезни
class Histories(db.Model):
    __tablename__='Histories'
    id = db.Column(db.Integer(), primary_key=True)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'), index = True)
    hist_number = db.Column(db.String(100), unique=False)
    time_created = db.Column(db.DateTime(), default=datetime.utcnow())
    date_in = db.Column(db.Date())
    patient = db.Column(db.Integer(), db.ForeignKey('Patients.id'))
    research_group = db.Column(db.Integer(), db.ForeignKey('ResearchGroups.id'), index = True)
    doctor_researcher = db.Column(db.Integer(), db.ForeignKey('Doctors.id'), index = True)
    date_research_in = db.Column(db.Date())
    date_research_out = db.Column(db.Date())
    reason = db.Column(db.Integer(), db.ForeignKey('Reasons.id'))

# События в рамках истории болезни
class HistoryEvents(db.Model):
    __tablename__='HistoryEvents'
    id = db.Column(db.Integer(), primary_key=True)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'))
    history = db.Column(db.Integer(), db.ForeignKey('Histories.id'))
    patient = db.Column(db.Integer(), db.ForeignKey('Patients.id'))
    event = db.Column(db.Integer(), db.ForeignKey('Events.id'), index = True)
    date_begin = db.Column(db.Date())
    date_end = db.Column(db.Date())
    doctor = db.Column(db.Integer(), db.ForeignKey('Doctors.id'), index = True)
    doctor_researcher = db.Column(db.Integer(), db.ForeignKey('Doctors.id'), index = True)
    doctor_chief = db.Column(db.Integer(), db.ForeignKey('Doctors.id'), index = True)
    days1 = db.Column(db.Integer()) #койко-день
    days2 = db.Column(db.Integer()) #предоперационный койко-день
    days3 = db.Column(db.Integer()) #послеоперационный койко-день


    def get_indicators_values(self, indicators_group, **kwargs):
        """
        Выбор показателей события
        Параметры:
        indicators_group - код группы
        indicators_list - список показателей (опционально)

        """
        indicators_list = kwargs.get('indicators_list',None)

        # Выбор всех показателей из группы
        indicators_values = IndicatorValues.query.join(Indicators, IndicatorValues.indicator==Indicators.id).\
                    filter(IndicatorValues.history_event==self.id, Indicators.group==indicators_group).all()

        items = []
        for i in indicators_values:
            indicator = Indicators.query.get(i.indicator)
            if indicators_list and indicator.id not in indicators_list:
                continue
            indicator_norms = IndicatorsNorms.query.filter(IndicatorsNorms.indicator==indicator.id).first()
                # Это физические параметры,
                #       телерентгенография
            item = {}
            item['id'] = i.id
            item['indicator'] = i.indicator
            item['slice'] = i.slice
            item['description'] = indicator.description
            if i.num_value == None:
                item['num_value'] = 0
            else:
                if indicator.type == 'integer':
                    item['num_value'] = int(i.num_value)
                else:
                    item['num_value'] = i.num_value
            if i.comment == None:
                item['comment'] = ''
            else:
                item['comment'] = i.comment
            if i.text_value == None:
                item['text_value'] = ''
            else:
                item['text_value'] = i.text_value
            if indicator.unit == None:
                item['unit'] = ''
            else:
                item['unit'] = indicator.unit
            if indicator_norms:
                item['nvalue_from'] = indicator_norms.nvalue_from
                item['nvalue_to'] = indicator_norms.nvalue_from
            items.append(item)

        return(items)


# Диагнозы
class Diagnoses(db.Model):
    __tablename__='Diagnoses'
    id = db.Column(db.Integer(), primary_key=True)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'), index = True)
    history = db.Column(db.Integer(), db.ForeignKey('Histories.id'), index = True)
    patient = db.Column(db.Integer(), db.ForeignKey('Patients.id'))
    diagnose = db.Column(db.Integer(), db.ForeignKey('DiagnosesItems.id'))
    side_damage = db.Column(db.String(100))
    date_created = db.Column(db.Date())
    prothes = db.Column(db.Integer(), db.ForeignKey('Prosthesis.id'))

# Фактические значения показателей пациентов
class IndicatorValues(db.Model):
    __tablename__='IndicatorValues'
    id = db.Column(db.Integer(), primary_key=True)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'), index = True)
    history = db.Column(db.Integer(), db.ForeignKey('Histories.id'), index = True)
    patient = db.Column(db.Integer(), db.ForeignKey('Patients.id'))
    history_event = db.Column(db.Integer(), db.ForeignKey('HistoryEvents.id'))
    indicator = db.Column(db.Integer(), db.ForeignKey('Indicators.id'))
    slice = db.Column(db.String(100))
    time_created = db.Column(db.DateTime(), default=datetime.utcnow())
    date_value = db.Column(db.Date())
    text_value = db.Column(db.String(100))
    num_value = db.Column(db.Numeric())
    num_deviation = db.Column(db.Numeric())
    comment = db.Column(db.String(500))

# Операции
class Operations(db.Model):
    __tablename__='Operations'
    id = db.Column(db.Integer(), primary_key=True)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'), index = True)
    history = db.Column(db.Integer(), db.ForeignKey('Histories.id'))
    patient = db.Column(db.Integer(), db.ForeignKey('Patients.id'))
    doctor_surgeon = db.Column(db.Integer(), db.ForeignKey('Doctors.id'))
    doctor_assistant = db.Column(db.Integer(), db.ForeignKey('Doctors.id'))
    operation_order = db.Column(db.Integer())
    time_begin = db.Column(db.DateTime())
    time_end = db.Column(db.DateTime())
    duration_min = db.Column(db.Integer()) # Длительность в минутах

# Журнал операции
class OperationLog(db.Model):
    __tablename__='OperationLog'
    id = db.Column(db.Integer(), primary_key=True)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'), index = True)
    history = db.Column(db.Integer(), db.ForeignKey('Histories.id'))
    patient = db.Column(db.Integer(), db.ForeignKey('Patients.id'))
    operation = db.Column(db.Integer(), db.ForeignKey('Operations.id'))
    operation_step = db.Column(db.Integer(), db.ForeignKey('OperationSteps.id'))
    time_begin = db.Column(db.DateTime())
    time_end = db.Column(db.DateTime())
    duration_min = db.Column(db.Integer()) # Длительность в минутах

# Осложнения операции
class OperationComp(db.Model):
    __tablename__='OperationComp'
    id = db.Column(db.Integer(), primary_key=True)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'), index = True)
    history = db.Column(db.Integer(), db.ForeignKey('Histories.id'))
    patient = db.Column(db.Integer(), db.ForeignKey('Patients.id'))
    operation = db.Column(db.Integer(), db.ForeignKey('Operations.id'))
    complication = db.Column(db.Integer(), db.ForeignKey('Complications.id'))
    date_begin = db.Column(db.Date())


# Осложнения операции
class ProfileResponses(db.Model):
    __tablename__='ProfileResponses'
    id = db.Column(db.Integer(), primary_key=True)
    clinic = db.Column(db.Integer(), db.ForeignKey('Clinics.id'), index = True)
    history = db.Column(db.Integer(), db.ForeignKey('Histories.id'))
    patient = db.Column(db.Integer(), db.ForeignKey('Patients.id'))
    history_event = db.Column(db.Integer(), db.ForeignKey('HistoryEvents.id'))
    profile = db.Column(db.Integer(), db.ForeignKey('Profiles.id'), index = True)
    profile_item= db.Column(db.Integer(), db.ForeignKey('ProfileItems.id'))
    response = db.Column(db.String(100), unique=False)
    response_value = db.Column(db.Numeric())


class LoadDictionary():

    def __init__(self, dict_list):
        self.dict_list = dict_list

    # Метод позволяет выбрать нужный справочник и загрузить его
    def switch_load(self,dict_name):
        default = "Метод загрузки отсутствует"
        return getattr(self, 'load_'+str(dict_name), lambda: default)()

    def default(self):
        return ''

    def load_Clinics(self):
        # Заполнение справочника групп из словаря
        # Сначала удаление значений справочника
        Clinics.query.delete()
        for i in self.dict_list:
            new_c = Clinics(id=i['id'],
                             description=i['description'])
            db.session.add(new_c)
        db.session.commit()

    def load_Reasons(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        Reasons.query.delete()
        for i in self.dict_list:
            new_c = Reasons(id=i['id'],
                             description=i['description'])
            db.session.add(new_c)
        db.session.commit()

    def load_DiagnosesItems(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        DiagnosesItems.query.delete()
        for i in self.dict_list:
            new_c = DiagnosesItems(id=i['id'],
                             description=i['description'],
                             mkb10=i['mkb10'],
                             type=i['type'])
            db.session.add(new_c)
        db.session.commit()

    def load_Roles(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        Roles.query.delete()
        for i in self.dict_list:
            new_c = Roles(id=i['id'],
                             description=i['description'],
                             permissions=i['permissions'],
                             is_admin=i['is_admin'])
            db.session.add(new_c)
        db.session.commit()


    def load_Prosthesis(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        Prosthesis.query.delete()
        for i in self.dict_list:
            new_c = Prosthesis(id=i['id'],
                             description=i['description'],
                             firm=i['firm'],
                             type=i['type'])
            db.session.add(new_c)
        db.session.commit()

    def load_Complications(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        Complications.query.delete()
        for i in self.dict_list:
            new_c = Complications(id=i['id'],
                             description=i['description'],
                             type=i['type'])
            db.session.add(new_c)
        db.session.commit()

    def load_ResearchGroups(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        ResearchGroups.query.delete()
        for i in self.dict_list:
            new_c = ResearchGroups(id=i['id'],
                             description=i['description'],
                             clinic=i['clinic'])
            db.session.add(new_c)
        db.session.commit()

    def load_Users(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        ResearchGroups.query.delete()
        for i in self.dict_list:
            new_c = ResearchGroups(id=i['id'],
                             description=i['description'],
                             clinic=i['clinic'])
            db.session.add(new_c)
        db.session.commit()

    def load_Doctors(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        Doctors.query.delete()
        for i in self.dict_list:
            new_c = Doctors(id=i['id'],
                            first_name=i['first_name'],
                            second_name=i['second_name'],
                            fio=i['fio']
                            )
            db.session.add(new_c)
        db.session.commit()


    def load_Indicators(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        Indicators.query.delete()
        for i in self.dict_list:
            new_c = Indicators(id=i['id'],
                               description=i['description'],
                               is_calculated=i['is_calculated'],
                               group=i['group'],
                               unit=i['unit'],
                               type=i['type']
                               )
            db.session.add(new_c)
        db.session.commit()


    def load_IndicatorsDefs(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        IndicatorsDefs.query.delete()
        for i in self.dict_list:
            new_c = IndicatorsDefs(id=i['id'],
                                   indicator=i['indicator'],
                                   text_value=i['text_value'],
                                   num_value=i['num_value'],
                                   id_value=i['id_value']
                                   )
            db.session.add(new_c)
        db.session.commit()

    def load_IndicatorsGroups(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        IndicatorsGroups.query.delete()
        for i in self.dict_list:
            new_c = IndicatorsGroups(id=i['id'],
                                   description=i['description']
                                   )
            db.session.add(new_c)
        db.session.commit()

    def load_IndicatorsNorms(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        IndicatorsNorms.query.delete()
        for i in self.dict_list:
            new_c = IndicatorsNorms(id=i['id'],
                                   indicator=i['indicator'],
                                   nvalue_from=i['nvalue_from'],
                                   nvalue_to=i['nvalue_to']
                                   )
            db.session.add(new_c)
        db.session.commit()

    def load_Events(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        Events.query.delete()
        for i in self.dict_list:
            new_c = Events(
                           id=i['id'],
                           description=i['description'],
                           type=i['type']
                           )
            db.session.add(new_c)
        db.session.commit()


    def load_OperationSteps(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        OperationSteps.query.delete()
        for i in self.dict_list:
            new_c = OperationSteps(
                           id=i['id'],
                           description=i['description'],
                           order=i['order']
                           )
            db.session.add(new_c)
        db.session.commit()

    """
    # Справочник исключен
    def load_Checkups(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        Checkups.query.delete()
        for i in self.dict_list:
            new_c = Checkups(
                           id=i['id'],
                           description=i['description'],
                           is_mandatory=i['is_mandatory']
                           )
            db.session.add(new_c)
        db.session.commit()
    """
    def load_Profiles(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        Profiles.query.delete()
        for i in self.dict_list:
            new_c = Profiles(
                           id=i['id'],
                           description=i['description']
                           )
            db.session.add(new_c)
        db.session.commit()

    def load_ProfileItems(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        ProfileItems.query.delete()
        for i in self.dict_list:
            new_c = ProfileItems(
                           id=i['id'],
                           profile=i['profile'],
                           description=i['description'],
                           item_group=i['item_group']
                           )
            db.session.add(new_c)
        db.session.commit()

    def load_ProfilesAnswers(self):
        # Заполнение справочника из словаря
        # Сначала удаление значений справочника
        ProfilesAnswers.query.delete()
        for i in self.dict_list:
            new_c = ProfilesAnswers(
                           id=i['id'],
                           profile = i['profile'],
                           profile_item=i['profile_item'],
                           response=i['response']
                           )
            db.session.add(new_c)
        db.session.commit()
