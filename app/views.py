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

# List of friends
@app.route('/friends/<user_id>', methods = ['GET'])
@login_required
def friends(user_id):
    friends = db.session.friends.get(user.id == user_id)
    result = []
    for f in friends:
        f_result = {}
        f_result['name'] = f.name
        f_result['realname'] = f.realname
        f_result['email'] = f.email
        result.append(f_result)

    return render_template('friends.html', title = 'Friends', data = result)

# Find user
@app.route('/friends', methods = ['GET'])
@login_required
def find_user():
    f_name = request.args.get('name')
    f_user = User.query.filter_by(name = f_name).first()
    result = {}
    result.['name'] = f_user.name
    result.['realname'] = f_user.realname
    result.['email'] = f_user.email
    return result

# Profile
@app.route('/profile/<id>', methods = ['GET'])
@login_required
def profile(id):
    f_user = User.query.filter_by(id = id).first()
    return render_template('profile.html', title = 'Profile', data = f_user)

# Send message
@app.route('/chats', methods = ['GET', 'POST'])
@login_required
def send_mess():
    sender_id = request.args.get('sender_id')
    message = request.args.get('message')
    chat_id = request.args.get('chat_id')
    user1 = User.query.filter_by(id = sender_id).first()
    chat1 = Chat.query.filter_by(id = chat_id).first()
    user1.out_messages.append(message)
    db.session.add(user1)
    us_chat = db.session.users.get(chat.id == chat_id)
    for f in us_chat:
        if f.id != sender_id:
            f.in_message.append(message)
            upd = UpdMesssage(user = f, message = message)
            db.session.add(f)
            db.session.add(upd)
    db.session.commit()

# Open dialog
@app.route('/chats', methods = ['GET'])
@login_required
def open_dia(user_id, chat_id):
    user_id = request.args.get('sender_id')
    chat_id = request.args.get('chat_id')
    list_mess = []
    messages = db.session.messages.get(chat.id == chat_id)
    for mess in messages:
        f_mess = {}
        f_mess['time'] = mess.created_time
        if mess.type == 'TextMessage':
            f_mess['text'] = mess.textmessage.text
        if mess.type = 'FileMessage':
            f_mess['file_name'] = mess.filemessage.filename
            f_mess['data'] = mess.filemessage.data
        list_mess.append(f_mess)
    return list_mess


# Chats
@app.route('/chats/<id>', methods = ['GET'])
@login_required
def list_chats(user_id):
    chats = db.session.chat.get(user.id == user_id)
    result = []
    for f in chats:
        f_chat = f.name
        result.append(f_chat)
    return render_template('chats.html', title = 'Chats', data = result)

# Delete message
@app.route('/chats/<id>', methods = ['GET', 'POST'])
@login_required
def del_message(user_id, chat_id, message_id):
    user_id = request.args.get('sender_id')
    chat_id = request.args.get('chat_id')
    message_id = request.args.get('message_id')


# Loading Updates
@login_required
def load_upd():
    user_id = request.args.get('user_id')
    upd = db.session.updates.get(user.id == user_id)
    result = []
    for f in upd:
        f_res = {}
        f_res['id'] = f.id
        f_res['type'] = f.type
        if f.type == 'updmessage':
            f_res['created_time'] = f.message.createdtime
            if f.message.type == 'textmessage':
                f_res['text'] = f.message.textmessage.text
            if f.message.type == 'filemessage':
                f_res['filename'] = f.message.filemessage.filename
                f_res['data'] = f.message.filemessage.data
        if f.type == 'updfriend':
            f_res['']


#Send request
@app.route('/friends', methods = ['GET', 'POST'])
@login_required
def send_req():
    sender_id = request.args.get('user_id')
    fr_id = request.args.get('user_id')
    user1 = User.query.get(sender_id)
    user2 = User.query.get(fr_id)
    relationship1 = Friendship(accepted = False)
    user1.out_friend_requests.append(relationship1)
    user2.in_friend_requests.append(relationship1)
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()


# Accept request
@app.route('/friends', methods = ['GET', 'POST'])
@login_required
def acc_req():
    sender_id = request.args.get('user_id')
    fr_id = request.args.get('user_id')
    user1 = User.query.get(sender_id)
    user2 = User.query.get(fr_id)
    relationship1 = Friendship(accepted=True)
    user1.out_friend_requests.append(relationship1)
    user2.in_friend_requests.append(relationship1)
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()

# Delete friend
@app.route('/friends/<id>', methods = ['GET', 'POST'])
@login_required
def del_fr(user_id, fr_id):


# Example page
@application.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title="Dashboard")
