from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask_wtf.csrf import CSRFProtect
import os
import base64
import hashlib
import zipfile
import shutil
import json
from flask_migrate import Migrate
import magic

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Uploads')
app.config['TEMP_CHUNK_DIR'] = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_chunks')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=0.2)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_CHUNK_DIR'], exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# 初始化 login_manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 添加 fromjson 滤镜（给 notes.html 用）
@app.template_filter('fromjson')
def fromjson_filter(data):
    return json.loads(data)

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.txt', '.doc', '.docx', '.zip', '.mp4'}

class User(UserMixin, db.Model):
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

def allowed_file(filename, file_content=None):
    # 规范化扩展名，始终转换为小写
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    # 如果未提供文件内容，允许通过（依赖扩展名）
    if not file_content:
        return True

    # MIME 类型验证
    try:
        mime = magic.Magic(mime=True)
        file_mime = mime.from_buffer(file_content[:2048])  # 检查前 2KB
        allowed_mimes = {
            '.png': ['image/png', 'image/x-png', 'application/octet-stream', 'image/vnd.microsoft.icon'],
            '.jpg': ['image/jpeg', 'image/x-jpeg', 'application/octet-stream'],
            '.jpeg': ['image/jpeg', 'image/x-jpeg', 'application/octet-stream'],
            '.gif': ['image/gif'],
            '.pdf': ['application/pdf'],
            '.txt': ['text/plain'],
            '.doc': ['application/msword'],
            '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            '.zip': ['application/zip'],
            '.mp4': ['video/mp4']
        }
        # 如果 MIME 类型不在列表中，但扩展名正确，允许通过
        return file_mime in allowed_mimes.get(ext, []) or ext in ALLOWED_EXTENSIONS
    except Exception as e:
        # 捕获 python-magic 异常，依赖扩展名
        print(f"MIME check failed for {filename}: {str(e)}")
        return ext in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            print("Session lost: User not authenticated. Redirecting to login.")
            return redirect(url_for('login'))
        print(f"Session active: user_id={current_user.id}, username={current_user.username}")
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
            login_user(user, remember=True)  # 使用 flask_login 登录用户
            session['username'] = user.username  # 仅用于模板显示
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
    logout_user()  # 使用 flask_login 登出用户
    session.clear()
    print("Logout successful: Session cleared.")
    return redirect(url_for('login'))

