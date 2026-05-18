# -*- coding: utf-8 -*-
"""商品模块:CRUD / 列表 / 详情 / 上传图片"""
import os, uuid
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, current_app, g, send_from_directory
from sqlalchemy import or_
from .common import ok, BizError, Code, login_required
from .models import db, Item
from .user import get_nickname_map

bp = Blueprint("item", __name__, url_prefix="/api/item")

CATEGORIES = {
    1: "教材教辅",
    2: "数码电子",
    3: "生活用品",
    4: "服饰鞋包",
    5: "运动户外",
    9: "其他",
}


def _to_brief(it: Item, nick_map=None):
    nick_map = nick_map or {}
    return {
        "id": it.id, "title": it.title, "price": str(it.price),
        "stock": it.stock, "coverUrl": it.cover_url, "status": it.status,
        "sellerId": it.seller_id, "sellerNickname": nick_map.get(it.seller_id),
        "createdAt": it.created_at.isoformat(timespec="seconds"),
    }


def _validate(data):
    title = (data.get("title") or "").strip()
    if not title:
        raise BizError(Code.PARAM, "标题不能为空")
    try:
        price = Decimal(str(data.get("price")))
    except (InvalidOperation, TypeError):
        raise BizError(Code.PARAM, "价格非法")
    if price < 0:
        raise BizError(Code.PARAM, "价格非法")
    stock = int(data.get("stock") or 0)
    if stock < 0:
        raise BizError(Code.PARAM, "库存非法")
    cat = int(data.get("categoryId") or 0)
    if cat not in CATEGORIES:
        raise BizError(Code.PARAM, "分类不存在")
    cover = (data.get("coverUrl") or "").strip()
    if not cover:
        raise BizError(Code.PARAM, "请上传封面图")
    return title, price, stock, cat, cover


@bp.post("/create")
@login_required
def create():
    data = request.get_json(silent=True) or {}
    title, price, stock, cat, cover = _validate(data)
    it = Item(seller_id=g.user_id, title=title, description=(data.get("description") or "").strip(),
              category_id=cat, price=price, stock=stock, cover_url=cover, status=1)
    db.session.add(it)
    db.session.commit()
    return ok(it.id)


@bp.put("/update/<int:item_id>")
@login_required
def update(item_id):
    it = Item.query.get(item_id) or _not_found()
    if it.seller_id != g.user_id:
        raise BizError(Code.FORBID, "只能修改自己的商品")
    data = request.get_json(silent=True) or {}
    title, price, stock, cat, cover = _validate(data)
    it.title, it.price, it.stock = title, price, stock
    it.category_id, it.cover_url = cat, cover
    it.description = (data.get("description") or "").strip()
    if "status" in data:
        it.status = int(data["status"])
    db.session.commit()
    return ok()


@bp.post("/offline/<int:item_id>")
@login_required
def offline(item_id):
    it = Item.query.get(item_id) or _not_found()
    if it.seller_id != g.user_id:
        raise BizError(Code.FORBID, "只能下架自己的商品")
    it.status = 3
    db.session.commit()
    return ok()


@bp.post("/list")
def list_items():
    data = request.get_json(silent=True) or {}
    page = max(int(data.get("page") or 1), 1)
    size = min(max(int(data.get("size") or 12), 1), 50)
    q = Item.query
    if data.get("categoryId"):
        q = q.filter(Item.category_id == int(data["categoryId"]))
    kw = (data.get("keyword") or "").strip()
    if kw:
        like = f"%{kw}%"
        q = q.filter(or_(Item.title.like(like), Item.description.like(like)))
    total = q.count()
    rows = q.order_by(Item.created_at.desc()).offset((page - 1) * size).limit(size).all()
    nick = get_nickname_map({r.seller_id for r in rows})
    return ok({"total": total, "records": [_to_brief(r, nick) for r in rows]})


@bp.get("/detail/<int:item_id>")
def detail(item_id):
    it = Item.query.get(item_id) or _not_found()
    nick = get_nickname_map({it.seller_id})
    body = _to_brief(it, nick)
    body["description"] = it.description
    body["categoryId"] = it.category_id
    body["categoryName"] = CATEGORIES.get(it.category_id, "其他")
    return ok(body)


@bp.get("/categories")
def categories():
    return ok(CATEGORIES)


@bp.post("/upload")
@login_required
def upload():
    if "file" not in request.files:
        raise BizError(Code.PARAM, "未选择文件")
    f = request.files["file"]
    if not f.filename:
        raise BizError(Code.PARAM, "文件为空")
    f.stream.seek(0, os.SEEK_END)
    size = f.stream.tell()
    f.stream.seek(0)
    if size > current_app.config["MAX_UPLOAD_SIZE"]:
        raise BizError(Code.PARAM, "图片不得超过 5MB")
    mime = (f.mimetype or "").lower()
    if mime not in current_app.config["ALLOWED_MIME"]:
        raise BizError(Code.PARAM, "仅支持 jpeg/png/webp")
    ext = os.path.splitext(f.filename)[1] or ".jpg"
    name = uuid.uuid4().hex + ext
    path = os.path.join(current_app.config["UPLOAD_DIR"], name)
    f.save(path)
    return ok({"url": f"{current_app.config['UPLOAD_BASE_URL']}/{name}"})


# 静态文件下载
files_bp = Blueprint("files", __name__)


@files_bp.get("/files/<path:name>")
def serve_file(name):
    return send_from_directory(current_app.config["UPLOAD_DIR"], name)


def _not_found():
    raise BizError(Code.ITEM_NOT_FOUND, "商品不存在")
