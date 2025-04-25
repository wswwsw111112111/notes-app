# utils/file_utils.py
import os
import hashlib

def save_file(file_data, filename, upload_folder):
    filepath = os.path.join(upload_folder, filename)
    with open(filepath, 'wb') as f:
        f.write(file_data)
    return filepath

def calculate_md5(file_data):
    return hashlib.md5(file_data).hexdigest()

def delete_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False