# -*- coding: utf-8 -*-
"""统一响应 / 异常 / 业务码"""
from functools import wraps
from flask import jsonify, request, g, current_app
import jwt
import logging

log = logging.getLogger(__name__)


# -------- 业务码:0 成功 / 1xxx 通用 / 2xxx 用户 / 3xxx 商品 / 4xxx 订单 / 5xxx 消息 --------
class Code:
    OK = 0
    PARAM = 1001
    UNAUTH = 1002
    FORBID = 1003
    SERVER = 1500

    USER_EXISTS = 2001
    USER_NOT_FOUND = 2002
    PASSWORD_WRONG = 2003
    USER_DISABLED = 2004

    ITEM_NOT_FOUND = 3001
    ITEM_OFFLINE = 3002

    ORDER_NOT_FOUND = 4001
    STOCK_NOT_ENOUGH = 4002
    ORDER_STATUS_ERROR = 4003


class BizError(Exception):
    def __init__(self, code: int, msg: str):
        super().__init__(msg)
        self.code = code
        self.msg = msg


def ok(data=None):
    return jsonify({"code": 0, "msg": "ok", "data": data})


def fail(code: int, msg: str):
    return jsonify({"code": code, "msg": msg, "data": None})


# ----------------- JWT 鉴权装饰器 -----------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise BizError(Code.UNAUTH, "未登录或登录过期")
        token = auth[7:]
        try:
            payload = jwt.decode(
                token, current_app.config["JWT_SECRET"], algorithms=["HS256"]
            )
            g.user_id = int(payload["sub"])
            g.username = payload.get("username")
            g.role = payload.get("role", 0)
        except jwt.ExpiredSignatureError:
            raise BizError(Code.UNAUTH, "登录已过期")
        except Exception:
            raise BizError(Code.UNAUTH, "token 无效")
        return fn(*args, **kwargs)

    return wrapper


# ----------------- 全局异常处理 -----------------
def register_error_handlers(app):
    @app.errorhandler(BizError)
    def _biz(e: BizError):
        log.warning("biz error: code=%s msg=%s", e.code, e.msg)
        return fail(e.code, e.msg)

    @app.errorhandler(404)
    def _404(_):
        return fail(404, "接口不存在"), 404

    @app.errorhandler(Exception)
    def _all(e: Exception):
        log.exception("unhandled exception")
        return fail(Code.SERVER, f"服务器内部错误: {e}"), 500
