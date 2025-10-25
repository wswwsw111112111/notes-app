**完全理解！** 我会给你生成一份**超详细的项目文档**，包含所有关键信息，让任何AI都能快速理解并继续开发。

---

# 📝 笔记应用系统 - 完整项目文档 v2.0

**最后更新**: 2025-10-20
**开发状态**: 核心功能已完成，系统稳定运行

---

## 📋 一、项目概述

这是一个基于 **Flask** 的**多用户云笔记管理系统**，支持文本、图片、文件、画廊、压缩包等多种笔记类型。系统具有完善的会员体系，提供笔记加锁、分享、MD5索引、搜索等高级功能。

### 核心特性
- 🔐 **用户系统**：注册/登录/会员体系
- 📝 **多种笔记类型**：文本、图片、文件、画廊（多图）、ZIP压缩包
- 👑 **三级会员体系**：免费用户 / 会员 / 超级会员
- 🔒 **笔记加密**：全局统一密码锁（会员专属）
- 📤 **笔记分享**：时效分享链接（会员专属）
- 🔍 **双模式搜索**：MD5索引搜索 + 全文搜索
- 🌍 **时区自适应**：自动使用客户端时区
- 📊 **后台管理**：用户管理、会员管理、广告管理
- 💾 **大文件上传**：5MB分片上传，支持断点续传

---

## 🛠 二、技术栈

### 后端
- **框架**: Flask 3.x
- **数据库**: SQLite（SQLAlchemy ORM）
- **认证**: Flask-Login
- **CSRF保护**: Flask-WTF
- **密码加密**: Werkzeug Security + PBKDF2
- **文件处理**: Werkzeug Utils
- **内容加密**: Fernet (cryptography)

### 前端
- **模板引擎**: Jinja2
- **样式**: 原生CSS（响应式设计，支持移动端）
- **脚本**: 原生JavaScript（ES6+）
- **文件压缩**: JSZip 3.10.1 (CDN)

### 存储
- **文件存储**: 本地文件系统 (`uploads/` 目录)
- **分片上传**: 5MB/片，临时目录 `uploads/temp/`
- **数据库**: SQLite 文件 `notes_app.db`

---

## 🎯 三、功能清单

### ✅ 已实现功能

#### 1. 用户系统
- [x] 用户注册（禁止注册 'admin' 用户名）
- [x] 用户登录/登出
- [x] 密码哈希存储（PBKDF2-SHA256）
- [x] 会员等级系统：
  - **免费用户**: 1GB存储，保留30天，显示广告
  - **会员**: 100GB存储，保留365天，无广告
  - **超级会员**: 无限存储，永久保留，无广告
- [x] 存储空间配额管理（实时显示在顶部导航栏）
- [x] 会员过期自动处理

#### 2. 笔记管理
- [x] **文本笔记**：支持URL自动链接化
- [x] **图片笔记**：
  - 粘贴上传（Ctrl+V）
  - 拖拽上传
  - 点击上传按钮
  - 自动生成缩略图
- [x] **单文件上传**：支持所有文件类型
- [x] **画廊上传**（多图）：
  - 免费用户：最多20张/次
  - 会员：最多100张/次
  - 懒加载显示（每次20张）
  - 图片点击放大预览
  - 键盘导航（左右箭头）
  - 鼠标滚轮缩放
- [x] **ZIP压缩包上传**：多文件自动打包
- [x] 笔记编辑（修改附加文本）
- [x] 笔记删除（同步删除磁盘文件）
- [x] 笔记分页显示（10条/页）
- [x] 时间戳自动转换为客户端时区（UTC → 本地）
- [x] 文件MD5计算和显示
- [x] 文件大小显示（MB格式）

#### 3. 笔记搜索
- [x] **MD5搜索**：精确搜索（至少8位）
- [x] **文本搜索**：模糊搜索笔记内容
- [x] 搜索结果高亮显示
- [x] 回车键快速搜索
- [x] 搜索框与笔记栏对齐

#### 4. 笔记加锁（会员专属）✨
- [x] **全局统一锁密码**：
  - 首次上锁设置密码（至少4位）
  - 后续上锁无需重复输入
  - 密码存储在 `user.note_lock_password_hash`
- [x] **加锁效果**：
  - 内容模糊显示（CSS blur）
  - 备份原内容到 `encrypted_content`
  - 显示"🔒 此笔记已加锁"
- [x] **解锁机制**：
  - 每个锁定笔记需单独解锁
  - 解锁后永久移除锁定状态
  - 恢复原始内容

