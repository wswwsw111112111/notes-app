from Gtest import app, db
from sqlalchemy import text

with app.app_context():
    # 添加新字段到 note 表
    try:
        with db.engine.connect() as conn:
            # 添加 is_locked
            conn.execute(text('ALTER TABLE note ADD COLUMN is_locked BOOLEAN DEFAULT 0'))
            conn.commit()
            print("✅ 添加 is_locked 字段成功")
    except Exception as e:
        print(f"is_locked 字段可能已存在: {e}")

    try:
        with db.engine.connect() as conn:
            # 添加 lock_password_hash
            conn.execute(text('ALTER TABLE note ADD COLUMN lock_password_hash VARCHAR(255)'))
            conn.commit()
            print("✅ 添加 lock_password_hash 字段成功")
    except Exception as e:
        print(f"lock_password_hash 字段可能已存在: {e}")

    try:
        with db.engine.connect() as conn:
            # 添加 encrypted_content
            conn.execute(text('ALTER TABLE note ADD COLUMN encrypted_content TEXT'))
            conn.commit()
            print("✅ 添加 encrypted_content 字段成功")
    except Exception as e:
        print(f"encrypted_content 字段可能已存在: {e}")

    try:
        with db.engine.connect() as conn:
            # 添加 client_timezone
            conn.execute(text('ALTER TABLE note ADD COLUMN client_timezone VARCHAR(50)'))
            conn.commit()
            print("✅ 添加 client_timezone 字段成功")
    except Exception as e:
        print(f"client_timezone 字段可能已存在: {e}")

    try:
        with db.engine.connect() as conn:
            # 为 md5 添加索引
            conn.execute(text('CREATE INDEX IF NOT EXISTS ix_note_md5 ON note (md5)'))
            conn.commit()
            print("✅ 添加 md5 索引成功")
    except Exception as e:
        print(f"md5 索引可能已存在: {e}")

    # 创建 note_share 表
    try:
        db.create_all()
        print("✅ 创建 note_share 表成功")
    except Exception as e:
        print(f"note_share 表可能已存在: {e}")

    print("\n" + "=" * 50)
    print("✅ 数据库迁移完成！")
    print("=" * 50)