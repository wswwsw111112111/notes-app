from Gtest import app, db

with app.app_context():
    # 删除所有表并重建
    db.drop_all()
    db.create_all()
    print("✅ 数据库已重建！")