#### 5. 笔记分享（会员专属）✨
- [x] **生成时效分享链接**：
  - 支持时长：5分钟、30分钟、1小时、6小时、24小时、3天、7天、30天
  - 生成唯一token（URL安全的Base64）
  - 记录访问次数
- [x] **分享管理**：
  - 查看最近10条分享记录
  - 显示分享状态（生效中/已过期/已撤销）
  - 显示访问统计
  - 一键撤销分享
- [x] **分享访问**：
  - 公开访问（无需登录）
  - 画廊懒加载（每次20张）
  - 图片点击放大预览
  - 文件下载权限控制
  - 加锁笔记显示"已加锁"

#### 6. 上传功能
- [x] **大文件分片上传**：
  - 5MB/片
  - 进度条显示
  - 前端存储空间预检查
  - 后端存储空间验证
- [x] **拖拽上传支持**
- [x] **三种上传模式**：
  - 单一上传：一次一个文件
  - 画廊上传：一次多张图片
  - 压缩包上传：自动打包成ZIP
- [x] **文件类型限制**：
  - 图片：.png, .jpg, .jpeg, .gif
  - 文档：.pdf, .txt, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .md
  - 压缩包：.zip, .rar, .7z
  - 媒体：.mp4, .mov, .avi, .mp3
  - 其他：.exe, .msi, .apk, .dmg, .iso

#### 7. 界面功能
- [x] **顶部导航栏**：
  - 笔记应用下拉菜单（设置、分享管理等）
  - 存储空间实时显示
  - 用户信息和会员标识
  - 退出登录
- [x] **响应式设计**：
  - 桌面端：三栏布局（广告-笔记-广告）
  - 移动端：单栏布局（隐藏广告）
- [x] **Flash消息提示**：成功/错误/警告/信息
- [x] **广告系统**：
  - 左右侧边栏广告位
  - 会员自动隐藏广告
  - 广告可关闭（5分钟后自动重新加载）
  - 目标用户定向（全部/非会员/特定用户）

#### 8. 后台管理（仅admin）
- [x] **用户管理**：
  - 用户列表查看（分页显示）
  - 用户搜索（ID/用户名）
  - 会员状态查看
- [x] **会员管理**：
  - 开通/取消会员
  - 设置/取消超级会员
  - 调整存储配额
- [x] **广告管理**：
  - 添加广告（图片URL、链接、频率）
  - 编辑广告
  - 删除广告
  - 目标用户设置
- [x] **独立管理入口**：
  - 独立登录页面（安全路径）
  - 强密码保护
  - 验证码机制

---

## 🗄 四、数据库结构

### 表结构详解

