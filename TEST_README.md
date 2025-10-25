# 笔记应用 - 自动化测试文档

## 📋 目录结构

```
notescloude/
├── Gtest.py                      # 主应用
├── test_app.py                   # 自动化测试套件
├── test_data_generator.py        # 测试数据生成器
├── run_tests.sh                  # Linux/Mac测试脚本
├── run_tests.bat                 # Windows测试脚本
├── TEST_README.md                # 本文件
└── test_files/                   # 测试文件目录（自动生成）
    ├── small_image.png
    ├── medium_image.jpg
    ├── large_image.png
    ├── gallery_01.png ~ gallery_10.png
    ├── mixed_img_1.png ~ mixed_img_5.png
    ├── mixed_doc_1.txt ~ mixed_doc_3.txt
    ├── large_50mb.bin
    └── invalid.xyz
```

---

## 🚀 快速开始

### 方法1：使用自动化脚本（推荐）

**Windows:**
```bash
run_tests.bat
```

**Linux/Mac:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

### 方法2：手动运行

```bash
# 1. 生成测试数据
python test_data_generator.py

# 2. 运行测试
python test_app.py

# 3. 清理测试文件（可选）
python -c "from test_data_generator import TestDataGenerator; TestDataGenerator().cleanup()"
```

---

## 📦 依赖安装

```bash
pip install flask flask-sqlalchemy flask-login flask-wtf pillow python-magic-bin
```

或使用 requirements.txt:
```bash
pip install -r requirements.txt
```

---

## 🧪 测试覆盖范围

### 1. 用户认证测试 (TestAuthentication)
- ✅ 用户注册成功
- ✅ 重复用户名注册失败
- ✅ 禁止注册admin用户名
- ✅ 登录成功
- ✅ 错误密码登录失败
- ✅ 管理员登录成功
- ✅ 管理员错误凭据失败
- ✅ 登出功能

### 2. 笔记操作测试 (TestNoteOperations)
- ✅ 创建文本笔记
- ✅ 上传图片笔记
- ✅ 编辑笔记
- ✅ 删除笔记
- ✅ 笔记分页功能

### 3. 存储管理测试 (TestStorageManagement)
- ✅ 免费用户1GB限制
- ✅ 会员用户100GB限制
- ✅ 超级会员无限存储
- ✅ 存储使用量计算

### 4. 会员管理测试 (TestMembershipManagement)
- ✅ 升级为会员
- ✅ 升级为超级会员
- ✅ 会员过期检测

### 5. 管理员功能测试 (TestAdminFunctions)
- ✅ 访问用户管理
- ✅ 更新用户会员状态
- ✅ 搜索用户
- ✅ 非管理员无权访问

### 6. 广告系统测试 (TestAdvertisementSystem)
- ✅ 创建广告
- ✅ 非会员显示广告
- ✅ 会员不显示广告

### 7. 文件验证测试 (TestFileValidation)
- ✅ 允许的文件格式
- ✅ 不允许的文件格式

### 8. 笔记保留期测试 (TestNoteRetention)
- ✅ 免费用户30天保留期
- ✅ 过期笔记自动删除

---

## 📊 测试报告示例

```
======================================================================
测试总结
======================================================================
运行测试: 35
成功: 35
失败: 0
错误: 0
======================================================================
```

---

## 🔧 自定义测试

### 添加新测试用例

在 `test_app.py` 中添加新的测试类或测试方法：

```python
class TestNewFeature(NotesAppTestCase):
    """测试新功能"""

    def test_01_new_feature(self):
        """测试新功能描述"""
        # 测试代码
        self.assertTrue(True)
```

### 生成自定义测试数据

在 `test_data_generator.py` 中添加新方法：

```python
def generate_custom_data(self):
    """生成自定义测试数据"""
    # 生成代码
    pass
```

---

## 🐛 常见问题

### Q1: 测试失败：数据库锁定错误
**原因:** 主应用正在运行，占用了数据库
**解决:** 停止主应用后再运行测试

### Q2: 导入错误：找不到模块
**原因:** 依赖包未安装
**解决:**
```bash
pip install flask flask-sqlalchemy flask-login flask-wtf pillow
```

### Q3: 文件权限错误
**原因:** Linux/Mac下脚本没有执行权限
**解决:**
```bash
chmod +x run_tests.sh
```

### Q4: 测试数据文件未生成
**原因:** PIL(Pillow)库未安装
**解决:**
```bash
pip install pillow
```

### Q5: CSRF Token错误
**原因:** 测试配置问题
**解决:** 确保 `test_app.py` 中有这行配置：
```python
app.config['WTF_CSRF_ENABLED'] = False
```

---

## 📝 测试最佳实践

### 1. 定期运行测试
- 每次修改代码后运行
- 提交代码前运行
- 部署前运行完整测试

### 2. 测试驱动开发(TDD)
```
1. 编写测试用例
2. 运行测试（应该失败）
3. 编写功能代码
4. 运行测试（应该通过）
5. 重构代码
6. 再次运行测试
```

### 3. 独立性原则
- 每个测试用例独立运行
- 不依赖其他测试的结果
- 使用setUp和tearDown清理环境

### 4. 命名规范
```python
# 测试类命名
class TestFeatureName(NotesAppTestCase):
    pass

# 测试方法命名（按执行顺序编号）
def test_01_description(self):
    pass
```

### 5. 断言使用
```python
# 推荐使用的断言
self.assertEqual(a, b)           # a == b
self.assertTrue(condition)       # condition is True
self.assertIsNone(obj)          # obj is None
self.assertIn(item, container)  # item in container
```

---

## 🔍 调试测试

### 运行单个测试类
```bash
python test_app.py TestAuthentication
```

### 运行单个测试方法
```bash
python -m unittest test_app.TestAuthentication.test_01_register_success
```

### 详细输出模式
```bash
python test_app.py -v
```

### 使用pytest（更强大的测试框架）
```bash
# 安装pytest
pip install pytest pytest-cov

# 运行测试
pytest test_app.py -v

# 生成覆盖率报告
pytest test_app.py --cov=. --cov-report=html
```

---

## 📈 持续集成(CI)

### GitHub Actions 配置示例

创建 `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        python test_data_generator.py
        python test_app.py
```

---

## 📚 扩展阅读

- [unittest 官方文档](https://docs.python.org/3/library/unittest.html)
- [pytest 官方文档](https://docs.pytest.org/)
- [Flask Testing 文档](https://flask.palletsprojects.com/en/2.3.x/testing/)

---

## 🎯 测试checklist

上线前确保以下测试全部通过：

- [ ] 所有单元测试通过
- [ ] 用户注册登录功能正常
- [ ] 笔记CRUD操作正常
- [ ] 文件上传下载正常
- [ ] 存储限制正确执行
- [ ] 会员系统正常工作
- [ ] 管理后台功能正常
- [ ] 广告系统正确显示
- [ ] 分页功能正常
- [ ] MD5显示正确
- [ ] 图片缩放功能正常

---

**最后更新:** 2025年10月12日
**版本:** v2.1
**维护者:** 开发团队