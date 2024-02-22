from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate , MigrateCommand
from flask_script import Manager
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_session import Session
from flask_mail import Mail
from flask_mobility import Mobility



app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SESSION_TYPE'] = 'filesystem'
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
loginManager = LoginManager(app)
loginManager.login_view = 'login'
loginManager.login_message_category = 'info'
Session(app)
socketio = SocketIO(app , manage_session=False)
app.config['MAIL_SERVER'] = ''
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
mail = Mail(app)
mobility = Mobility(app)
migrate = Migrate(app , db)
manager = Manager(app)
manager.add_command('db' , MigrateCommand )


from mes import routes



       