#### 1. `user` - 用户表
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc')),
    membership_start DATETIME,
    membership_end DATETIME,
    is_super_member BOOLEAN DEFAULT 0,
    storage_limit_gb FLOAT DEFAULT 1.0,
    retention_days INTEGER DEFAULT 30,
    disable_ads BOOLEAN DEFAULT 0,
    note_lock_password_hash VARCHAR(255),  -- ⭐ 全局锁密码
    INDEX idx_username (username)
);
```

**字段说明**：
- `note_lock_password_hash`: 用户的全局笔记锁密码（首次加锁时设置）

#### 2. `note` - 笔记表
```sql
CREATE TABLE note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content_type VARCHAR(20) NOT NULL,  -- text/image/file/zip/gallery
    content_data TEXT NOT NULL,
    raw_content TEXT,
    additional_text TEXT,
    timestamp DATETIME NOT NULL DEFAULT (datetime('now', 'utc')),
    file_size INTEGER,
    md5 VARCHAR(32),  -- ⭐ MD5索引
    is_locked BOOLEAN DEFAULT 0,  -- ⭐ 是否加锁
    lock_password_hash VARCHAR(255),  -- 锁密码（冗余存储）
    encrypted_content TEXT,  -- ⭐ 加密备份内容
    client_timezone VARCHAR(50),  -- 客户端时区
    FOREIGN KEY (user_id) REFERENCES user(id),
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_md5 (md5)
);
```

**content_type 类型说明**：
- `text`: 纯文本笔记
- `image`: 单张图片
- `file`: 单个文件
- `gallery`: 画廊（多张图片，content_data为JSON数组）
- `zip`: 压缩包

#### 3. `advertisement` - 广告表
```sql
CREATE TABLE advertisement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url VARCHAR(255) NOT NULL,
    link VARCHAR(255) NOT NULL,
    frequency_minutes INTEGER DEFAULT 5,
    target_users TEXT DEFAULT '{"type": "non_member"}'  -- JSON格式
);
```

**target_users 格式**：
```json
{"type": "all"}  // 所有用户
{"type": "non_member"}  // 非会员
{"users": [1,2,3]}  // 特定用户ID
```

#### 4. `note_share` - 笔记分享表 ⭐
```sql
CREATE TABLE note_share (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER NOT NULL,
    share_token VARCHAR(64) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT (datetime('now', 'utc')),
    expires_at DATETIME NOT NULL,
    access_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,  -- 是否生效
    FOREIGN KEY (note_id) REFERENCES note(id) ON DELETE CASCADE,
    INDEX idx_share_token (share_token)
);
```

---

## 📁 五、文件结构

```
project/
├── Gtest.py                    # ⭐ 主程序文件（约1400行）
├── requirements.txt            # Python依赖包
├── add_lock_password.py        # 数据库迁移脚本（添加锁密码字段）
├── notes_app.db                # SQLite数据库文件
├── uploads/                    # ⭐ 文件上传目录
│   ├── temp/                  # 临时分片目录
│   ├── [user_id]/             # 用户文件夹
│   │   └── [YYYYMMDD]/        # 日期文件夹
│   │       └── [files]        # 用户上传的文件
│   └── [直接上传的文件]
├── templates/                  # ⭐ 模板文件目录
│   ├── base.html              # 基础模板（导航栏、存储空间显示）
│   ├── login.html             # 登录页面
│   ├── register.html          # 注册页面
│   ├── notes.html             # ⭐ 主笔记页面（核心，约900行）
│   ├── gallery.html           # 画廊查看页面
│   ├── admin.html             # 后台管理页面
│   ├── admin_login.html       # 管理员登录页面
│   ├── my_shares.html         # ⭐ 分享管理页面
│   ├── shared_note.html       # ⭐ 分享查看页面（公开访问）
│   └── error.html             # 错误提示页面
└── static/                     # 静态资源（可选）
```

---

## 🔌 六、核心API路由

### 认证相关
```python
GET  /login                    # 登录页面
POST /login                    # 登录提交
GET  /register                 # 注册页面
POST /register                 # 注册提交
GET  /logout                   # 登出
GET  /secure_admin_portal_x9k2m  # 管理员登录入口（安全路径）
```

### 笔记相关
```python
GET  /notes                    # 笔记列表（支持分页）
POST /notes/add                # 添加笔记（文本/图片）
POST /notes/upload_chunk       # 分片上传
POST /notes/add_multiple       # 添加画廊笔记
POST /notes/edit/<id>          # 编辑笔记
POST /notes/delete/<id>        # 删除笔记
GET  /notes/search             # 搜索（MD5/文本）
GET  /notes/gallery/<id>       # 查看画廊
GET  /notes/download/<id>      # 下载文件 ⭐ 允许公开访问
GET  /notes/download_gallery/<id>  # 下载画廊ZIP ⭐ 允许公开访问
GET  /notes/download_zip/<id>      # 下载压缩包 ⭐ 允许公开访问
```

### 笔记加锁（会员）⭐
```python
POST /notes/lock/<id>          # 加锁笔记
POST /notes/unlock/<id>        # 解锁笔记
```

### 笔记分享（会员）⭐
```python
POST /notes/share/<id>              # 生成分享链接
GET  /notes/my_shares               # 分享管理页面
POST /notes/share/<share_id>/revoke # 撤销分享
GET  /shared/<token>                # 访问分享笔记 ⭐ 公开访问
```

### 管理相关
```python
GET  /admin                    # 后台管理页面
POST /admin/update_membership  # 更新会员状态
POST /admin/ads/add            # 添加广告
POST /admin/ads/update/<id>    # 更新广告
POST /admin/ads/delete/<id>    # 删除广告
```

### 静态文件
```python
GET  /uploads/<filename>       # 文件访问 ⭐ 允许公开访问
```

---

## ⚙️ 七、核心功能实现说明

### 1. 分片上传流程
```
前端流程：
1. 用户选择文件
2. 检查存储空间（读取顶部导航栏）
3. 将文件切分为5MB的块
4. 依次上传每个块，附带元数据：
   - chunk: 文件块
   - filename: 原始文件名
   - chunkIndex: 当前块索引
   - totalChunks: 总块数
   - chunkId: 上传会话ID
   - totalFileSize: 文件总大小
   - timezone: 客户端时区
