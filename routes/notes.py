from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from models.note import Note
from app import db
from datetime import datetime, timezone
from sqlalchemy import or_
from datetime import timedelta
import hashlib

notes_bp = Blueprint('notes', __name__)


@notes_bp.route('/')
@login_required
def index():
    return render_template('notes/index.html')


@notes_bp.route('/api/notes', methods=['GET'])
@login_required
def get_notes():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.timestamp.desc()).paginate(page=page,
                                                                                                   per_page=per_page)
    return jsonify({
        'notes': [note.to_dict() for note in notes.items],
        'has_next': notes.has_next,
        'has_prev': notes.has_prev,
        'page': notes.page,
        'pages': notes.pages
    })


@notes_bp.route('/api/notes/search', methods=['GET'])
@login_required
def search_notes():
    query = request.args.get('q', '')
    notes = Note.query.filter(
        Note.user_id == current_user.id,
        or_(
            Note.content_data.ilike(f'%{query}%'),
            Note.raw_content.ilike(f'%{query}%')
        )
    ).all()
    return jsonify({'notes': [note.to_dict() for note in notes]})


@notes_bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'success': False, 'error': '无权删除此笔记'}), 403

    db.session.delete(note)
    db.session.commit()
    return jsonify({'success': True})


@notes_bp.route('/api/notes/<int:note_id>/share', methods=['POST'])
@login_required
def share_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'success': False, 'error': '无权分享此笔记'}), 403

    note.share_token = hashlib.sha256(f"{note_id}{current_user.id}{datetime.now()}".encode()).hexdigest()
    note.share_expiry = datetime.now(timezone.utc) + timedelta(days=7)
    db.session.commit()

    share_url = url_for('notes.view_shared', token=note.share_token, _external=True)
    return jsonify({'success': True, 'share_url': share_url})


@notes_bp.route('/shared/<token>', methods=['GET'])
def view_shared(token):
    note = Note.query.filter_by(share_token=token).first()
    if not note or note.share_expiry < datetime.now(timezone.utc):
        return render_template('errors/404.html'), 404

    return render_template('notes/shared.html', note=note)