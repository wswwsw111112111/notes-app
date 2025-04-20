import os
import base64
import uuid
from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, session, send_from_directory, flash, abort
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta  # 增加 timedelta 导入
from functools import wraps
from flask_wtf.csrf import CSRFProtect
import magic
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # 设置 session 超时为2小时
csrf = CSRFProtect(app)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'notes_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Upload Folder Configuration
UPLOAD_FOLDER = os.path.join(basedir, 'Uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    notes = db.relationship('Note', backref='author', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # 'text', 'image', or 'file'
    content_data = db.Column(db.Text, nullable=False)
    raw_content = db.Column(db.Text)  # 存储原始文件名
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    file_size = db.Column(db.Integer, nullable=True)  # 新增字段，存储文件大小（字节）

    def __repr__(self):
        return f'<Note {self.id} {self.content_type}>'


# Create Database Tables
with app.app_context():
    db.create_all()
    print("Database tables checked/created.")


# Login Required Decorator with Timeout Check
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'error': '请先登录以访问此页面', 'redirect': url_for('login')}), 401
            flash('请先登录以访问此页面。', 'warning')
            return redirect(url_for('login'))

        # 检查 session 是否超时
        if not session.permanent:
            session.permanent = True
        last_activity = session.get('last_activity', datetime.now(timezone.utc))
        last_activity = last_activity if isinstance(last_activity, datetime) else datetime.fromisoformat(last_activity)
        current_time = datetime.now(timezone.utc)
        if (current_time - last_activity).total_seconds() > app.config['PERMANENT_SESSION_LIFETIME'].total_seconds():
            session.clear()
            if request.is_json or request.headers.get('Accept') == 'application/json':
                # 跳过 CSRF 验证，直接返回超时响应
                response = jsonify({'success': False, 'error': '会话已超时，请重新登录', 'redirect': url_for('login')})
                response.status_code = 401
                return response
            flash('会话已超时，请重新登录。', 'warning')
            return redirect(url_for('login'))

        # 更新最后活动时间
        session['last_activity'] = current_time.isoformat()
        return f(*args, **kwargs)

    return decorated_function
# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        # 每次请求时更新 last_activity
        session['last_activity'] = datetime.now(timezone.utc).isoformat()  # 去掉 + 'Z'
        return redirect(url_for('notes_page'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('notes_page'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('请输入用户名和密码。', 'danger')
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True
            session['last_activity'] = datetime.now(timezone.utc).isoformat()  # 去掉 + 'Z'
            flash('登录成功！', 'success')
            return redirect(url_for('notes_page'))
        else:
            flash('用户名或密码无效。', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('notes_page'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not username or not password or not confirm_password:
            flash('所有字段都是必填的。', 'danger')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('两次输入的密码不一致。', 'danger')
            return redirect(url_for('register'))
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('该用户名已被注册。', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        try:
            db.session.commit()
            flash('注册成功！请登录。', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'注册时发生错误: {e}', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html')


# 其他路由保持不变
@app.route('/logout')
@login_required
def logout():
    session.clear()  # 清除整个 session，包括 last_activity
    flash('您已成功登出。', 'info')
    return redirect(url_for('login'))


@app.route('/notes')
@login_required
def notes_page():
    user_id = session['user_id']
    user_notes = Note.query.filter_by(user_id=user_id).order_by(Note.timestamp.asc()).all()
    return render_template('notes.html', notes=user_notes, username=session.get('username'))

@app.route('/notes/add', methods=['POST'])
@login_required
def add_note():
    user_id = session['user_id']
    data = request.get_json()
    if not data or 'type' not in data or 'content' not in data:
        return jsonify({'success': False, 'error': '无效的请求数据'})

    note_type = data['type']
    content = data['content']
    filename = data.get('filename')

    new_note = Note(user_id=user_id, content_type=note_type, timestamp=datetime.now(timezone.utc))

    if note_type == 'text':
        new_note.content_data = content
    elif note_type in ['image', 'file']:
        if not filename:
            return jsonify({'success': False, 'error': '文件名缺失'})
        try:
            file_data = base64.b64decode(content.split(',')[1])
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
            with open(file_path, 'wb') as f:
                f.write(file_data)
            new_note.content_data = secure_filename(filename)
            new_note.raw_content = filename
            new_note.file_size = len(file_data)  # 计算文件大小（字节）
        except Exception as e:
            return jsonify({'success': False, 'error': f'文件保存失败: {str(e)}'})

    try:
        db.session.add(new_note)
        db.session.commit()
        return jsonify({
            'success': True,
            'note': {
                'id': new_note.id,
                'type': new_note.content_type,
                'content': new_note.content_data if note_type == 'text' else url_for('uploaded_file', filename=new_note.content_data),
                'raw_content': new_note.raw_content,
                'timestamp': new_note.timestamp.isoformat(),
                'file_size': new_note.file_size  # 返回文件大小
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'数据库错误: {str(e)}'})


@app.route('/notes/edit/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    user_id = session['user_id']
    note = Note.query.get_or_404(note_id)
    if note.user_id != user_id:
        abort(403)
    if note.content_type != 'text':
        return jsonify({'success': False, 'error': '目前不支持编辑图片类型的笔记'}), 400
    data = request.get_json()
    new_content = data.get('content')
    if new_content is None or not new_content.strip():
        return jsonify({'success': False, 'error': '笔记内容不能为空'}), 400
    try:
        note.content_data = new_content
        note.timestamp = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '笔记已更新',
            'new_content': new_content,
            'new_timestamp': note.timestamp.isoformat() + 'Z'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error editing note {note_id}: {e}")
        return jsonify({'success': False, 'error': '更新笔记时出错'}), 500


@app.route('/notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    user_id = session['user_id']
    note = Note.query.get_or_404(note_id)
    if note.user_id != user_id:
        abort(403)
    try:
        if note.content_type in ['image', 'file']:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], note.content_data)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as file_e:
                    print(f"Warning: Could not delete file {filepath}: {file_e}")
        db.session.delete(note)
        db.session.commit()
        return jsonify({'success': True, 'message': '笔记已删除'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting note {note_id}: {e}")
        return jsonify({'success': False, 'error': '删除笔记时出错'}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=5000)