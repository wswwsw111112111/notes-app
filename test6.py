from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory, \
    send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timezone, timedelta
from flask_wtf.csrf import CSRFProtect
import os
import base64
import hashlib
import zipfile
import shutil
import json
import glob  # 添加 glob 模块
from flask_migrate import Migrate
import magic
import logging
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Uploads')
app.config['TEMP_CHUNK_DIR'] = os.path.join(app.config['UPLOAD_FOLDER'], 'temp')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_CHUNK_DIR'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Template filter for JSON parsing
@app.template_filter('fromjson')
def fromjson_filter(data):
    return json.loads(data)


ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.txt', '.doc', '.docx', '.zip', '.mp4'}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    notes = db.relationship('Note', backref='user', lazy=True)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content_type = db.Column(db.String(20), nullable=False)
    content_data = db.Column(db.Text, nullable=False)
    raw_content = db.Column(db.Text)
    additional_text = db.Column(db.Text, nullable=True)  # 新增字段，用于存储附加文本
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    file_size = db.Column(db.Integer, nullable=True)
    md5 = db.Column(db.String(32), nullable=True)

    def __repr__(self):
        return f'<Note {self.id} {self.content_type}>'


def allowed_file(filename, file_content=None):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if not file_content:
        return False
    try:
        mime = magic.Magic(mime=True)
        file_mime = mime.from_buffer(file_content[:2048])
        allowed_mimes = {
            '.png': ['image/png'],
            '.jpg': ['image/jpeg'],
            '.jpeg': ['image/jpeg'],
            '.gif': ['image/gif'],
            '.pdf': ['application/pdf'],
            '.txt': ['text/plain'],
            '.doc': ['application/msword'],
            '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            '.zip': ['application/zip'],
            '.mp4': ['video/mp4']
        }
        return file_mime in allowed_mimes.get(ext, [])
    except Exception as e:
        logger.error(f"MIME check failed for {filename}: {str(e)}")
        return False


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            logger.error("Login failed: Missing username or password")
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            session['username'] = user.username
            logger.info(f"Login successful: user_id={user.id}, username={username}")
            return redirect(url_for('notes_page'))
        else:
            flash('用户名或密码错误', 'danger')
            logger.error(f"Login failed: Invalid username or password for {username}")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            logger.error("Registration failed: Missing username or password")
            return redirect(url_for('register'))
        if len(username) < 3:
            flash('用户名必须至少3个字符', 'danger')
            logger.error(f"Registration failed: Username '{username}' too short")
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('密码必须至少6个字符', 'danger')
            logger.error(f"Registration failed: Password too short for {username}")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            logger.error(f"Registration failed: Username '{username}' already exists")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            logger.info(f"Registration successful: Username '{username}' created")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请重试', 'danger')
            logger.error(f"Registration failed: Database error - {str(e)}")
            return redirect(url_for('register'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    logger.info("Logout successful: Session cleared")
    return redirect(url_for('login'))


@app.route('/notes', defaults={'page': 1})
@app.route('/notes/page/<int:page>')
@login_required
def notes_page(page):
    page = request.args.get('page', 1, type=int)
    per_page = 10
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.timestamp.desc()).paginate(page=page,
                                                                                                   per_page=per_page,
                                                                                                   error_out=False)
    logger.info(f"Notes page loaded: user_id={current_user.id}, page={page}, number of notes={notes.total}")
    return render_template('notes.html', notes=notes)


@app.route('/notes/gallery/<int:note_id>')
@login_required
def gallery_page(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        logger.error(f"Gallery access failed: User ID {current_user.id} has no permission for note ID {note_id}")
        flash('无权访问此画廊', 'danger')
        return redirect(url_for('notes_page'))
    if note.content_type != 'gallery':
        logger.error(f"Gallery access failed: Note ID {note_id} is not a gallery note")
        flash('无效的画廊笔记', 'danger')
        return redirect(url_for('notes_page'))
    try:
        image_paths = json.loads(note.content_data)
        raw_contents = json.loads(note.raw_content) if note.raw_content else [os.path.basename(path) for path in
                                                                              image_paths]
        logger.info(f"Gallery page loaded: Note ID={note_id}, Images={len(image_paths)}")
        return render_template('gallery.html', note=note, image_paths=image_paths, raw_contents=raw_contents)
    except Exception as e:
        logger.error(f"Gallery page failed: {str(e)}")
        flash('加载画廊失败', 'danger')
        return redirect(url_for('notes_page'))


@app.route('/notes/add', methods=['POST'])
@login_required
def add_note():
    user_id = current_user.id
    data = request.get_json()
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400

        file_content = file.read()
        file.seek(0)  # 重置文件指针

        if not allowed_file(file.filename, file_content):
            return jsonify({'success': False, 'error': '不允许的文件类型'}), 400

        md5_hash = hashlib.md5(file_content).hexdigest()
        existing_note = Note.query.filter_by(md5=md5_hash, user_id=current_user.id).first()

        if existing_note:
            return jsonify({'success': False, 'error': '文件已存在 (MD5 相同)'}), 409

        filename = secure_filename(f"{md5_hash}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(file_path)
        except Exception as e:
            return jsonify({'success': False, 'error': f'文件保存失败: {str(e)}'}), 500

        ext = os.path.splitext(filename)[1].lower()
        content_type = 'image' if ext in ['.png', '.jpg', '.jpeg', '.gif'] else 'file'

        new_note = Note(
            user_id=current_user.id,
            content_type=content_type,
            content_data=filename,
            raw_content=file.filename,  # 原始文件名，用于下载显示
            file_size=len(file_content),
            md5=md5_hash,
            additional_text=request.form.get('additional_text')
        )
        db.session.add(new_note)
        db.session.commit()

        return jsonify({
            'success': True,
            'note': {
                'id': new_note.id,
                'content_type': new_note.content_type,
                'content_data': new_note.content_data,
                'raw_content': new_note.raw_content,
                'timestamp': new_note.timestamp.isoformat(),
                'additional_text': new_note.additional_text,
                'md5': new_note.md5,
                'file_size': new_note.file_size
            }
        })
    if not data or 'type' not in data or 'content' not in data:
        logger.error("Add note failed: Invalid request data")
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    note_type = data['type']
    content = data['content']
    filename = data.get('filename')

    new_note = Note(user_id=user_id, content_type=note_type, timestamp=datetime.now(timezone.utc))

    if note_type == 'text':
        new_note.content_data = content
    elif note_type in ['image', 'file']:
        if not filename:
            logger.error("Add note failed: Filename missing for file/image upload")
            return jsonify({'success': False, 'error': '文件名缺失'}), 400
        try:
            if ',' not in content:
                logger.error("Add note failed: Invalid file data")
                return jsonify({'success': False, 'error': '无效的文件数据'}), 400
            file_data = base64.b64decode(content.split(',')[1])
            if len(file_data) > app.config['MAX_CONTENT_LENGTH']:
                logger.error(f"Add note failed: File {filename} exceeds 200MB limit")
                return jsonify({'success': False, 'error': '文件过大，最大200MB'}), 400
            if not allowed_file(filename, file_data):
                logger.error(f"Add note failed: Invalid file type for {filename}")
                return jsonify({'success': False, 'error': '不支持的文件类型'}), 400

            md5_hash = hashlib.md5(file_data).hexdigest()
            existing_note = Note.query.filter_by(user_id=user_id, md5=md5_hash).first()
            if existing_note:
                logger.error(f"Add note failed: File already exists (MD5: {md5_hash})")
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
            logger.error(f"Add note failed: File save error - {str(e)}")
            return jsonify({'success': False, 'error': f'文件保存失败: {str(e)}'}), 500

    try:
        db.session.add(new_note)
        db.session.commit()
        logger.info(f"Note added: ID={new_note.id}, Type={note_type}, User ID={user_id}")
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
        logger.error(f"Add note failed: Database error - {str(e)}")
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
    mode = request.form.get('mode', 'file')
    additional_text = request.form.get('additional_text', '')

    if mode not in ['file', 'gallery', 'zip']:
        logger.error(f"Invalid upload mode: {mode}")
        return jsonify({'success': False, 'error': '无效的上传模式'}), 400

    if not chunk or not filename or chunk_index < 0 or total_chunks < 0 or not chunk_id:
        logger.error("Missing or invalid chunk parameters")
        return jsonify({'success': False, 'error': '缺少必要参数或参数无效'}), 400

    chunk_dir = os.path.join(app.config['TEMP_CHUNK_DIR'], chunk_id)
    os.makedirs(chunk_dir, exist_ok=True)
    chunk_path = os.path.join(chunk_dir, f'chunk-{chunk_index}')
    try:
        chunk.save(chunk_path)
    except Exception as e:
        shutil.rmtree(chunk_dir, ignore_errors=True)
        logger.error(f"Save chunk failed: {str(e)}")
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
                try:
                    os.remove(final_path)
                except PermissionError:
                    logger.warning(f"Failed to remove {final_path} due to PermissionError")
            logger.error(f"Merge chunk failed: {str(e)}")
            return jsonify({'success': False, 'error': f'合并分片失败: {str(e)}'}), 500

        with open(final_path, 'rb') as f:
            file_data = f.read(2048)
            if not allowed_file(filename, file_data):
                try:
                    os.remove(final_path)
                except PermissionError:
                    logger.warning(f"Failed to remove {final_path} due to PermissionError")
                shutil.rmtree(chunk_dir)
                logger.error(f"Invalid file type: {filename}")
                return jsonify({'success': False, 'error': '不支持的文件类型'}), 400

        if file_size > app.config['MAX_CONTENT_LENGTH']:
            try:
                os.remove(final_path)
            except PermissionError:
                logger.warning(f"Failed to remove {final_path} due to PermissionError")
            shutil.rmtree(chunk_dir)
            logger.error(f"File too large: {filename}")
            return jsonify({'success': False, 'error': '文件过大，最大200MB'}), 400

        with open(final_path, 'rb') as f:
            file_data = f.read()
            md5_hash = hashlib.md5(file_data).hexdigest()

        existing_note = Note.query.filter_by(user_id=user_id, md5=md5_hash).first()
        if existing_note:
            shutil.rmtree(chunk_dir)
            logger.error(f"File already exists: MD5={md5_hash}")
            return jsonify({'success': False, 'error': '文件已存在，无需重复上传'}), 409

        if mode == 'zip':
            current_date = datetime.now(timezone.utc).strftime('%Y%m%d')
            zip_notes_count = Note.query.filter(
                Note.content_type == 'zip',
                Note.user_id == user_id,
                Note.timestamp >= datetime.strptime(current_date, '%Y%m%d'),
                Note.timestamp < (datetime.strptime(current_date, '%Y%m%d') + timedelta(days=1))
            ).count()
            zip_number = zip_notes_count + 1
            zip_filename = f"{current_date}-{zip_number}.zip"

            extract_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'extract-{chunk_id}')
            os.makedirs(extract_dir, exist_ok=True)
            try:
                with zipfile.ZipFile(final_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                file_paths = []
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        logger.debug(f"Processing file: {file_path}")
                        relative_path = os.path.relpath(file_path, extract_dir)
                        safe_file = secure_filename(relative_path)
                        base_name, ext = os.path.splitext(safe_file)
                        counter = 0
                        final_file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_file)
                        while os.path.exists(final_file_path):
                            counter += 1
                            safe_file = f"{base_name}_{counter}{ext}"
                            final_file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_file)
                        os.makedirs(os.path.dirname(final_file_path), exist_ok=True)
                        os.rename(file_path, final_file_path)
                        with open(final_file_path, 'rb') as f:
                            file_data = f.read()
                            md5_hash = hashlib.md5(file_data).hexdigest()
                        file_size = os.path.getsize(final_file_path)
                        file_paths.append(safe_file)
                if not file_paths:
                    shutil.rmtree(extract_dir)
                    try:
                        os.remove(final_path)
                    except PermissionError:
                        logger.warning(f"Failed to remove {final_path} due to PermissionError")
                    logger.error(f"Zip extract failed: No files found in {zip_filename}")
                    return jsonify({'success': False, 'error': '解压后无有效文件'}), 400
                new_note = Note(
                    user_id=user_id,
                    content_type='zip',
                    content_data=json.dumps(file_paths),
                    raw_content=zip_filename,
                    additional_text=additional_text,
                    file_size=sum(os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], f)) for f in file_paths),
                    md5=hashlib.md5(''.join(
                        hashlib.md5(open(os.path.join(app.config['UPLOAD_FOLDER'], f), 'rb').read()).hexdigest()
                        for f in file_paths
                    ).encode()).hexdigest(),
                    timestamp=datetime.now(timezone.utc)
                )
                db.session.add(new_note)
                db.session.commit()
                shutil.rmtree(extract_dir)
                try:
                    os.remove(final_path)
                except PermissionError:
                    logger.warning(f"Failed to remove {final_path} due to PermissionError")
                logger.info(f"Zip file processed: {zip_filename}, extracted {len(file_paths)} files")
                try:
                    shutil.rmtree(chunk_dir)
                    logger.info(f"Cleaned chunk directory after zip upload: {chunk_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean chunk directory {chunk_dir}: {str(e)}")
                return jsonify({
                    'success': True,
                    'note': {
                        'id': new_note.id,
                        'type': 'zip',
                        'content': [url_for('uploaded_file', filename=f) for f in file_paths],
                        'raw_content': zip_filename,
                        'additional_text': additional_text,
                        'timestamp': new_note.timestamp.isoformat(),
                        'file_size': new_note.file_size,
                        'md5': new_note.md5
                    }
                })
            except zipfile.BadZipFile as e:
                shutil.rmtree(extract_dir, ignore_errors=True)
                if os.path.exists(final_path):
                    try:
                        os.remove(final_path)
                    except PermissionError:
                        logger.warning(f"Failed to remove {final_path} due to PermissionError")
                logger.error(f"Zip extract failed: Invalid ZIP file - {str(e)}")
                return jsonify({'success': False, 'error': '无效的 ZIP 文件'}), 400
            except Exception as e:
                shutil.rmtree(extract_dir, ignore_errors=True)
                if os.path.exists(final_path):
                    try:
                        os.remove(final_path)
                    except PermissionError:
                        logger.warning(f"Failed to remove {final_path} due to PermissionError")
                logger.error(f"Zip extract failed: {str(e)}")
                return jsonify({'success': False, 'error': f'解压失败: {str(e)}'}), 500
            finally:
                try:
                    shutil.rmtree(chunk_dir)
                    logger.info(f"Cleaned chunk directory after zip processing: {chunk_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean chunk directory {chunk_dir}: {str(e)}")

        if mode == 'gallery':
            try:
                shutil.rmtree(chunk_dir)
                logger.info(f"Cleaned chunk directory after gallery upload: {chunk_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean chunk directory {chunk_dir}: {str(e)}")
            logger.info(f"Gallery file uploaded: {filename}, Path={safe_filename}")
            return jsonify({
                'success': True,
                'content': safe_filename,
                'file_size': file_size,
                'md5': md5_hash,
                'raw_content': filename
            })

        content_type = 'image' if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'file'
        new_note = Note(
            user_id=user_id,
            content_type=content_type,
            content_data=safe_filename,
            raw_content=filename,
            additional_text=additional_text,
            file_size=file_size,
            md5=md5_hash,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            db.session.add(new_note)
            db.session.commit()
            logger.info(f"Note added: ID={new_note.id}, Type={content_type}, User ID={user_id}")
            try:
                shutil.rmtree(chunk_dir)
                logger.info(f"Cleaned chunk directory after file upload: {chunk_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean chunk directory {chunk_dir}: {str(e)}")
            return jsonify({
                'success': True,
                'note': {
                    'id': new_note.id,
                    'type': new_note.content_type,
                    'content': url_for('uploaded_file', filename=new_note.content_data),
                    'raw_content': new_note.raw_content,
                    'additional_text': additional_text,
                    'timestamp': new_note.timestamp.isoformat(),
                    'file_size': new_note.file_size,
                    'md5': new_note.md5
                }
            })
        except Exception as e:
            db.session.rollback()
            if os.path.exists(final_path):
                try:
                    os.remove(final_path)
                except PermissionError:
                    logger.warning(f"Failed to remove {final_path} due to PermissionError")
            logger.error(f"Database save failed: {str(e)}")
            return jsonify({'success': False, 'error': f'数据库保存失败: {str(e)}'}), 500
        finally:
            try:
                shutil.rmtree(chunk_dir)
                logger.info(f"Cleaned chunk directory after file processing: {chunk_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean chunk directory {chunk_dir}: {str(e)}")

    logger.info(f"Chunk uploaded: {filename}, index={chunk_index}/{total_chunks}")
    return jsonify({'success': True, 'message': '分片上传成功'})


@app.route('/notes/add_multiple', methods=['POST'])
@login_required
def add_multiple():
    user_id = current_user.id
    data = request.get_json()
    if not data or 'mode' not in data or 'file_data' not in data:
        logger.error("Add multiple notes failed: Invalid request data")
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    mode = data['mode']
    file_data = data['file_data']  # List of {content, raw_content, file_size, md5}
    additional_text = data.get('additional_text', '')
    if mode != 'gallery':
        logger.error(f"Unsupported mode: {mode}")
        return jsonify({'success': False, 'error': '不支持的模式'}), 400

    file_paths = [item['content'] for item in file_data]
    try:
        new_note = Note(
            user_id=user_id,
            content_type='gallery',
            content_data=json.dumps(file_paths),
            raw_content=json.dumps([item['raw_content'] for item in file_data]),
            additional_text=additional_text,
            file_size=sum(item['file_size'] for item in file_data),
            md5=hashlib.md5(''.join(item['md5'] for item in file_data).encode()).hexdigest(),
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(new_note)
        db.session.commit()
        logger.info(f"Gallery note added: ID={new_note.id}, User ID={user_id}, Files={len(file_paths)}")
        return jsonify({
            'success': True,
            'note': {
                'id': new_note.id,
                'type': 'gallery',
                'content': file_paths,
                'additional_text': additional_text,
                'timestamp': new_note.timestamp.isoformat(),
                'file_size': new_note.file_size,
                'md5': new_note.md5
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Add multiple notes failed: Database error - {str(e)}")
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500


@app.route('/notes/edit/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    user_id = current_user.id
    note = Note.query.get_or_404(note_id)
    if note.user_id != user_id:
        logger.error(f"Edit note failed: User ID {user_id} has no permission to edit note ID {note_id}")
        return jsonify({'success': False, 'error': '无权编辑此笔记'}), 403
    data = request.get_json()
    new_text = data.get('content')
    if not new_text:
        logger.error(f"Edit note failed: Content is empty for note ID {note_id}")
        return jsonify({'success': False, 'error': '内容不能为空'}), 400
    if note.content_type == 'text':
        note.content_data = new_text
    else:  # zip or gallery
        note.additional_text = new_text
    note.timestamp = datetime.now(timezone.utc)
    try:
        db.session.commit()
        logger.info(f"Note edited: ID={note_id}, New Content={new_text}")
        return jsonify({
            'success': True,
            'new_content': note.content_data if note.content_type == 'text' else note.additional_text,
            'new_timestamp': note.timestamp.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Edit note failed: Database error - {str(e)}")
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500


@app.route('/notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    user_id = current_user.id
    note = Note.query.get_or_404(note_id)
    if note.user_id != user_id:
        logger.error(f"Delete note failed: User ID {user_id} has no permission to delete note ID {user_id}")
        return jsonify({'success': False, 'error': '无权删除此笔记'}), 403
    try:
        if note.content_type in ['image', 'file', 'zip']:
            if note.content_type == 'zip':
                for path in json.loads(note.content_data):
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"File deleted: {file_path}")
                        except PermissionError:
                            logger.warning(f"Failed to remove {file_path} due to PermissionError")
            else:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], note.content_data)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"File deleted: {file_path}")
                    except PermissionError:
                        logger.warning(f"Failed to remove {file_path} due to PermissionError")
        elif note.content_type == 'gallery':
            for path in json.loads(note.content_data):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Gallery file deleted: {file_path}")
                    except PermissionError:
                        logger.warning(f"Failed to remove {file_path} due to PermissionError")

        # 清理可能残留的分块文件
        chunk_dirs = glob.glob(os.path.join(app.config['TEMP_CHUNK_DIR'], f"chunk-*-{note.content_data}"))
        for chunk_dir in chunk_dirs:
            if os.path.exists(chunk_dir):
                try:
                    shutil.rmtree(chunk_dir)
                    logger.info(f"Cleaned chunk directory: {chunk_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean chunk directory {chunk_dir}: {str(e)}")

        db.session.delete(note)
        db.session.commit()
        logger.info(f"Note deleted: ID={note_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete note failed: Database error - {str(e)}")
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500


@app.route('/notes/download/<int:note_id>')
@login_required
def download_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'success': False, 'error': '无权下载'}), 403
    if note.content_type not in ['image', 'file', 'zip']:
        return jsonify({'success': False, 'error': '不支持下载'}), 400

    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], note.content_data)
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        # 强制下载，无论文件类型
        return send_file(file_path, as_attachment=True, download_name=note.raw_content or note.content_data)
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500


@app.route('/notes/download_gallery/<int:note_id>')
@login_required
def download_gallery(note_id):
    user_id = current_user.id
    note = Note.query.get_or_404(note_id)
    if note.user_id != user_id:
        logger.error(f"Download gallery failed: User ID {user_id} has no permission to download note ID {note_id}")
        return jsonify({'success': False, 'error': '无权下载此笔记'}), 403
    if note.content_type != 'gallery':
        logger.error(f"Download gallery failed: Note ID {note_id} is not a gallery note")
        return jsonify({'success': False, 'error': '仅画廊笔记支持一键下载'}), 400

    try:
        file_paths = json.loads(note.content_data)
        raw_contents = json.loads(note.raw_content) if note.raw_content else [os.path.basename(path) for path in
                                                                              file_paths]
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for path, original_name in zip(file_paths, raw_contents):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
                if os.path.exists(file_path):
                    zip_file.write(file_path, original_name)
                else:
                    logger.warning(f"File not found for download: {file_path}")
        zip_buffer.seek(0)
        logger.info(f"Gallery downloaded: Note ID={note_id}, Files={len(file_paths)}")
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'gallery_note_{note_id}.zip'
        )
    except Exception as e:
        logger.error(f"Download gallery failed: {str(e)}")
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500


