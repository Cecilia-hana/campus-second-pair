# 校园二手物品交易系统 - 系统部署说明

## 一、技术栈声明
| 层 | 选型 |
|---|---|
| 后端框架 | Flask 3 + Flask-SQLAlchemy |
| 数据库 | SQLite(默认,文件 `campus_second.db` 自动生成) |
| 实时通信 | Flask-SocketIO + eventlet(替代原 STOMP/WebSocket) |
| 鉴权 | PyJWT(HS256)+ bcrypt |
| 前端 | Vue 3 + Vite + Element Plus + Pinia + socket.io-client |
| 测试 | pytest |

---

## 二、本地部署步骤

### 1. 后端启动 (零外部依赖)
无需安装 MySQL、Redis 或任何中间件,SQLite 文件首次启动自动生成,种子数据(4 个测试账号 + 4 件示例商品)自动写入。
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py  # 默认监听 0.0.0.0:5000
```

### 2. 前端启动
```bash
cd frontend
npm install
npm run dev    # 访问 http://localhost:5173,生产构建使用 npm run build
```
*(注：Vite 已把 /api、/files、/ws 三类请求代理到 http://localhost:5000)*

### 3. 测试账号
| 用户名 | 密码 | 角色 |
|---|---|---|
| admin | 123456 | 管理员 |
| stu001 | 123456 | 普通用户(默认买家) |
| stu002 | 123456 | 普通用户(默认卖家) |
| stu003 | 123456 | 普通用户 |
### 4. pytest 集成测试
```bash
cd backend && pip install pytest && pytest -v
```
覆盖 6 条主路径:健康检查、注册+登录、未登录浏览、完整下单链路 + 防超卖、私信发送 + 收件箱、未授权 1002。本地运行实测 6 / 6 通过。

### 5. 生产部署 (可选)
项目结构极简,生产环境推荐使用 gunicorn(SocketIO 需要单 worker)。
```bash
pip install gunicorn
gunicorn -w 1 -b 0.0.0.0:5000 "app:flask_app"
```
如需切换数据库,设置环境变量即可,无需改代码:
```bash
export DATABASE_URL=postgresql+psycopg2://user:pwd@host:5432/campus_second
```

### 6. 项目目录结构
```text
campus-second/
├─ backend/                       # Flask 后端
│  ├─ app.py                      # 启动入口
│  ├─ requirements.txt
│  ├─ app/
│  │  ├─ __init__.py              # create_app() + 自动建表/种子
│  │  ├─ config.py
│  │  ├─ common.py                # 统一响应 / @login_required
│  │  ├─ models.py                # 5 个 SQLAlchemy 模型
│  │  ├─ user.py / item.py / order.py / message.py  # 4 个 Blueprint
│  └─ tests/test_api.py           # 6 条主路径集成测试
├─ frontend/                      # Vue3 前端
│  ├─ src/views/{user,item,order,message}
│  └─ src/utils/{request.js,ws.js}
└─ README.md
```

### 7. 常见问题
* **端口冲突**: 若本机已占用 5000/5173,后端可通过环境变量 PORT 修改(`PORT=5050 python app.py`),前端在 `vite.config.js` 中改 `server.port`。
* **SQLite 文件位置**: 默认在 `backend/campus_second.db`,若需要重置只需删除该文件,下次启动会重新建表 + 写种子数据。
* **上传图片 413**: 后端 `MAX_UPLOAD_SIZE` 默认 5 MB,可在 `app/config.py` 中调整;若使用 Nginx 反代,需同步设置 `client_max_body_size`。
* **WebSocket 连不上**: 检查 Vite 代理 `ws: true` 是否生效,生产环境 Nginx `location /ws/` 需要加 `proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";`
