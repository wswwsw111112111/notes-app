# utils/db_utils.py
from extensions import db

def commit_changes():
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return False

def add_to_db(obj):
    try:
        db.session.add(obj)
        return commit_changes()
    except Exception as e:
        print(f"Error adding to database: {str(e)}")
        return False