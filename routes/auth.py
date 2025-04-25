from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from extensions import db
import os
from utils.security import validate_password, generate_secure_filename


auth_bp = Blueprint('auth', __name__,
                  template_folder='templates/auth',  # ⚠️ 导致路径嵌套
                  static_folder='static')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('notes.index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('登录成功', 'success')
            return redirect(url_for('notes.index'))

        flash('无效的用户名或密码', 'danger')
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('auth.register'))

        if not validate_password(password):
            flash('密码必须包含大小写字母和数字，且至少8位', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('auth.login'))


# @auth_bp.route('/settings', methods=['GET', 'POST'])
# @login_required
# def settings():
#     if request.method == 'POST':
#         # 处理头像上传
#         if 'avatar' in request.files:
#             avatar = request.files['avatar']
#             if avatar and allowed_file(avatar.filename):
#                 filename = generate_secure_filename(avatar.filename)
#                 avatar.save(os.path.join(current_app.config['AVATAR_FOLDER'], filename))
#                 current_user.avatar = filename
#
#         # 更新密码
#         new_password = request.form.get('new_password')
#         if new_password:
#             if not validate_password(new_password):
#                 flash('密码不符合安全要求', 'danger')
#                 return redirect(url_for('auth.settings'))
#
#             current_user.set_password(new_password)
#
#         db.session.commit()
#         flash('设置已更新', 'success')
#
#     return render_template('settings.html')
