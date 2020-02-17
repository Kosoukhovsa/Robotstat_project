from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import Users, Clinics
from datetime import datetime
from app.email import send_password_reset_email

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()


@bp.route('/register', methods = ['GET','POST'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(username=form.username.data.lower(),
                        email=form.email.data)
        user.set_password(form.password1.data)
        user.time_create = datetime.utcnow()
        user.clinic = Clinics.query.get(form.clinic.data).id
        db.session.add(user)
        db.session.commit()
        flash('You are registered!', category='info')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)


@bp.route('/login', methods = ['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data.lower()).first()
        print(user.check_password(form.password.data))
        if user is not None and user.check_password(form.password.data):
            print(user)
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
                #next = url_for('auth.welcome')
            return redirect(next)
        flash('Invalid username or password.', category='warning')
    return render_template('auth/login.html', form=form, title='Sign In')

@bp.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')

@bp.route('/logout')
def logout():
    logout_user()
    #flash('You are logged out!', category='info')
    return redirect(url_for('main.index'))

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user=Users.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', category='info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', form=form, title='Reset password')


@bp.route('/reset_password/<token>', methods=['GET','POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user=Users.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset!', category='info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_form.html', form=form, title='Reset password')
