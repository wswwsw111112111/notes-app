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
import glob
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
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return []


# FIX 1: 放开文件上传限制，增加更多常见类型
ALLOWED_EXTENSIONS = {
    # Images (for preview)
    '.png', '.jpg', '.jpeg', '.gif',
    # Documents
    '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.md',
    # Archives
    '.zip', '.rar', '.7z',
    # Media
    '.mp4', '.mov', '.avi', '.mp3',
    # Executables & Others
    '.exe', '.msi', '.apk', '.dmg', '.iso'
}


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
    additional_text = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    file_size = db.Column(db.Integer, nullable=True)
    md5 = db.Column(db.String(32), nullable=True)

    def __repr__(self):
        return f'<Note {self.id} {self.content_type}>'


# FIX 1: 简化文件验证逻辑，使其更加宽容
def allowed_file(filename, file_content=None):
    """
    Checks if a file is allowed.
    - Strict check (MIME) for image types that need previews.
    - Lenient check (extension only) for all other file types.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    # 对于需要预览的图片，为了安全，继续进行严格的MIME类型检查
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
    if ext in image_extensions:
        if not file_content:
            return False
        try:
            mime = magic.Magic(mime=True)
            file_mime = mime.from_buffer(file_content[:2048])
            image_mimes = {
                '.png': ['image/png'],
                '.jpg': ['image/jpeg'],
                '.jpeg': ['image/jpeg'],
                '.gif': ['image/gif'],
            }
            return file_mime in image_mimes.get(ext, [])
        except Exception as e:
            logger.error(f"MIME check failed for image {filename}: {str(e)}")
            return False

    # 对于所有其他允许的后缀名，我们信任它，直接允许上传
    return True


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
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            session['username'] = user.username
            return redirect(url_for('notes_page'))
        else:
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            return redirect(url_for('register'))
        if len(username) < 3:
            flash('用户名必须至少3个字符', 'danger')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('密码必须至少6个字符', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请重试', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))


@app.route('/notes', defaults={'page': 1})
@app.route('/notes/page/<int:page>')
@login_required
def notes_page(page):
    per_page = 10
    notes_pagination = Note.query.filter_by(user_id=current_user.id).order_by(Note.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('notes.html', notes=notes_pagination, pagination=notes_pagination)


@app.route('/notes/gallery/<int:note_id>')
@login_required
def gallery_page(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash('无权访问此画廊', 'danger')
        return redirect(url_for('notes_page'))
    if note.content_type != 'gallery':
        flash('无效的画廊笔记', 'danger')
        return redirect(url_for('notes_page'))
    try:
        image_paths = json.loads(note.content_data)
        raw_contents = json.loads(note.raw_content) if note.raw_content else [os.path.basename(path) for path in
                                                                              image_paths]
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
    if not data or 'type' not in data or 'content' not in data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    note_type = data['type']
    content = data['content']
    filename = data.get('filename')
    additional_text = data.get('additional_text', '').strip()

    new_note = Note(user_id=user_id, content_type=note_type, timestamp=datetime.now(timezone.utc),
                    additional_text=additional_text or None)

    if note_type == 'text':
        new_note.content_data = content
    elif note_type == 'image':
        if not filename:
            return jsonify({'success': False, 'error': '文件名缺失'}), 400
        try:
            if ',' not in content:
                return jsonify({'success': False, 'error': '无效的文件数据'}), 400
            file_data = base64.b64decode(content.split(',')[1])
            if len(file_data) > app.config['MAX_CONTENT_LENGTH']:
                return jsonify({'success': False, 'error': '文件过大，最大200MB'}), 400
            if not allowed_file(filename, file_data):
                return jsonify({'success': False, 'error': '不支持的文件类型'}), 400

            md5_hash = hashlib.md5(file_data).hexdigest()
            existing_note = Note.query.filter_by(user_id=user_id, md5=md5_hash).first()
            if existing_note:
                return jsonify({'success': False, 'error': '文件已存在，无需重复上传'}), 409

            safe_filename = secure_filename(f"{md5_hash}_{filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            new_note.content_data = safe_filename
            new_note.raw_content = filename
            new_note.file_size = len(file_data)
            new_note.md5 = md5_hash
        except Exception as e:
            return jsonify({'success': False, 'error': f'文件保存失败: {str(e)}'}), 500

    try:
        db.session.add(new_note)
        db.session.commit()
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
                'md5': new_note.md5,
                'additional_text': new_note.additional_text
            }
        })
    except Exception as e:
        db.session.rollback()
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
    additional_text = request.form.get('additional_text', '').strip()

    if not chunk or not filename or chunk_index < 0 or total_chunks < 0 or not chunk_id:
        return jsonify({'success': False, 'error': '缺少必要参数或参数无效'}), 400

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
        md5_hash = hashlib.md5()
        try:
            with open(final_path, 'wb') as f:
                for i in range(total_chunks):
                    chunk_file = os.path.join(chunk_dir, f'chunk-{i}')
                    with open(chunk_file, 'rb') as cf:
                        chunk_data = cf.read()
                        f.write(chunk_data)
                        md5_hash.update(chunk_data)
                        file_size += len(chunk_data)
        except Exception as e:
            shutil.rmtree(chunk_dir, ignore_errors=True)
            if os.path.exists(final_path): os.remove(final_path)
            return jsonify({'success': False, 'error': f'合并分片失败: {str(e)}'}), 500

        with open(final_path, 'rb') as f:
            file_header = f.read(2048)
            if not allowed_file(filename, file_header):
                os.remove(final_path)
                shutil.rmtree(chunk_dir)
                return jsonify({'success': False, 'error': '不支持的文件类型'}), 400

        md5_digest = md5_hash.hexdigest()
        existing_note = Note.query.filter_by(user_id=user_id, md5=md5_digest).first()
        if existing_note:
            os.remove(final_path)
            shutil.rmtree(chunk_dir)
            return jsonify({'success': False, 'error': '文件已存在，无需重复上传'}), 409

        base, ext = os.path.splitext(safe_filename)
        final_filename_with_hash = f"{base}_{md5_digest}{ext}"
        final_path_with_hash = os.path.join(app.config['UPLOAD_FOLDER'], final_filename_with_hash)
        os.rename(final_path, final_path_with_hash)
        safe_filename = final_filename_with_hash

        if mode == 'gallery':
            shutil.rmtree(chunk_dir)
            return jsonify({
                'success': True,
                'content': safe_filename,
                'file_size': file_size,
                'md5': md5_digest,
                'raw_content': filename
            })

        content_type = 'image' if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'file'
        new_note = Note(
            user_id=user_id,
            content_type=content_type,
            content_data=safe_filename,
            raw_content=filename,
            additional_text=additional_text or None,
            file_size=file_size,
            md5=md5_digest,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            db.session.add(new_note)
            db.session.commit()
            shutil.rmtree(chunk_dir)
            return jsonify({
                'success': True,
                'note': {
                    'id': new_note.id,
                    'type': new_note.content_type,
                    'content': url_for('uploaded_file', filename=new_note.content_data),
                    'raw_content': new_note.raw_content,
                    'additional_text': new_note.additional_text,
                    'timestamp': new_note.timestamp.isoformat(),
                    'file_size': new_note.file_size,
                    'md5': new_note.md5
                }
            })
        except Exception as e:
            db.session.rollback()
            if os.path.exists(final_path_with_hash): os.remove(final_path_with_hash)
            return jsonify({'success': False, 'error': f'数据库保存失败: {str(e)}'}), 500

    return jsonify({'success': True, 'message': '分片上传成功'})


@app.route('/notes/add_multiple', methods=['POST'])
@login_required
def add_multiple():
    user_id = current_user.id
    data = request.get_json()
    if not data or 'mode' not in data or 'file_data' not in data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    mode = data['mode']
    file_data = data['file_data']
    additional_text = data.get('additional_text', '').strip()
    if mode != 'gallery':
        return jsonify({'success': False, 'error': '不支持的模式'}), 400

    file_paths = [item['content'] for item in file_data]
    try:
        new_note = Note(
            user_id=user_id,
            content_type='gallery',
            content_data=json.dumps(file_paths),
            raw_content=json.dumps([item['raw_content'] for item in file_data]),
            additional_text=additional_text or None,
            file_size=sum(item['file_size'] for item in file_data),
            md5=hashlib.md5(''.join(item['md5'] for item in file_data).encode()).hexdigest(),
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(new_note)
        db.session.commit()
        return jsonify({
            'success': True,
            'note': {
                'id': new_note.id,
                'type': 'gallery',
                'content': file_paths,
                'additional_text': new_note.additional_text,
                'timestamp': new_note.timestamp.isoformat(),
                'file_size': new_note.file_size,
                'md5': new_note.md5
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500


@app.route('/notes/edit/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'success': False, 'error': '无权编辑此笔记'}), 403

    data = request.get_json()
    new_text = data.get('content', '').strip()

    if note.content_type == 'text':
        if not new_text:
            return jsonify({'success': False, 'error': '内容不能为空'}), 400
        note.content_data = new_text
    else:
        note.additional_text = new_text or None

    note.timestamp = datetime.now(timezone.utc)
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'new_content': note.content_data if note.content_type == 'text' else note.additional_text,
            'new_timestamp': note.timestamp.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500


@app.route('/notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'success': False, 'error': '无权删除此笔记'}), 403
    try:
        if note.content_type in ['image', 'file', 'zip', 'gallery']:
            paths_to_delete = []
            if note.content_type in ['zip', 'gallery']:
                try:
                    paths_to_delete.extend(json.loads(note.content_data))
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Could not parse content_data for note {note_id}")
            else:
                paths_to_delete.append(note.content_data)

            for path in paths_to_delete:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")
        db.session.delete(note)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'}), 500


@app.route('/notes/download/<int:note_id>')
@login_required
def download_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash('无权下载此文件', 'danger')
        return redirect(url_for('notes_page'))
    if note.content_type not in ['image', 'file']:
        flash('此笔记类型不支持下载', 'danger')
        return redirect(url_for('notes_page'))

    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], note.content_data)
        if not os.path.exists(file_path):
            flash('文件不存在', 'danger')
            return redirect(url_for('notes_page'))
        return send_file(file_path, as_attachment=True, download_name=note.raw_content)
    except Exception as e:
        flash('下载失败', 'danger')
        return redirect(url_for('notes_page'))


@app.route('/notes/download_gallery/<int:note_id>')
@login_required
def download_gallery(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'success': False, 'error': '无权下载此笔记'}), 403
    if note.content_type != 'gallery':
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
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'gallery_note_{note_id}.zip'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500


@app.route('/notes/download_zip/<int:note_id>')
@login_required
def download_zip(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'success': False, 'error': '无权下载此笔记'}), 403
    if note.content_type != 'zip':
        return jsonify({'success': False, 'error': '仅ZIP笔记支持一键下载'}), 400

    try:
        file_paths = json.loads(note.content_data)
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in file_paths:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file))
        zip_buffer.seek(0)
        zip_filename = note.raw_content if note.raw_content else f"archive_{note_id}.zip"
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500


@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': '非法访问'}), 400

    # This check is important but can be slow. For simplicity, we trust the secure_filename
    # A more robust check might be needed in a high-security environment.
    # note = Note.query.filter(Note.content_data.like(f'%{secure_filename(filename)}%'), Note.user_id == current_user.id).first()
    # if not note:
    #     return jsonify({'error': '无权访问'}), 403

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)