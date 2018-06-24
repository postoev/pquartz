# -*- coding: cp1251 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from . import db, lm


# Maximum string length for database model
MAX_LENGTH = 128
# Max type string length
MAX_TYPE_LENGTH = 32


# Friend relationship
in_friends = db.Table('in_friends',
    db.Column('friendship_id', db.Integer, db.ForeignKey('friendship.fr_id'), primary_key=True),
    db.Column('from_id', db.Integer, db.ForeignKey('user.id'))
)

out_friends = db.Table('out_friends',
    db.Column('friendship_id', db.Integer, db.ForeignKey('friendship.fr_id'), primary_key=True),
    db.Column('to_id', db.Integer, db.ForeignKey('user.id'))
)


# Chat relationship
chats = db.Table('chats',
    db.Column('chat_id', db.Integer, db.ForeignKey('chat.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


# Message relationship
in_messages = db.Table('in_messages',
    db.Column('message_id', db.Integer, db.ForeignKey('message.id'), primary_key=True),
    db.Column('receiver_id', db.Integer, db.ForeignKey('receiver.id'))
)

out_messages = db.Table('out_messages',
    db.Column('message_id', db.Integer, db.ForeignKey('message.id'), primary_key=True),
    db.Column('sender_id', db.Integer, db.ForeignKey('user.id'))
)



# Base model for all message receivers
class Receiver(db.Model):
    __tablename__ = 'receiver'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    type = db.Column(db.String(MAX_TYPE_LENGTH))
    
    __mapper_args__ = {
        'polymorphic_identity': 'receiver',
        'polymorphic_on': type
    }


class Friendship(db.Model):
    __tablename__ = 'friendship'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    # represent type of friendship update:
    # false - pending friendship request <from_id> to <to_id>
    # true - accepted friendship from <from_id> to <to_id>
    accepted = db.Column(db.Boolean, nullable=False)
    update = db.relationship('UpdFriend',
                              uselist=False,
                              backref='friendship')


# User model
class User(UserMixin, Receiver):
    __tablename__ = 'user'

    id = db.Column(db.Integer, db.ForeignKey('receiver.id'), primary_key=True)
    name = db.Column(db.String(MAX_LENGTH), unique=True, nullable=False)
    realname = db.Column(db.String(MAX_LENGTH), nullable=False)
    email = db.Column(db.String(MAX_LENGTH), unique=True, nullable=False)
    password_hash = db.Column(db.String(MAX_LENGTH), unique=False, nullable=False)
    # chats invited in
    chats = db.relationship('Chat', 
                            secondary=chats, 
                            lazy='subquery',
                            backref=db.backref('users', lazy=True))

    # incomming friendship requests
    in_friend_requests = db.relationship('Friendship',
                                         secondary=in_friends,
                                         lazy='dynamic',
                                         primaryjoin=(id == in_friends.c.from_id),
                                         backref=db.backref('request_to', lazy=True, uselist=False))

    # outcomming friendship requests
    out_friend_requests = db.relationship('Friendship',
                                          secondary=out_friends,
                                          lazy='dynamic',
                                          primaryjoin=(id == out_friends.c.to_id),
                                          backref=db.backref('request_from', lazy=True, uselist=False))

    # received messages
    in_messages = db.relationship('Message',
                                secondary=in_messages,
                                lazy='dynamic',
                                primaryjoin=(id == in_messages.c.receiver_id),
                                backref=db.backref('receiver', lazy=True, uselist=False))
    # posted messages
    out_messages = db.relationship('Message',
                                secondary=out_messages,
                                lazy='dynamic',
                                primaryjoin=(id == out_messages.c.sender_id),
                                backref=db.backref('sender', lazy=True, uselist=False))
    #updates
    updates = db.relationship('Update',
                              uselist=False,
                              backref='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User name=%r>' % (self.name,)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'inherit_condition': (id == Receiver.id)
    }


# Chat model
class Chat(Receiver):
    __tablename__ = 'chat'

    id = db.Column(db.Integer, db.ForeignKey('receiver.id'), primary_key=True)
    name = db.Column(db.String(MAX_LENGTH), unique=True, nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'chat',
        'inherit_condition': (id == Receiver.id)
    }


# Base model for messages
class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    type = db.Column(db.String(MAX_TYPE_LENGTH))
    created_time = db.Column(db.DateTime, nullable=False)
    update = db.relationship('UpdMessage',
                              uselist=False,
                              backref='message')

    __mapper_args__ = {
        'polymorphic_identity': 'message',
        'polymorphic_on': type
    }



# Simple text message model (Single Table inheritance)
class TextMessage(Message):
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<TextMessage created_time=%r, text=%r>' % (self.created_time, self.text,)

    __mapper_args__ = {
        'polymorphic_identity': 'textmessage'
    }

# File message
class FileMessage(Message):
    filename = db.Column(db.String(MAX_LENGTH))
    data = db.Column(db.LargeBinary)

    def __repr__(self):
        return '<FileMessage created_time=%r, filename=%r>' % (self.created_time, self.filename)

    __mapper_args__ = {
        'polymorphic_identity': 'filemessage'
    }


#Updates model
class Update(db.Model):
    __tablename__ = 'update'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(MAX_TYPE_LENGTH))
    # represents receiver of update
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    __mapper_args__ = {
        'polymorphic_identity': 'update',
        'polymorphic_on': type
    }


class UpdMessage(Update):
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))

    __mapper_args__ = {
        'polymorphic_identity': 'updmessage'
    }