5. 显示进度条
6. 最后一块上传完成后合并

后端流程：
1. 接收块并保存到临时目录 temp/[chunkId]/
2. 第一个块时检查存储空间
3. 最后一块时：
   - 合并所有块
   - 计算MD5
   - 保存到数据库
   - 删除临时文件
```

### 2. 笔记加锁机制 ⭐
```
加锁流程：
1. 首次加锁：
   - 提示用户设置全局密码（至少4位）
   - 密码哈希存储到 user.note_lock_password_hash

2. 加锁操作：
   - 备份原内容到 note.encrypted_content
   - 设置 note.is_locked = True
   - 保存用户的全局密码哈希到 note.lock_password_hash（冗余）
   - 隐藏显示内容（文本笔记显示"[已加锁]"）

3. 后续加锁：
   - 直接使用已保存的全局密码
   - 不需要重新输入

解锁流程：
1. 用户点击🔓按钮
2. 弹出密码输入框
3. 验证密码（与 user.note_lock_password_hash 比对）
4. 从 encrypted_content 恢复原内容
5. 设置 is_locked = False
6. 清除加密数据
7. 刷新页面显示原内容
```

### 3. 笔记分享机制 ⭐
```
生成分享：
1. 创建唯一token（URL安全的Base64，32字节）
2. 设置过期时间（当前时间 + 用户选择的时长）
3. 保存到 note_share 表
4. 返回分享URL：http://domain/shared/{token}

访问分享：
1. 接收token参数
2. 查询 note_share 表
3. 验证：
   - token是否存在
   - 是否过期（expires_at < now）
   - 是否已撤销（is_active = False）
4. 增加访问计数（access_count + 1）
5. 渲染 shared_note.html

权限控制：
- 分享链接可以公开访问笔记内容
- 文件下载需验证：
  1. 是文件所有者？允许
  2. 有有效的分享链接？允许
  3. 否则拒绝
- 加锁笔记显示"已加锁"，不显示内容
```

### 4. 画廊懒加载 ⭐
```javascript
// 前端实现（shared_note.html）
let allImages = [];  // 所有图片路径
let loadedCount = 0;  // 已加载数量
const IMAGES_PER_LOAD = 20;  // 每次加载20张

function loadMoreImages() {
    for (let i = loadedCount; i < loadedCount + 20 && i < allImages.length; i++) {
        const img = document.createElement('img');
        img.src = '/uploads/' + allImages[i];
        img.loading = 'lazy';  // 浏览器原生懒加载
        container.appendChild(img);
    }
    loadedCount += 20;

    if (loadedCount >= allImages.length) {
        hideLoadMoreButton();
    }
}
```

### 5. MD5生成机制
```python
def generate_content_md5(content_type, content_data, additional_text=''):
    """为笔记生成唯一MD5"""
    md5_hash = hashlib.md5()

    if content_type == 'text':
        # 文本：内容 + 附加文本
        combined = f"{content_data}{additional_text}"
        md5_hash.update(combined.encode('utf-8'))

    elif content_type in ['file', 'zip', 'image']:
        # 文件：读取文件内容计算
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)

    elif content_type == 'gallery':
        # 画廊：所有图片内容组合
        for img_path in images:
            with open(img_path, 'rb') as f:
                md5_hash.update(f.read())

    # 添加时间戳确保唯一性
    timestamp = datetime.now(timezone.utc).isoformat()
    md5_hash.update(timestamp.encode('utf-8'))

    return md5_hash.hexdigest()
