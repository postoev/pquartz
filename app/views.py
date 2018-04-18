from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from . import application, db, bootstrap
from .forms import LoginForm, RegistrationForm
from .models import User


# Index page (session control)
@application.route('/')
@application.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')


# Login form
@application.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)


# Logout
@application.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# Registration form
@application.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, 
                    realname=form.realname.data, 
                    email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


# Example page
@application.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title="Dashboard")

