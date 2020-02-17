from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from app import db
from app.admin import bp
from app.admin.forms import UserRoleForm, UserRoleFilterForm, ClinicsForm, ResearchGroupForm, ResearchGroupFilterForm
from app.models import Users, Clinics, UserRoles, Roles, ResearchGroups, LoadDictionary
from datetime import datetime
from sqlalchemy.orm.util import join
from Tools.sqltools import SqlEngine
from Tools.filetools import FileEngine
import pandas

# Список справочников
@bp.route('/admin/dict_list')
def dict_list():
    # Получить список таблиц с количеством записей
    # { table: rows }
    tables_dict = SqlEngine.GetTablesInfo(db)

    # Получить спсисок настраиваемых справочников и ограничить выводимый список только ими
    dict_list = FileEngine.GetDictList()

    only_dict = {}
    for (k,v) in tables_dict.items():
        if k in dict_list:
            only_dict[k]=v

    return render_template('admin/dict_dashboard.html', tables_dict=only_dict)

# Загрузка отделных справочников
@bp.route('/admin/dict_load/<t>', methods= ['GET','POST'])
def dict_load(t):
    # Загрузить данные из файла
    dict = FileEngine.GetListData(t)
    if dict != {}:
        ld = LoadDictionary(dict)
        ld.switch_load(t)

    return redirect(url_for('.dict_list'))

# Загрузка всех справочников
@bp.route('/admin/dict_load_all/', methods= ['GET','POST'])
def dict_load_all():
    # Загрузить список справочников  из файла
    # Получить спсисок настраиваемых справочников
    dict_list = FileEngine.GetDictList()
    for t in dict_list:
        dict = FileEngine.GetListData(t)
        if dict != {}:
            ld = LoadDictionary(dict)
            ld.switch_load(t)

    return redirect(url_for('.dict_list'))

# Функция-переключатьель ведения  справочников
@bp.route('/admin/dict_edit_switch/<t>', methods= ['GET','POST'])
def dict_edit_switch(t):

    def edit_Clinics():
        return redirect(url_for('.list_clinics'))

    def edit_ResearchGroups():
        return redirect(url_for('.research_groups_edit'))

    def default():
        return redirect(url_for('.dict_list'))

    dict_switch = {
    'Clinics':edit_Clinics,
    'ResearchGroups':edit_ResearchGroups
    }

    return dict_switch.get(t,default)()


# Справочник Клиник
@bp.route('/admin/lists/clinics', methods= ['GET','POST'])
def list_clinics():
    Form = ClinicsForm()
    page = request.args.get('page',1,type=int)
    pagination = Clinics.query.paginate(page,5,error_out=False)
    clinic_list = pagination.items
    if Form.submit_ok.data and Form.validate_on_submit():
        if Form.action.data==1:
            clinic = Clinics(description=Form.clinic.data)
            db.session.add(clinic)
            db.session.commit()
            flash('Клиника добавлена', category='info')
        if Form.action.data==2:
            #clinic = Clinics.query.filter_by(description=Form.clinic.data).first()
            #if clinic:
            #    db.session.delete(clinic)
            #    db.session.commit()
            #    flash('Клиника удалена', category='info')
            flash('Удаление клиник запрещено!', category='error')
        return redirect(url_for('.list_clinics'))
    return render_template('admin/clinics.html',pagination=pagination, title = 'Ведение списка клиник', Form=Form, clinic_list = clinic_list)

# Справочник Групп исследования
@bp.route('/research_groups_edit', methods = ['GET','POST'])
def research_groups_edit():
    GroupForm = ResearchGroupForm()
    GroupFilterForm = ResearchGroupFilterForm()
    page = request.args.get('page',1,type=int)

    clinic_filter_id = session.get('clinic_filter_id')
    group_list = ResearchGroups.query
    if clinic_filter_id is not None:
        group_list = group_list.filter(ResearchGroups.clinic==clinic_filter_id)

    pagination =  group_list.paginate(page,5,error_out=False)
    groups = pagination.items

    if GroupForm.submit_ok.data and GroupForm.validate_on_submit():
