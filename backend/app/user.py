# -*- coding: utf-8 -*-
"""用户模块:注册 / 登录 / profile"""
import jwt, bcrypt, datetime
from flask import Blueprint, request, current_app, g
from .common import ok, BizError, Code, login_required
from .models import db, User

bp = Blueprint("user", __name__, url_prefix="/api/user")


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _verify(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def _gen_token(u: User) -> str:
    payload = {
        "sub": str(u.id),
        "username": u.username,
        "role": u.role,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=current_app.config["JWT_EXPIRE_MINUTES"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    nickname = (data.get("nickname") or "").strip() or username
    if len(username) < 3:
        raise BizError(Code.PARAM, "用户名至少 3 位")
    if len(password) < 6:
        raise BizError(Code.PARAM, "密码至少 6 位")
    if User.query.filter_by(username=username).first():
        raise BizError(Code.USER_EXISTS, "用户名已存在")
    u = User(username=username, password=_hash(password), nickname=nickname)
    db.session.add(u)
    db.session.commit()
    return ok(u.id)


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    u = User.query.filter_by(username=(data.get("username") or "").strip()).first()
    if not u:
        raise BizError(Code.USER_NOT_FOUND, "用户不存在")
    if u.status == 0:
        raise BizError(Code.USER_DISABLED, "用户已被禁用")
    if not _verify(data.get("password") or "", u.password):
        raise BizError(Code.PASSWORD_WRONG, "密码错误")
    return ok({
        "token": _gen_token(u),
        "userId": u.id,
        "username": u.username,
        "nickname": u.nickname,
        "role": u.role,
    })


@bp.get("/profile")
@login_required
def profile():
    u = User.query.get(g.user_id)
    if not u:
        raise BizError(Code.USER_NOT_FOUND, "用户不存在")
    return ok(u.to_brief())


def get_nickname_map(uids):
    """供 item / order 模块批量查昵称用"""
    if not uids:
        return {}
    rows = User.query.filter(User.id.in_(list(uids))).all()
    return {r.id: r.nickname for r in rows}
