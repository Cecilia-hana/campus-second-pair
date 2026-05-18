# -*- coding: utf-8 -*-
"""订单模块:下单 / 状态机 / 我买/我卖

防超卖策略(无 Redis 版本):
1) 进程内 RLock,按 item_id 分桶,序列化同商品并发请求。
2) DB 层 UPDATE item SET stock=stock-? WHERE id=? AND stock>=? 行级原子校验,
   affected_rows == 0 时回滚整笔订单,保证不超卖。
"""
import threading
from datetime import datetime
from collections import defaultdict
from decimal import Decimal
from random import randint
from flask import Blueprint, request, g
from sqlalchemy import text
from .common import ok, BizError, Code, login_required
from .models import db, Order, OrderItem, Item
from . import message as msg_mod  # 用于发送系统通知

bp = Blueprint("order", __name__, url_prefix="/api/order")

# 进程内细粒度锁:同 item 串行,跨 item 并发
_LOCKS = defaultdict(threading.RLock)
_LOCKS_GUARD = threading.Lock()
STATUS_TEXT = ["待支付", "已支付", "已发货", "已完成", "已关闭"]


def _lock_for(item_id: int):
    with _LOCKS_GUARD:
        return _LOCKS[item_id]


def _gen_order_no():
    return f"{int(datetime.utcnow().timestamp() * 1000)}{randint(1000, 9999)}"


def _decrease_stock(item_id: int, qty: int) -> int:
    """返回受影响行数(0 表示库存不足)"""
    res = db.session.execute(
        text("UPDATE item SET stock = stock - :q WHERE id = :id AND stock >= :q"),
        {"q": qty, "id": item_id},
    )
    return res.rowcount or 0


@bp.post("/create")
@login_required
def create():
    data = request.get_json(silent=True) or {}
    item_id = int(data.get("itemId") or 0)
    qty = int(data.get("quantity") or 0)
    if item_id <= 0 or qty <= 0:
        raise BizError(Code.PARAM, "参数错误")

    it = Item.query.get(item_id)
    if not it:
        raise BizError(Code.ITEM_NOT_FOUND, "商品不存在")
    if it.status != 1:
        raise BizError(Code.ITEM_OFFLINE, "商品已下架")
    if it.seller_id == g.user_id:
        raise BizError(Code.PARAM, "不能购买自己的商品")

    # 关键:同商品串行
    with _lock_for(item_id):
        affected = _decrease_stock(item_id, qty)
        if affected == 0:
            db.session.rollback()
            raise BizError(Code.STOCK_NOT_ENOUGH, "库存不足")

        # 重新查一次,看看是否售罄
        db.session.refresh(it)
        if it.stock == 0:
            it.status = 2

        order = Order(
            order_no=_gen_order_no(),
            buyer_id=g.user_id,
            seller_id=it.seller_id,
            total_amount=Decimal(it.price) * qty,
            status=0,
        )
        db.session.add(order)
        db.session.flush()  # 拿到 order.id

        oi = OrderItem(order_id=order.id, item_id=it.id, item_title=it.title,
                       price=it.price, quantity=qty)
        db.session.add(oi)
        db.session.commit()

    # 通知卖家(失败不影响下单)
    try:
        msg_mod.send_message(0, it.seller_id,
                             f"[系统] 您有一笔新订单 {order.order_no},买家 uid={g.user_id}")
    except Exception:
        pass

    return ok({"orderId": order.id, "orderNo": order.order_no,
               "totalAmount": str(order.total_amount)})


def _change_status(order_id: int, expect: int, target: int, owner: str):
    o = Order.query.get(order_id)
    if not o:
        raise BizError(Code.ORDER_NOT_FOUND, "订单不存在")
    if owner == "buyer" and o.buyer_id != g.user_id:
        raise BizError(Code.FORBID, "无权操作")
    if owner == "seller" and o.seller_id != g.user_id:
        raise BizError(Code.FORBID, "无权操作")
    if o.status != expect:
        raise BizError(Code.ORDER_STATUS_ERROR, f"订单非 {STATUS_TEXT[expect]} 状态")
    o.status = target
    if target == 1:
        o.paid_at = datetime.utcnow()
    db.session.commit()
    return o


@bp.post("/pay/<int:oid>")
@login_required
def pay(oid):
    _change_status(oid, 0, 1, "buyer")
    return ok()


@bp.post("/ship/<int:oid>")
@login_required
def ship(oid):
    _change_status(oid, 1, 2, "seller")
    return ok()


@bp.post("/finish/<int:oid>")
@login_required
def finish(oid):
    _change_status(oid, 2, 3, "buyer")
    return ok()


def _serialize_orders(orders):
    if not orders:
        return []
    ids = [o.id for o in orders]
    items = OrderItem.query.filter(OrderItem.order_id.in_(ids)).all()
    grp = defaultdict(list)
    for oi in items:
        grp[oi.order_id].append({
            "id": oi.id, "itemId": oi.item_id, "itemTitle": oi.item_title,
            "price": str(oi.price), "quantity": oi.quantity,
        })
    return [{
        "id": o.id, "orderNo": o.order_no,
        "buyerId": o.buyer_id, "sellerId": o.seller_id,
        "totalAmount": str(o.total_amount),
        "status": o.status, "statusText": STATUS_TEXT[o.status],
        "createdAt": o.created_at.isoformat(timespec="seconds"),
        "items": grp.get(o.id, []),
    } for o in orders]


@bp.get("/my/buy")
@login_required
def my_buy():
    rows = Order.query.filter_by(buyer_id=g.user_id).order_by(Order.created_at.desc()).all()
    return ok(_serialize_orders(rows))


@bp.get("/my/sell")
@login_required
def my_sell():
    rows = Order.query.filter_by(seller_id=g.user_id).order_by(Order.created_at.desc()).all()
    return ok(_serialize_orders(rows))