# Обработка удаления и добавления данных

        group = ResearchGroups.query.filter(ResearchGroups.description==GroupForm.description.data,
                                            ResearchGroups.clinic==GroupForm.clinic.data).first()
        if group is not None:
            flash('Данная группа уже существует', category='warning')
        elif group is None:
            new_group = ResearchGroups(clinic=GroupForm.clinic.data, description=GroupForm.description.data)
            db.session.add(new_group)
            db.session.commit()
            flash('Группа создана', category='info')

        return redirect(url_for('.research_groups_edit'))
    if GroupFilterForm.submit_filter.data and GroupFilterForm.validate_on_submit():
# Фильтрация списка
        group_list = ResearchGroups.query
        if GroupFilterForm.clinic_filter.data != 0:
# Выбрано значение ( не All)
            group_list = group_list.filter(ResearchGroups.clinic==GroupFilterForm.clinic_filter.data)
            session['clinic_filter_id']= GroupFilterForm.clinic_filter.data

# Выбрано значение ALL - снять фильтр
        if GroupFilterForm.clinic_filter.data == 0:
            session['clinic_filter_id'] = None

        pagination =  group_list.paginate(page,5,error_out=False)
        groups = pagination.items


    return render_template('admin/research_groups.html', GroupForm=GroupForm, GroupFilterForm=GroupFilterForm, groups=groups,
                            title='Группы исследования', ResearchGroups=ResearchGroups, pagination=pagination)


# Ведение полномочий
@bp.route('/user_role_edit', methods = ['GET','POST'])
def user_role():
    UserForm = UserRoleForm()
    UserFilterForm = UserRoleFilterForm()
    page = request.args.get('page',1,type=int)

    user_filter_id = session.get('user_filter_id')
    role_filter_id = session.get('role_filter_id')
    user_list = UserRoles.query
    if user_filter_id is not None:
        user_list = user_list.filter(UserRoles.user==user_filter_id)
    if role_filter_id is not None:
        user_list = user_list.filter(UserRoles.role==role_filter_id)
    pagination =  user_list.paginate(page,5,error_out=False)
    userroles = pagination.items

    if UserForm.submit_ok.data and UserForm.validate_on_submit():
# Обработка удаления и добавления данных
        user = Users.query.get(UserForm.user.data)
        role = Roles.query.get(UserForm.role.data)
        user_role = UserRoles.query.filter_by(user=user.id, role=role.id).first()
        if user_role is not None and UserForm.action.data == 1:
            flash('Данному пользователю роль уже назначена', category='warning')
        elif user_role is None and UserForm.action.data == 1:
            user_role = UserRoles(user=user.id, role=role.id)
            db.session.add(user_role)
            db.session.commit()
            flash('Полномочия назначены', category='info')
        elif user_role is None and UserForm.action.data == 2:
            flash('Таких полномочий нет', category='warning')
        elif user_role is not None and UserForm.action.data == 2:
            db.session.delete(user_role)
            db.session.commit()
            flash('Полномочия удалены', category='warning')
        return redirect(url_for('.user_role'))
    if UserFilterForm.submit_filter.data and UserFilterForm.validate_on_submit():
# Фильтрация списка
        user_list = UserRoles.query
        if UserFilterForm.user_filter.data != 0:
# Выбрано значение ( не All)
            user_list = user_list.filter(UserRoles.user==UserFilterForm.user_filter.data)
            session['user_filter_id']= UserFilterForm.user_filter.data
        if UserFilterForm.role_filter.data != 0:
            user_list = user_list.filter(UserRoles.role==UserFilterForm.role_filter.data)
            session['role_filter_id']= UserFilterForm.role_filter.data
# Выбрано значение ALL - снять фильтр
        if UserFilterForm.user_filter.data == 0:
            session['user_filter_id'] = None
        if UserFilterForm.role_filter.data == 0:
            session['role_filter_id'] = None
        pagination =  user_list.paginate(page,5,error_out=False)
        userroles = pagination.items


    return render_template('admin/user_role.html', Panel='UserRoles', UserForm=UserForm, UserFilterForm=UserFilterForm, userroles=userroles,
                            title='Назначение полномочий', Users=Users, Roles=Roles,
                            pagination=pagination)
