 from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from . import application, db, bootstrap
from .forms import LoginForm, RegistrationForm
from .models import User
from flask import jsonify
from sqlalchemy import desc

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
@application.route('/friends', methods = ['GET'])
@login_required
def friends():
    users = User.query.get(current_user.id)
    acc_in = users.in_friend_request.query.filter_by(accepted = True)
    acc_out = users.out_friend_request.query.filter_by(accepted = True)
    result = []
    for f in acc_in:
        f_result = {}
        f_result['id'] = f.id
        f_result['name'] = f.name
        f_result['realname'] = f.realname
        f_result['email'] = f.email
        result.append(f_result)
    for f in acc_out:
        f_result = {}
        f_result['id'] = f.id
        f_result['name'] = f.name
        f_result['realname'] = f.realname
        f_result['email'] = f.email
        result.append(f_result)
    return render_template('friends.html', title = 'Friends', data = result)

# Find user
@application.route('/users', methods = ['GET'])
@login_required
def find_user():
    f_name = request.args.get('name')
    f_user = User.query.filter_by(name = f_name).first(10)
    result_list = []
    for f in f_user:
        result = {}
        result['id'] = f.id
        result['name'] = f.name
        result['realname'] = f.realname
        result['email'] = f.email
        result_list.append(result)
    return result_list

# Profile
@application.route('/profile/<id>', methods = ['GET'])
@login_required
def profile(id):
    f_user = User.query.get(id)
    result = {}
    result['id'] = f.id
    result['name'] = f_user.name
    result['realname'] = f_user.realname
    result['email'] = f_user.email
    return render_template('profile.html', title = 'Profile', data = jsonify(result))

# Send message
@application.route('/chats/<chat_id>', methods = ['POST'])
@login_required
def send_mess():
    sender_id = request.args.get('sender_id')
    message = {}
    created_time = request.args.get('created_time')
    message['created_time'] = created_time
    type_mess = request.args.get('type')
    message['type'] = type_mess
    if type_mess == "textmessage":
        text_mess = request.args.get('textmessage')
        message['textmessage'] = text_mess
    if type_mess == "filemessage":
        name_of_file = request.args.get('filename')
        message['filename'] = name_of_file
    user1 = User.query.get(sender_id)
    chat_id = request.args.get('chat_id')
    user1.out_messages.append(message)
    db.session.add(user1)
    us_chat = User.chats.query.filter_by(id == chat_id)
    for f in us_chat:
        if f.id != sender_id:
            f.in_message.append(message)
            upd = UpdMessage(user=f, message=message)
            db.session.add(upd)
            db.session.add(f)
    db.session.commit()

# Load chat messages
@application.route('/chats/<chat_id>', methods = ['GET'])
@login_required
def open_dia(chat_id):
    list_mess = []
    # TODO Load chat messages using current_user.id, inache mozhno
    # zagruzit' chat lubogo 4eloveka, a eto ne bezopasno
    messages = Chat.in_messages.query.filter_by(chat_id).order_by(desc(created_time))
    for mess in messages:
        f_mess = {}
        f_mess['time'] = mess.created_time
        if mess.type == 'textmessage':
            f_mess['text'] = mess.textmessage.text
            list_mess.append(f_mess)
        if mess.type == 'filemessage':
            f_mess['file_name'] = mess.filemessage.filename
            f_mess['data'] = mess.filemessage.data
            list_mess.append(f_mess)
    return jsonify({list_mess})


# Chats
@application.route('/chats', methods = ['GET'])
@login_required
def list_chats():

    result = ['user1', 'user2', 'user4']
    ### OSHIBKA NIZHE
    # chats = User.chats.query.get(current_user.id)
    ### OSHIBKA VISHE

    # result = []
    # for f in chats:
    #     f_chat = f.name
    #     result.append(f_chat)
    return render_template('chats.html', title = 'Chats', data = result)

# Delete message
@application.route('/chats/<id>', methods = ['GET', 'POST'])
@login_required
def del_message(user_id, chat_id, message_id):
    user_id = request.args.get('sender_id')
    chat_id = request.args.get('chat_id')
    message_id = request.args.get('message_id')
    chat1 = Chat.query.get(chat_id)
    user1 = User.query.get(user_id)
    mess = chat1.in_messages.query.get(message_id)
    mess.delete()
    mess1 = user1.out_messages.query.get(message_id)
    mess1.delete()
    db.session.commit()


# Loading Updates
@application.route('/upd/<id>', methods = ['GET', 'POST'])
@login_required
def load_upd():
    user_id = request.args.get('user_id')
    upd = db.session.updates.get(user.id == user_id)
    tmess_upd = []
    fmess_upd = []
    fr_upd = []
    for f in upd:
        f_res = {}
        f_res['id'] = f.id
        f_res['type'] = f.type
        if f.type == 'updmessage':
            mess = Message.query.get(f.message_id)
            f_res['created_time'] = mess.created_time
            if f.message.type == 'textmessage':
                f_res['text'] = mess.text
                tmess_upd.append(f_res)
            if f.message.type == 'filemessage':
                f_res['filename'] = mess.filename
                fmess_upd.append(f_res)
        if f.type == 'updfriend':
            frie = User.query.get(out_friend_request = f.friendship_id)
            f_res['id'] = frie.id
            f_res['name'] = frie.name
            f_res['realname'] = frie.realname
            f_res['email'] = frie.email
            fr_upd.append(f_res)
    return jsonify({tmess_upd, fmess_upd, fr_upd})


#Send request
@application.route('/friends', methods = ['GET', 'POST'])
@login_required
def send_req():
    sender_id = request.args.get('user_id')
    fr_id = request.args.get('user_id')
    user1 = User.query.get(sender_id)
    user2 = User.query.get(fr_id)
    relationship1 = Friendship(accepted = False)
    upd = UpdFriend(user = user2, friendship = relationship1)
    user1.out_friend_requests.append(relationship1)
    user2.in_friend_requests.append(relationship1)
    db.session.add(upd)
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()


# Accept request
@application.route('/friends', methods = ['GET', 'POST'])
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
@application.route('/friends', methods = ['GET', 'POST'])
@login_required
def del_fr():
    user_id = request.args.get('user_id')
    fr_id = request.args.get('fr_id')
    user1 = User.query.get(user_id)
    fr = user1.in_friend.query.get(fr_id)
    if fr:
        fr.accepted = False
    req = user1.out_friend_requests.query.get(fr_id)
    if req:
        req.delete()
    db.session.commit()

# Example page
@application.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():

    print(current_user.chats)
    chat_messages=[{"message": "asdasd"}]
    return render_template('dashboard.html', title="Dashboard", chat_messages=chat_messages)

# @application.route('/sobesedniks', methods=['POST'])
# @login_required
# def dashboard():
#     print(current_user.chats)
#     return render_template('dashboard.html', title="Dashboard")

    # User page
@application.route('/userpage')
@login_required
def userpage():
    return render_template('userpage.html', title="Userpage")

