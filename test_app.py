"""
笔记应用自动化冒烟测试
- 使用固定测试账号 test123
- 在生产数据库上运行
- 测试完成后清理该账号的所有数据（但保留账号）
"""

import unittest
import os
import sys
from io import BytesIO
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Gtest import app, db, User, Note, Advertisement
from werkzeug.security import generate_password_hash


class SmokeTestCase(unittest.TestCase):
    """冒烟测试 - 使用固定测试账号"""

    TEST_USERNAME = 'test123'
    TEST_PASSWORD = 'test123456'

    def setUp(self):
        """每个测试前的准备"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        # 创建或获取测试账号
        with app.app_context():
            user = User.query.filter_by(username=self.TEST_USERNAME).first()
            if not user:
                # 账号不存在，创建
                user = User(
                    username=self.TEST_USERNAME,
                    password_hash=generate_password_hash(self.TEST_PASSWORD, method='pbkdf2:sha256')
                )
                db.session.add(user)
                db.session.commit()
                print(f"✅ 创建测试账号: {self.TEST_USERNAME}")
            else:
                # 账号存在，清理旧数据
                self._cleanup_test_data()
                print(f"✅ 使用已存在的测试账号: {self.TEST_USERNAME}")

    def tearDown(self):
        """每个测试后清理数据"""
        with app.app_context():
            self._cleanup_test_data()
            print(f"🧹 已清理测试账号 {self.TEST_USERNAME} 的数据")

    def _cleanup_test_data(self):
        """清理测试账号的所有数据（但保留账号）"""
        user = User.query.filter_by(username=self.TEST_USERNAME).first()
        if user:
            # 删除该用户的所有笔记
            Note.query.filter_by(user_id=user.id).delete()
            db.session.commit()

            # 重置用户为初始状态（非会员）
            user.membership_start = None
            user.membership_end = None
            user.is_super_member = False
            user.storage_limit_gb = 1.0
            user.retention_days = 30
            user.disable_ads = False
            db.session.commit()

    def login(self):
        """登录测试账号"""
        return self.client.post('/login', data={
            'username': self.TEST_USERNAME,
            'password': self.TEST_PASSWORD
        }, follow_redirects=True)

    def logout(self):
        """登出"""
        return self.client.get('/logout', follow_redirects=True)


class TestAuthentication(SmokeTestCase):
    """测试认证功能"""

    def test_01_login_success(self):
        """测试登录成功"""
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.TEST_USERNAME, response.get_data(as_text=True))
        print("✅ 登录测试通过")

    def test_02_logout(self):
        """测试登出"""
        self.login()
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        print("✅ 登出测试通过")


class TestNoteOperations(SmokeTestCase):
    """测试笔记操作"""

    def test_01_create_text_note(self):
        """测试创建文本笔记"""
        self.login()

        response = self.client.post('/notes/add',
                                    json={
                                        'type': 'text',
                                        'content': '这是一条测试笔记',
                                        'filename': None,
                                        'additional_text': ''
                                    },
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        print("✅ 创建文本笔记测试通过")

    def test_02_view_notes(self):
        """测试查看笔记列表"""
        self.login()

        # 先创建一条笔记
        self.client.post('/notes/add',
                        json={
                            'type': 'text',
                            'content': '测试笔记内容',
                            'filename': None,
                            'additional_text': ''
                        },
                        content_type='application/json')

        # 访问笔记页面
        response = self.client.get('/notes')
        self.assertEqual(response.status_code, 200)
        self.assertIn('测试笔记内容', response.get_data(as_text=True))
        print("✅ 查看笔记列表测试通过")

    def test_03_edit_note(self):
        """测试编辑笔记"""
        self.login()

        # 创建笔记
        with app.app_context():
            user = User.query.filter_by(username=self.TEST_USERNAME).first()
            note = Note(
                user_id=user.id,
                content_type='text',
                content_data='原始内容'
            )
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        # 编辑笔记
        response = self.client.post(f'/notes/edit/{note_id}',
                                    json={'content': '修改后的内容'},
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

        # 验证内容已更新
        with app.app_context():
            note = db.session.get(Note, note_id)
            self.assertEqual(note.content_data, '修改后的内容')
        print("✅ 编辑笔记测试通过")

    def test_04_delete_note(self):
        """测试删除笔记"""
        self.login()

        # 创建笔记
        with app.app_context():
            user = User.query.filter_by(username=self.TEST_USERNAME).first()
            note = Note(
                user_id=user.id,
                content_type='text',
                content_data='待删除的内容'
            )
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        # 删除笔记
        response = self.client.post(f'/notes/delete/{note_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

        # 验证已删除
        with app.app_context():
            note = db.session.get(Note, note_id)
            self.assertIsNone(note)
        print("✅ 删除笔记测试通过")


class TestUserFeatures(SmokeTestCase):
    """测试用户功能"""

    def test_01_view_storage_info(self):
        """测试查看存储信息"""
        self.login()

        response = self.client.get('/notes')
        self.assertEqual(response.status_code, 200)
        response_text = response.get_data(as_text=True)
        self.assertIn('可用存储空间', response_text)
        print("✅ 查看存储信息测试通过")

    def test_02_user_profile(self):
        """测试用户信息"""
        with app.app_context():
            user = User.query.filter_by(username=self.TEST_USERNAME).first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, self.TEST_USERNAME)
            print(f"✅ 用户信息正确: {user.username}")


class TestBasicFlow(SmokeTestCase):
    """测试基本流程"""

    def test_complete_workflow(self):
        """测试完整工作流：登录 -> 创建笔记 -> 查看 -> 编辑 -> 删除 -> 登出"""
        # 1. 登录
        response = self.login()
        self.assertEqual(response.status_code, 200)
        print("  ✓ 步骤1: 登录成功")

        # 2. 创建笔记
        response = self.client.post('/notes/add',
                                    json={
                                        'type': 'text',
                                        'content': '完整流程测试笔记',
                                        'filename': None,
                                        'additional_text': ''
                                    },
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        print("  ✓ 步骤2: 创建笔记成功")

        # 3. 查看笔记
        response = self.client.get('/notes')
        self.assertIn('完整流程测试笔记', response.get_data(as_text=True))
        print("  ✓ 步骤3: 查看笔记成功")

        # 4. 获取笔记ID并编辑
        with app.app_context():
            user = User.query.filter_by(username=self.TEST_USERNAME).first()
            note = Note.query.filter_by(user_id=user.id).first()
            note_id = note.id

            response = self.client.post(f'/notes/edit/{note_id}',
                                        json={'content': '编辑后的内容'},
                                        content_type='application/json')
            self.assertEqual(response.status_code, 200)
        print("  ✓ 步骤4: 编辑笔记成功")

        # 5. 删除笔记
        response = self.client.post(f'/notes/delete/{note_id}')
        self.assertEqual(response.status_code, 200)
        print("  ✓ 步骤5: 删除笔记成功")

        # 6. 登出
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        print("  ✓ 步骤6: 登出成功")

        print("✅ 完整工作流测试通过")


def run_smoke_tests():
    """运行冒烟测试"""
    print("\n" + "=" * 70)
    print("🚀 开始冒烟测试")
    print("=" * 70)
    print(f"测试账号: {SmokeTestCase.TEST_USERNAME}")
    print(f"数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("=" * 70 + "\n")

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestAuthentication))
    suite.addTests(loader.loadTestsFromTestCase(TestNoteOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestUserFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestBasicFlow))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print(f"✅ 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败: {len(result.failures)}")
    print(f"⚠️  错误: {len(result.errors)}")
    print(f"📝 总计: {result.testsRun}")
    print("=" * 70)

    # 最终清理提示
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！测试数据已自动清理。")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_smoke_tests()
    sys.exit(0 if success else 1)