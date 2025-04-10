import bcrypt
from peewee import (
    CharField,
    ForeignKeyField,
    Model,
    SqliteDatabase,
    AutoField,
)

from flask_login import UserMixin, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from utils import search_file, search_files
bcrypt = Bcrypt()
db = SqliteDatabase("tbx-users-db.sqlite3")

class BaseModel(Model): 
    class Meta:
        database = db

class User(BaseModel, UserMixin):
    id = AutoField()
    username = CharField(unique=True)
    password = CharField()

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
    
    def get_id(self):
        return str(self.id)
    
class File(BaseModel):
    file_name = CharField(max_length=256, unique=True)
    user = ForeignKeyField(User, backref='files')


def create_tables():
    with db:
        db.create_tables([User, File,], safe=True)

from flask_login import LoginManager
login_manager = LoginManager()

login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get(User.id == user_id)
    except User.DoesNotExist:
        return None
    

from flask import Flask, request, send_file

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

login_manager.init_app(app)
bcrypt.init_app(app)

create_tables()

@app.before_request
def before_request():
    db.connect()

@app.after_request
def after_request(response):
    db.close()
    return response

@app.route('/register', methods=['POST'])
def register():
    print('form',request.form)
    username = request.form['username']
    password = request.form['password']

    if User.select().where(User.username == username).exists():
        return 'Username already exists', 400

    user = User(username=username,)
    user.set_password(password)
    user.save()

    return 'User registered successfully', 201

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.select().where(User.username == username).first()

    if user and user.check_password(password):
        login_user(user)
        return 'Logged in successfully', 200
    else:
        return 'Invalid credentials', 401
@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return 'Logged out successfully', 200

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    return f'Hello, {current_user.username}!', 200

@app.route('/search_file', methods=['GET'])
@login_required
def search():
    folder = request.args.get('folder')
    prefix = request.args.get('prefix')

    if not folder or not prefix:
        return 'Folder and prefix are required', 400

    files_found = search_files(folder, prefix)
    submitted_files = File.select().where(File.file_name.startswith(prefix),File.user==current_user.username)
    submitted_files = [file.file_name for file in submitted_files]

    file_path = None
    for file in files_found:
        if file not in submitted_files:
            file_path = file
            break

    if file_path:
        return file_path, 200
    else:
        return 'File not found', 404
    

@app.route('/download',methods=['GET'])
def download():
    file_name = request.args.get('file')
    if not file_name:
        return 'file name required', 400
    
    user = User.get(User.username==current_user.username)
    if File.select().where(File.file_name==file_name,File.user==user.id).exists():
        return 'file already downloaded', 404
    new_file = File(file_name=file_name, user=user.id)
    new_file.save()
    return send_file('screenshots/'+file_name)
