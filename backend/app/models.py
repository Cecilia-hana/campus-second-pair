# -*- coding: utf-8 -*-
"""SQLAlchemy ORM 模型 — 5 张核心表"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password = db.Column(db.String(128), nullable=False)  # bcrypt 哈希
    nickname = db.Column(db.String(32), nullable=False)
    avatar_url = db.Column(db.String(512))
    role = db.Column(db.SmallInteger, default=0, nullable=False)    # 0 学生 / 1 管理员
    status = db.Column(db.SmallInteger, default=1, nullable=False)  # 0 禁用 / 1 正常
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_brief(self):
        return {"id": self.id, "username": self.username, "nickname": self.nickname,
                "avatarUrl": self.avatar_url, "role": self.role}


class Item(db.Model):
    __tablename__ = "item"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seller_id = db.Column(db.Integer, nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(1024))
    category_id = db.Column(db.Integer, nullable=False, index=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=1)
    cover_url = db.Column(db.String(512), nullable=False)
    status = db.Column(db.SmallInteger, default=1, nullable=False)  # 0 草稿 1 在售 2 售罄 3 下架
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Order(db.Model):
    __tablename__ = "`order`" if False else "orders"  # SQLite 也支持 order,但避开关键字
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(32), unique=True, nullable=False)
    buyer_id = db.Column(db.Integer, nullable=False, index=True)
    seller_id = db.Column(db.Integer, nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.SmallInteger, nullable=False)  # 0 待付 1 已付 2 已发 3 完成 4 关闭
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    paid_at = db.Column(db.DateTime)


class OrderItem(db.Model):
    __tablename__ = "order_item"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, nullable=False, index=True)
    item_id = db.Column(db.Integer, nullable=False)
    item_title = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class Message(db.Model):
    __tablename__ = "message"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, nullable=False, index=True)    # 0 = 系统消息
    receiver_id = db.Column(db.Integer, nullable=False, index=True)
    content = db.Column(db.String(1024), nullable=False)
    is_read = db.Column(db.SmallInteger, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