@app.route('/notes/download_zip/<int:note_id>')
@login_required
def download_zip(note_id):
    user_id = current_user.id
    note = Note.query.get_or_404(note_id)
    if note.user_id != user_id:
        logger.error(f"Download zip failed: User ID {user_id} has no permission to download note ID {note_id}")
        return jsonify({'success': False, 'error': '无权下载此笔记'}), 403
    if note.content_type != 'zip':
        logger.error(f"Download zip failed: Note ID {note_id} is not a zip note")
        return jsonify({'success': False, 'error': '仅ZIP笔记支持一键下载'}), 400

    try:
        file_paths = json.loads(note.content_data)
        if not isinstance(file_paths, list):
            raise ValueError("Invalid content_data format")
        raw_contents = json.loads(note.raw_content) if note.raw_content and isinstance(note.raw_content, str) else [
            os.path.basename(path) for path in file_paths]
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for path, original_name in zip(file_paths, raw_contents):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
                if os.path.exists(file_path):
                    zip_file.write(file_path, original_name)
                else:
                    logger.warning(f"File not found for download: {file_path}")
        zip_buffer.seek(0)
        zip_filename = note.raw_content if note.raw_content else f"archive_{note_id}.zip"
        logger.info(f"Zip downloaded: Note ID={note_id}, Filename={zip_filename}, Files={len(file_paths)}")
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except json.JSONDecodeError as e:
        logger.error(f"Download zip failed: Invalid JSON data - {str(e)}")
        return jsonify({'success': False, 'error': '数据格式错误'}), 500
    except Exception as e:
        logger.error(f"Download zip failed: {str(e)}")
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return jsonify({'error': '文件不存在'}), 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database tables checked/created")

    port = int(os.environ.get('PORT', 5000))  # 优先从环境变量读取
    app.run(host='0.0.0.0', port=port, debug=False)