@app.route('/notes', defaults={'page': 1})
@app.route('/notes/page/<int:page>')
@login_required
def notes_page(page):
    print(f"Session active: user_id={current_user.id}, username={current_user.username}")
    per_page = 10
    pagination = Note.query.filter_by(user_id=current_user.id).order_by(Note.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    notes = pagination.items

    print(f"Notes page loaded: user_id={current_user.id}, page={page}, number of notes={len(notes)}")
    for note in notes:
        print(f"Note ID: {note.id}, Type: {note.content_type}, Content: {note.content_data}, Timestamp: {note.timestamp}")

    return render_template('notes.html', notes=notes, pagination=pagination)

@app.route('/notes/add', methods=['POST'])
@login_required
def add_note():
    user_id = current_user.id
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

            # 强化验证
            if len(file_data) > app.config['MAX_CONTENT_LENGTH']:
                print("Add note failed: File too large.")
                return jsonify({'success': False, 'error': '文件过大，最大200MB'}), 400
            if not allowed_file(filename, file_data):
                print("Add note failed: Invalid file type.")
                return jsonify({'success': False, 'error': '不支持的文件类型'}), 400

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
                'content': new_note.content_data if note_type == 'text' else url_for('uploaded_file', filename=new_note.content_data),
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

@app.route('/notes/upload_chunk', methods=['POST'])
@login_required
def upload_chunk():
    user_id = current_user.id
    chunk = request.files.get('chunk')
    filename = request.form.get('filename')
    chunk_index = int(request.form.get('chunkIndex', -1))
    total_chunks = int(request.form.get('totalChunks', -1))
    chunk_id = request.form.get('chunkId')

    if not chunk or not filename or chunk_index < 0 or total_chunks < 0 or not chunk_id:
        return jsonify({'success': False, 'error': '缺少必要参数或参数无效'}), 400

    # 保存分片
    chunk_dir = os.path.join(app.config['TEMP_CHUNK_DIR'], chunk_id)
    os.makedirs(chunk_dir, exist_ok=True)
    chunk_path = os.path.join(chunk_dir, f'chunk-{chunk_index}')
    try:
        chunk.save(chunk_path)
    except Exception as e:
        shutil.rmtree(chunk_dir, ignore_errors=True)
        return jsonify({'success': False, 'error': f'保存分片失败: {str(e)}'}), 500

    if chunk_index == total_chunks - 1:
        safe_filename = secure_filename(filename)
        final_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file_size = 0
        try:
            with open(final_path, 'wb') as f:
                for i in range(total_chunks):
                    chunk_file = os.path.join(chunk_dir, f'chunk-{i}')
                    with open(chunk_file, 'rb') as cf:
                        chunk_data = cf.read()
                        f.write(chunk_data)
                        file_size += len(chunk_data)
        except Exception as e:
            shutil.rmtree(chunk_dir, ignore_errors=True)
            if os.path.exists(final_path):
                os.remove(final_path)
            return jsonify({'success': False, 'error': f'合并分片失败: {str(e)}'}), 500

        # 验证完整文件的 MIME 类型
        try:
            with open(final_path, 'rb') as f:
                file_data = f.read(2048)
                if not allowed_file(filename, file_data):
                    os.remove(final_path)
                    shutil.rmtree(chunk_dir)
                    return jsonify({'success': False, 'error': '不支持的文件类型'}), 400
        except Exception as e:
            shutil.rmtree(chunk_dir, ignore_errors=True)
            if os.path.exists(final_path):
                os.remove(final_path)
            return jsonify({'success': False, 'error': f'文件验证失败: {str(e)}'}), 500

        if file_size > app.config['MAX_CONTENT_LENGTH']:
            os.remove(final_path)
            shutil.rmtree(chunk_dir)
            return jsonify({'success': False, 'error': '文件过大，最大200MB'}), 400

        try:
            with open(final_path, 'rb') as f:
                file_data = f.read()
                md5_hash = hashlib.md5(file_data).hexdigest()
        except Exception as e:
            shutil.rmtree(chunk_dir, ignore_errors=True)
            if os.path.exists(final_path):
                os.remove(final_path)
            return jsonify({'success': False, 'error': f'计算 MD5 失败: {str(e)}'}), 500

        existing_note = Note.query.filter_by(user_id=user_id, md5=md5_hash).first()
        if existing_note:
            shutil.rmtree(chunk_dir)
            return jsonify({'success': False, 'error': '文件已存在，无需重复上传'}), 409

        content_type = 'image' if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'file'
        new_note = Note(
            user_id=user_id,
            content_type=content_type,
            content_data=safe_filename,
            raw_content=filename,
            file_size=file_size,
            md5=md5_hash,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            db.session.add(new_note)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            shutil.rmtree(chunk_dir, ignore_errors=True)
            if os.path.exists(final_path):
                os.remove(final_path)
            return jsonify({'success': False, 'error': f'数据库保存失败: {str(e)}'}), 500

        shutil.rmtree(chunk_dir)

        return jsonify({
            'success': True,
            'note': {
                'id': new_note.id,
                'type': new_note.content_type,
                'content': url_for('uploaded_file', filename=new_note.content_data),
                'raw_content': new_note.raw_content,
                'timestamp': new_note.timestamp.isoformat(),
                'file_size': new_note.file_size,
                'md5': new_note.md5
            }
        })

    return jsonify({'success': True, 'message': '分片上传成功'})

@app.route('/notes/add_multiple', methods=['POST'])
@login_required
def add_multiple():
    user_id = current_user.id
    data = request.get_json()
    if not data or 'mode' not in data or 'file_paths' not in data:
        print("Add multiple notes failed: Invalid request data.")
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    mode = data['mode']
    file_paths = data['file_paths']
    if mode != 'gallery':  # 仅支持 gallery 模式，后续改为逐个添加
        return jsonify({'success': False, 'error': '不支持的模式'}), 400

    try:
        for file_path in file_paths:
            safe_filename = os.path.basename(file_path)
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            if not os.path.exists(full_path):
                continue
            file_size = os.path.getsize(full_path)
            with open(full_path, 'rb') as f:
                file_data = f.read()
                md5_hash = hashlib.md5(file_data).hexdigest()

            existing_note = Note.query.filter_by(user_id=user_id, md5=md5_hash).first()
            if not existing_note:
                new_note = Note(
                    user_id=user_id,
                    content_type='image',
                    content_data=safe_filename,
                    raw_content=safe_filename,
                    file_size=file_size,
                    md5=md5_hash,
                    timestamp=datetime.now(timezone.utc)
                )
                db.session.add(new_note)

        db.session.commit()
        print(f"Multiple notes added successfully: User ID={user_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Add multiple notes failed: Database error - {str(e)}")
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500

@app.route('/notes/edit/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    user_id = current_user.id
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
    user_id = current_user.id
    note = Note.query.get_or_404(note_id)
    if note.user_id != user_id:
        print(f"Delete note failed: User ID {user_id} has no permission to delete note ID {note_id}.")
        return jsonify({'success': False, 'error': '无权删除此笔记'}), 403
    try:
        if note.content_type in ['image', 'file', 'zip']:
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
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return jsonify({'error': '文件不存在'}), 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables checked/created.")
    app.run(debug=True, host='0.0.0.0', port=5000)
