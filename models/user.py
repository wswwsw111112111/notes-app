from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    avatar = db.Column(db.String(120))
    notes = db.relationship('Note', backref='author', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    from werkzeug.security import generate_password_hash, check_password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)  # ✅ 生成哈希

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  # ✅ 安全验证
