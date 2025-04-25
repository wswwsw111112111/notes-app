from flask import Blueprint, request, jsonify, send_from_directory, url_for
from flask_login import login_required, current_user
from models.note import Note
from app import db, app
import os
import hashlib
import base64
from werkzeug.utils import secure_filename
from datetime import datetime, timezone

files_bp = Blueprint('files', __name__)


@files_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@files_bp.route('/api/files/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': '不支持的文件类型'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    with open(filepath, 'rb') as f:
        file_data = f.read()
        md5_hash = hashlib.md5(file_data).hexdigest()

    existing = Note.query.filter_by(user_id=current_user.id, md5=md5_hash).first()
    if existing:
        os.remove(filepath)
        return jsonify({'success': False, 'error': '文件已存在'}), 409

    content_type = 'image' if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'file'
    note = Note(
        user_id=current_user.id,
        content_type=content_type,
        content_data=filename,
        raw_content=filename,
        file_size=len(file_data),
        md5=md5_hash
    )
    db.session.add(note)
    db.session.commit()

    return jsonify({
        'success': True,
        'note': note.to_dict(),
        'url': url_for('files.uploaded_file', filename=filename)
    })


def allowed_file(filename):
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in app.config['ALLOWED_EXTENSIONS']