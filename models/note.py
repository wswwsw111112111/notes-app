from datetime import datetime
from extensions import db

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    title = db.Column(db.String(120))
    content_type = db.Column(db.String(20), nullable=False)
    content_data = db.Column(db.Text, nullable=False)
    raw_content = db.Column(db.Text)
    file_size = db.Column(db.Integer)
    md5 = db.Column(db.String(32), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Note {self.id} {self.content_type}>'