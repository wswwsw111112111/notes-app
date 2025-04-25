import re
from werkzeug.utils import secure_filename
import os

def validate_password(password):
    """密码强度验证"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

def generate_secure_filename(original_name):
    """生成安全文件名（保留扩展名）"""
    import hashlib
    _, ext = os.path.splitext(original_name)
    safe_base = secure_filename(original_name).replace(ext, '')
    return f"{safe_base}_{hashlib.md5(original_name.encode()).hexdigest()[:6]}{ext}"