```

---

## 🔑 八、重要配置

### 存储配额
```python
免费用户: 1GB
会员:     100GB
超级会员: 无限制（float('inf')）
```

### 画廊限制
```python
免费用户: 最多20张/次
会员:     最多100张/次
```

### 分享时长选项
```python
5分钟、30分钟、1小时、6小时、24小时、3天、7天、30天
```

### 分片大小
```python
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB
```

### 分享管理显示
```python
最近10条分享记录
```

### 管理员配置
```python
ADMIN_USERNAME = 'sa_root_2024'  # 强用户名
ADMIN_PASSWORD = 'Adm!nP@ss_9X7k2#mQ'  # 强密码
ADMIN_LOGIN_PATH = '/secure_admin_portal_x9k2m'  # 安全入口
ADMIN_VERIFY_CODE = '888888'  # 验证码
```

---

## 🐛 九、已知问题和注意事项

### 已修复
- ✅ 时区问题（统一使用UTC存储，前端显示转换）
- ✅ 解锁后内容显示错误
- ✅ 分享画廊图片无法显示
- ✅ 分享文件无法下载
- ✅ 上传功能失效（重复定义关系、重复函数）
- ✅ 存储空间检查失效（元素不存在）
- ✅ 会员不隐藏广告

### 需注意
- ⚠️ 文件存储在本地，大规模使用需迁移到云存储（OSS）
- ⚠️ SQLite在高并发下性能不足，建议迁移到MySQL/PostgreSQL
- ⚠️ 会员过期需要定时任务处理（目前在访问时检查）
- ⚠️ 文件删除时需同步清理磁盘文件
- ⚠️ 没有备份机制，建议定期备份数据库和uploads目录
- ⚠️ MD5索引在大量数据下需要优化查询

### 安全建议
- 🔒 生产环境必须修改：
  - `SECRET_KEY`
  - 管理员用户名/密码
  - 管理员登录路径
- 🔒 建议启用HTTPS
- 🔒 建议添加登录失败次数限制
- 🔒 建议添加邮箱验证

---

## 🚀 十、快速启动

### 环境要求
```bash
Python 3.8+
Flask 3.x
SQLAlchemy 2.x
Flask-Login
Flask-WTF
cryptography
python-magic
```

### 安装依赖
```bash
pip install flask flask-sqlalchemy flask-login flask-wtf cryptography python-magic
```

### 启动应用
```bash
python Gtest.py
```

### 访问地址
```
普通用户登录: http://127.0.0.1:5000/login
普通用户注册: http://127.0.0.1:5000/register
管理员登录:   http://127.0.0.1:5000/secure_admin_portal_x9k2m
```

### 默认管理员凭据
```
用户名: sa_root_2024
密码:   Adm!nP@ss_9X7k2#mQ
验证码: 888888
```

---

## 📝 十一、给AI的开发指南

### 当你收到这份文档时

**你应该能立即理解**：
1. ✅ 项目是做什么的
2. ✅ 使用了哪些技术
3. ✅ 已经实现了哪些功能
4. ✅ 数据库结构是怎样的
5. ✅ 核心功能是如何实现的
6. ✅ 有哪些已知问题
7. ✅ 代码在哪些文件里

### 开发新功能时的注意事项

#### 修改数据库
```python
# 1. 修改 Gtest.py 中的模型类
class User(db.Model):
    new_field = db.Column(db.String(100))

# 2. 创建迁移脚本
from Gtest import app, db
with app.app_context():
    db.session.execute(text('ALTER TABLE user ADD COLUMN new_field VARCHAR(100)'))
    db.session.commit()

# 3. 运行迁移
python migration_script.py
```

#### 添加新路由
```python
@app.route('/new_feature')
@login_required  # 如果需要登录
def new_feature():
    # 处理逻辑
    return render_template('new_template.html')
```

#### 修改前端
```html
<!-- templates/notes.html -->
<script>
// 新增JavaScript功能
function newFeature() {
    // 使用 csrfToken 发送请求
    fetch('/api/endpoint', {
        method: 'POST',
        headers: { 'X-CSRF-Token': csrfToken },
        body: JSON.stringify(data)
    });
}
</script>
```

#### 存储空间检查
```javascript
// 前端：从顶部导航栏读取
const navbarStorage = document.querySelector('.navbar-storage');
const storageText = navbarStorage.textContent.trim();
// 格式：📦 X.XXGB 或 📦 无限

// 后端：在第一个chunk时检查
if chunk_index == 0:
    check_storage_space(user, total_file_size)
```

---

## 🎯 十二、待开发功能（优先级排序）

### 高优先级
- [ ] 修改锁密码功能（入口已预留）
- [ ] 绑定手机号功能（入口已预留）
- [ ] 会员到期自动提醒（邮件/短信）
- [ ] 数据备份和恢复功能
- [ ] 登录失败次数限制

### 中优先级
- [ ] 笔记标签系统
- [ ] 笔记分类管理
- [ ] 笔记排序（按时间/大小/类型）
- [ ] 全文搜索优化（搜索高亮）
- [ ] 笔记导出（PDF/Word）
- [ ] 笔记版本历史
- [ ] 回收站功能

### 低优先级
- [ ] 主题切换（暗色模式）
- [ ] 笔记统计图表
- [ ] 协作编辑功能
- [ ] 移动端APP
- [ ] 云存储对接
略.....