class UpdFriend(Update):
    friendship_id = db.Column(db.Integer, db.ForeignKey('friendship.fr_id'))

    __mapper_args__ = {
        'polymorphic_identity': 'updfriend'
    }

    
# Helper for Flask-Login
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))



# Examples
# Create users
'''
user1 = User(realname='Ivan', name='ivan777', email='ivan@example.com',
             password_hash='daaad6e5604e8e17bd9f108d91e26afe6281dac8fda0091040a7a6d7bd9b43b5')
user2 = User(realname='Oleg', name='oleg_ivanov', email='oleg@gmail.com',
             password_hash='1e11ff7b5f872a5a0ee8a2a08d13ea97ff63dd71cd0c8b5c22819a7faeaa5fff')
user3 = User(realname='Max', name='MadMax', email='maximus@gmail.com',
            password_hash='246ebf1a41e451101415ac0de094d5ff850f69336f59b214d4a01c82cbeebf5b')


message1 = TextMessage(created_time=datetime.utcnow(), text='Hello!')
message2 = TextMessage(created_time=datetime.utcnow(), text='Goodbuy!')

user1.out_messages.append(message1)
user2.in_messages.append(message1)

db.session.add(user1)
db.session.add(user2)
db.session.add(user3)
db.session.add(message1)
db.session.commit()
'''


'''
# Accepted friendship request
friendship1 = Friendship(accepted=True)
user1 = User.query.get(1)
user2 = User.query.get(2)

user1.out_friend_requests.append(friendship1)
user2.in_friend_requests.append(friendship1)


db.session.add(user1)
db.session.add(user2)
db.session.add(friendship1)

print(user1.out_friend_requests[0].request_to)
print(user2.in_friend_requests[0].request_from)
db.session.commit()
'''

'''
# Send message updates
user2 = User.query.get(2)
message1 = Message.query.get(1)
upd1 = UpdMessage(user=user2, message=message1)
db.session.add(user2)
db.session.add(message1)
db.session.add(upd1)
db.session.commit()
'''

'''
# Send friendship updates
user1 = User.query.get(1)
user2 = User.query.get(2)

friendship1 = Friendship.query.get(1)

upd3 = UpdFriend(user=user2, friendship=friendship1)
db.session.add(user1)
db.session.add(user2)
db.session.add(upd3)
db.session.commit()
'''
