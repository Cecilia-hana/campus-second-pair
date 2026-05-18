# -*- coding: utf-8 -*-
"""消息模块:站内信 REST + Socket.IO 实时推送"""
import threading
from flask import Blueprint, request, g
from sqlalchemy import or_, and_
from .common import ok, BizError, Code, login_required
from .models import db, Message

bp = Blueprint("message", __name__, url_prefix="/api/message")

# userId -> sid 映射;ConcurrentHashMap 等价物
_USER_SIDS: dict[int, set[str]] = {}
_LOCK = threading.RLock()
socketio = None  # 由 app/__init__.py 注入


def bind_socketio(sio):
    global socketio
    socketio = sio


def _bind_user_sid(user_id: int, sid: str):
    with _LOCK:
        _USER_SIDS.setdefault(user_id, set()).add(sid)


def _unbind_sid(sid: str):
    with _LOCK:
        for uid, sids in list(_USER_SIDS.items()):
            sids.discard(sid)
            if not sids:
                _USER_SIDS.pop(uid, None)


def _push(user_id: int, payload: dict):
    if not socketio:
        return
    with _LOCK:
        sids = list(_USER_SIDS.get(user_id, set()))
    for sid in sids:
        try:
            socketio.emit("message", payload, to=sid)
        except Exception:
            pass


def send_message(sender_id: int, receiver_id: int, content: str) -> int:
    if not content or not content.strip():
        raise BizError(Code.PARAM, "消息内容不能为空")
    if len(content) > 1024:
        raise BizError(Code.PARAM, "消息过长(<=1024)")
    m = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(m)
    db.session.commit()
    _push(receiver_id, {
        "type": "message", "id": m.id,
        "senderId": sender_id, "content": content,
        "createdAt": m.created_at.isoformat(timespec="seconds"),
    })
    return m.id


# ---------------- REST ----------------
@bp.post("/send")
@login_required
def send():
    data = request.get_json(silent=True) or {}
    rid = int(data.get("receiverId") or 0)
    if rid <= 0:
        raise BizError(Code.PARAM, "receiverId 非法")
    return ok(send_message(g.user_id, rid, data.get("content") or ""))


@bp.get("/conversation/<int:other_id>")
@login_required
def conversation(other_id):
    me = g.user_id
    rows = Message.query.filter(or_(
        and_(Message.sender_id == me, Message.receiver_id == other_id),
        and_(Message.sender_id == other_id, Message.receiver_id == me),
    )).order_by(Message.created_at.asc()).all()
    # 进入会话标记已读
    Message.query.filter_by(receiver_id=me, sender_id=other_id, is_read=0)\
        .update({Message.is_read: 1})
    db.session.commit()
    return ok([{
        "id": m.id, "senderId": m.sender_id, "receiverId": m.receiver_id,
        "content": m.content, "isRead": m.is_read,
        "createdAt": m.created_at.isoformat(timespec="seconds"),
    } for m in rows])


@bp.get("/inbox")
@login_required
def inbox():
    rows = Message.query.filter_by(receiver_id=g.user_id)\
        .order_by(Message.created_at.desc()).limit(100).all()
    return ok([{
        "id": m.id, "senderId": m.sender_id, "content": m.content,
        "isRead": m.is_read,
        "createdAt": m.created_at.isoformat(timespec="seconds"),
    } for m in rows])


@bp.get("/unread")
@login_required
def unread():
    cnt = Message.query.filter_by(receiver_id=g.user_id, is_read=0).count()
    return ok({"count": cnt})


# ---------------- Socket.IO 事件 ----------------
def register_socketio_events(sio):
    bind_socketio(sio)

    @sio.on("connect")
    def _on_connect():
        # 客户端连接后发送 register 事件,带上 userId
        pass

    @sio.on("register")
    def _on_register(data):
        try:
            uid = int((data or {}).get("userId") or 0)
            if uid > 0:
                _bind_user_sid(uid, request.sid)
        except Exception:
            pass

    @sio.on("disconnect")
    def _on_disconnect():
        _unbind_sid(request.sid)
