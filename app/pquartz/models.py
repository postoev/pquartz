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
friends = db.Table('friends',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'))
)


# Chat relationship
chats = db.Table('chats',
    db.Column('chat_id', db.Integer, db.ForeignKey('chat.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


# Message relationship
messages = db.Table('messages',
    db.Column('message_id', db.Integer, db.ForeignKey('message.id'), primary_key=True),
    db.Column('sender_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('receiver_id', db.Integer, db.ForeignKey('receiver.id'))
)


# Base model for all message receivers
class Receiver(db.Model):
    __tablename__ = 'receiver'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    type = db.Column(db.String(MAX_TYPE_LENGTH))
    updates = db.relationship('Updates',
                              uselist = False,
                              backref = 'receiver')
    __mapper_args__ = {
        'polymorphic_identity': 'receiver',
        'polymorphic_on': type
    }


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
    # relationships (requests of friendship)
    friends = db.relationship('User', 
                            secondary=friends, 
                            backref='requested_by',
                            primaryjoin=(id == friends.c.user_id), 
                            secondaryjoin=(id == friends.c.friend_id))
    # received messages
    in_messages = db.relationship('Message',
                                secondary=messages, 
                                lazy='dynamic',
                                primaryjoin=(id == messages.c.receiver_id), 
                                backref=db.backref('receiver', lazy=True))
    # posted messages
    out_messages = db.relationship('Message',
                                secondary=messages, 
                                lazy='dynamic',
                                primaryjoin=(id == messages.c.sender_id), 
                                backref=db.backref('sender', lazy=True))
    #updates
    updates = db.relationship('Update',
                              backref = 'user',
                              lazy = True)
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
        'polymorphic_identity': 'text_message'
    }

# File message
class FileMessage(Message):
    name_file = db.Column(db.NameFile, nullable=False)
    data = db.Column(db.Data)

    def __repr__(self):
        return '<FileMessage created_time=%r, name_file=%r>' % (self.created_time, self.name_file)

    __mapper_args__ = {
        'polymorphic_identity': 'filemessage'
    }
    


#Updates model
class Update(db.Model):
    __tablename__ = 'update'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(MAX_TYPE_LENGTH))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    __mapper_args__ = {
        'polymorphic_identity': 'update',
        'polymorphic_on': type
    }


class UpdMessage(Update):
    sender_id = db.Column(db.Integer, db.ForeignKey('receiver.id'))
    type = db.Column(db.String(MAX_TYPE_LENGTH), db.ForeignKey('reciver.id'))


class UpdFriend(Update):
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    type_fr = db.Column(db.Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'updfriend'
    }

    
# Helper for Flask-Login
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


# Examples
'''
# Create users
user1 = User(name='Ivan', nickname='ivan777', email='ivan@example.com', 
            password='daaad6e5604e8e17bd9f108d91e26afe6281dac8fda0091040a7a6d7bd9b43b5')
user2 = User(name='Oleg', nickname='oleg_ivanov', email='oleg@gmail.com', 
            password='1e11ff7b5f872a5a0ee8a2a08d13ea97ff63dd71cd0c8b5c22819a7faeaa5fff')
user3 = User(name='Max', nickname='MadMax', email='maximus@gmail.com', 
            password='246ebf1a41e451101415ac0de094d5ff850f69336f59b214d4a01c82cbeebf5b')

# Accepted friendship request
user1.friends.append(user2)
user2.friends.append(user1)

# Create text message
message1 = TextMessage(created_time=datetime.utcnow(), text='Hello!')
message2 = TextMessage(created_time=datetime.utcnow(), text='Goodbuy!')
# Send msg1 from user1 -> user2
user1.out_messages.append(message1)
user2.in_messages.append(message1)
# Send msg2 from user1 -> user3
user1.out_messages.append(message2)
user3.in_messages.append(message2)
# Init database session
db.session.add(user1)
db.session.add(user2)
db.session.add(user3)
db.session.add(message1)

print (user1)
print (user1.out_messages.filter(receiver == user2))

#print(user2)
#print (user2.in_messages)

#db.session.commit()
'''

