from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_bootstrap import Bootstrap

application = Flask(__name__, instance_relative_config=True)

# Load the default configuration
application.config.from_object('config')
# Load the configuration from the instance folder
application.config.from_pyfile('config.py', silent=True)

db = SQLAlchemy(application)
lm = LoginManager()
lm.init_app(application)
lm.login_view = 'login'
bootstrap = Bootstrap(application)

from . import views, models