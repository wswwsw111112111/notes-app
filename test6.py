from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask_wtf.csrf import CSRFProtect
import os
import base64
import hashlib
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # 确保 SECRET_KEY 是唯一的
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Uploads')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_PERMANENT'] = True  # 确保会话是永久的
app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系统存储会话
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# 添加最大上传限制
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
#313232
#备注12355456
#备注21:14
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    notes = db.relationship('Note', backref='user', lazy=True)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)
    content_data = db.Column(db.Text, nullable=False)
    raw_content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    file_size = db.Column(db.Integer, nullable=True)
    md5 = db.Column(db.String(32), nullable=True)

    def __repr__(self):
        return f'<Note {self.id} {self.content_type}>'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            print("Session lost: 'user_id' not found. Redirecting to login.")
            return redirect(url_for('login'))
        print(f"Session active: user_id={session['user_id']}, username={session.get('username')}")
        session.modified = True
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session.modified = True
            print(f"Login successful: user_id={user.id}, username={username}")
            return redirect(url_for('notes_page'))
        else:
            flash('用户名或密码错误')
            print("Login failed: Invalid username or password.")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            print(f"Registration failed: Username '{username}' already exists.")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功，请登录')
        print(f"Registration successful: Username '{username}' created.")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    print("Logout successful: Session cleared.")
    return redirect(url_for('login'))


@app.route('/notes')
@login_required
def notes_page():
    user_id = session['user_id']
    user_notes = Note.query.filter_by(user_id=user_id).order_by(Note.timestamp.asc()).all()
    print(f"Notes page loaded: user_id={user_id}, number of notes={len(user_notes)}")
    for note in user_notes:
        print(
            f"Note ID: {note.id}, Type: {note.content_type}, Content: {note.content_data}, Timestamp: {note.timestamp}")
    return render_template('notes.html', notes=user_notes, username=session.get('username'))


@app.route('/notes/add', methods=['POST'])
@login_required
def add_note():
    user_id = session['user_id']
    data = request.get_json()
    if not data or 'type' not in data or 'content' not in data:
        print("Add note failed: Invalid request data.")
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    note_type = data['type']
    content = data['content']
    filename = data.get('filename')

    new_note = Note(user_id=user_id, content_type=note_type, timestamp=datetime.now(timezone.utc))

    if note_type == 'text':
        new_note.content_data = content
    elif note_type in ['image', 'file']:
        if not filename:
            print("Add note failed: Filename missing for file/image upload.")
            return jsonify({'success': False, 'error': '文件名缺失'}), 400
        try:
            if ',' not in content:
                print("Add note failed: Invalid file data.")
                return jsonify({'success': False, 'error': '无效的文件数据'}), 400
            file_data = base64.b64decode(content.split(',')[1])

            md5_hash = hashlib.md5(file_data).hexdigest()

            existing_note = Note.query.filter_by(user_id=user_id, md5=md5_hash).first()
            if existing_note:
                print(f"Add note failed: File already exists (MD5: {md5_hash}).")
                return jsonify({'success': False, 'error': '文件已存在，无需重复上传'}), 409

            safe_filename = secure_filename(filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            new_note.content_data = safe_filename
            new_note.raw_content = filename
            new_note.file_size = len(file_data)
            new_note.md5 = md5_hash
        except Exception as e:
            print(f"Add note failed: File save error - {str(e)}")
            return jsonify({'success': False, 'error': f'文件保存失败: {str(e)}'}), 500

    try:
        db.session.add(new_note)
        db.session.commit()
        print(f"Note added successfully: ID={new_note.id}, Type={note_type}, User ID={user_id}")
        return jsonify({
            'success': True,
            'note': {
                'id': new_note.id,
                'type': new_note.content_type,
                'content': new_note.content_data if note_type == 'text' else url_for('uploaded_file',
                                                                                     filename=new_note.content_data),
                'raw_content': new_note.raw_content,
                'timestamp': new_note.timestamp.isoformat(),
                'file_size': new_note.file_size,
                'md5': new_note.md5
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Add note failed: Database error - {str(e)}")
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500


@app.route('/notes/edit/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    user_id = session['user_id']
    note = Note.query.get_or_404(note_id)
    if note.user_id != user_id:
        print(f"Edit note failed: User ID {user_id} has no permission to edit note ID {note_id}.")
        return jsonify({'success': False, 'error': '无权编辑此笔记'}), 403
    if note.content_type != 'text':
        print(f"Edit note failed: Note ID {note_id} is not a text note.")
        return jsonify({'success': False, 'error': '只能编辑文本笔记'}), 400
    data = request.get_json()
    new_content = data.get('content')
    if not new_content:
        print(f"Edit note failed: Content is empty for note ID {note_id}.")
        return jsonify({'success': False, 'error': '内容不能为空'}), 400
    note.content_data = new_content
    note.timestamp = datetime.now(timezone.utc)
    try:
        db.session.commit()
        print(f"Note edited successfully: ID={note_id}, New Content={new_content}")
        return jsonify({
            'success': True,
            'new_content': note.content_data,
            'new_timestamp': note.timestamp.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        print(f"Edit note failed: Database error - {str(e)}")
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500


@app.route('/notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    user_id = session['user_id']
    note = Note.query.get_or_404(note_id)
    if note.user_id != user_id:
        print(f"Delete note failed: User ID {user_id} has no permission to delete note ID {note_id}.")
        return jsonify({'success': False, 'error': '无权删除此笔记'}), 403
    try:
        if note.content_type in ['image', 'file']:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], note.content_data)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File deleted: {file_path}")
        db.session.delete(note)
        db.session.commit()
        print(f"Note deleted successfully: ID={note_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Delete note failed: Database error - {str(e)}")
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables checked/created.")

