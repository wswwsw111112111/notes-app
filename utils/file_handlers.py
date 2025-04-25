import os
import hashlib
import base64
from werkzeug.utils import secure_filename
from flask import current_app
from models.note import Note


def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def save_file(file_data, filename, user_id):
    try:
        # 生成MD5
        md5_hash = hashlib.md5(file_data).hexdigest()

        # 检查重复
        if Note.query.filter_by(md5=md5_hash, user_id=user_id).first():
            return None, '文件已存在'

        # 保存文件
        safe_name = secure_filename(filename)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_name)

        with open(save_path, 'wb') as f:
            f.write(file_data)

        return {
                   'filename': safe_name,
                   'md5': md5_hash,
                   'size': len(file_data)
               }, None

    except Exception as e:
        current_app.logger.error(f'文件保存失败: {str(e)}')
        return None, str(e)


def handle_chunk_upload(chunk, chunk_id, chunk_index):
    try:
        chunk_dir = os.path.join(current_app.config['TEMP_CHUNK_DIR'], chunk_id)
        os.makedirs(chunk_dir, exist_ok=True)
        chunk_path = os.path.join(chunk_dir, f'chunk_{chunk_index}')
        chunk.save(chunk_path)
        return True, None
    except Exception as e:
        return False, str(e)


def merge_chunks(chunk_id, filename, user_id):
    try:
        chunk_dir = os.path.join(current_app.config['TEMP_CHUNK_DIR'], chunk_id)
        chunks = sorted(os.listdir(chunk_dir),
                        key=lambda x: int(x.split('_')[1]))

        # 合并文件
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                 secure_filename(filename))
        with open(full_path, 'wb') as f:
            for chunk_name in chunks:
                with open(os.path.join(chunk_dir, chunk_name), 'rb') as cf:
                    f.write(cf.read())

        # 计算哈希
        with open(full_path, 'rb') as f:
            file_data = f.read()
            md5_hash = hashlib.md5(file_data).hexdigest()

        # 清理临时文件
        shutil.rmtree(chunk_dir)

        return {
                   'filename': secure_filename(filename),
                   'md5': md5_hash,
                   'size': len(file_data)
               }, None

    except Exception as e:
        return None, str(e)