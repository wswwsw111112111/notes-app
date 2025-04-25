from flask import Flask
from config import config
from extensions import db, login_manager, migrate, csrf
import routes.notes as notes_bp
import os
import models
from routes.auth import auth_bp  # ✅ 正确导入蓝图对象
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # 正确的写法 ✅
    from routes.auth import auth_bp
    from routes.notes import notes_bp

    # 直接注册蓝图对象
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(notes_bp, url_prefix='/notes')
    # 创建上传目录
    with app.app_context():
        for folder in [app.config['UPLOAD_FOLDER'],
                       app.config['TEMP_CHUNK_DIR'],
                       app.config['AVATAR_FOLDER']]:
            os.makedirs(folder, exist_ok=True)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)