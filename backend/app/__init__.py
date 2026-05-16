# -*- coding: utf-8 -*-
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from .config import Config
from .common import register_error_handlers
from .models import db
from . import user as user_mod
from . import item as item_mod
from . import order as order_mod
from . import message as msg_mod

socketio: SocketIO = None  # type: ignore[assignment]


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=True)

    # 蓝图
    app.register_blueprint(user_mod.bp)
    app.register_blueprint(item_mod.bp)
    app.register_blueprint(order_mod.bp)
    app.register_blueprint(msg_mod.bp)
    app.register_blueprint(item_mod.files_bp)

    # 全局异常
    register_error_handlers(app)

    # 健康检查
    @app.get("/api/health")
    def _health():
        return {"code": 0, "msg": "ok", "data": {"service": "campus-second"}}

    # SocketIO
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*",
                       async_mode="threading", path="/ws/socket.io")
    msg_mod.register_socketio_events(socketio)

    # 自动建表 + 种子数据
    with app.app_context():
        db.create_all()
        _seed_if_empty()

    return app


def _seed_if_empty():
    """首次启动写入 4 个测试用户 + 4 件商品(密码均为 123456)"""
    from .models import User, Item
    from datetime import datetime
    import bcrypt
    if User.query.first():
        return
    pw = bcrypt.hashpw(b"123456", bcrypt.gensalt()).decode()
    users = [
        User(username="admin",  password=pw, nickname="管理员",   role=1),
        User(username="stu001", password=pw, nickname="小买买"),
        User(username="stu002", password=pw, nickname="老卖头"),
        User(username="stu003", password=pw, nickname="学姐二手"),
    ]
    db.session.add_all(users)
    db.session.flush()

    base = "http://localhost:5000/files"
    items = [
        Item(seller_id=users[2].id, title="《算法导论》第三版 九成新",
             description="本人已上岸,无划线无破损,可面交。",
             category_id=1, price=60, stock=1,
             cover_url=f"{base}/sample-book.jpg", status=1),
        Item(seller_id=users[2].id, title="小米台灯 1S 充电款",
             description="宿舍闲置,带原盒,正常使用。",
             category_id=3, price=80, stock=2,
             cover_url=f"{base}/sample-lamp.jpg", status=1),
        Item(seller_id=users[3].id, title="罗技 G304 无线鼠标",
             description="电池在用,无故障,送鼠标垫一个。",
             category_id=2, price=120, stock=1,
             cover_url=f"{base}/sample-mouse.jpg", status=1),
        Item(seller_id=users[3].id, title="迪卡侬慢跑鞋 42 码",
             description="只穿过两次,室内基本全新。",
             category_id=5, price=99, stock=1,
             cover_url=f"{base}/sample-shoes.jpg", status=1),
    ]
    db.session.add_all(items)
    db.session.commit()
