# -*- coding: utf-8 -*-
"""
集成测试:覆盖核心 5 条主路径(由"领航员"编写,"驾驶员"跑通)
执行:pip install pytest && pytest -v
"""
import os, sys, json, tempfile, importlib

# 在 app 加载前注入临时 sqlite,避免污染默认库
TMP_DB = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB}"
os.environ["SECRET_KEY"] = "test-secret"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app
from app.models import db


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.session.remove()
        db.drop_all()
    if os.path.exists(TMP_DB):
        try: os.remove(TMP_DB)
        except OSError: pass


def _post(client, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    return client.post(path, data=json.dumps(body or {}), headers=headers)


def _get(client, path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.get(path, headers=headers)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["code"] == 0


def test_register_and_login(client):
    # 注册新用户
    r = _post(client, "/api/user/register",
              {"username": "alice01", "password": "abcdef", "nickname": "Alice"})
    body = r.get_json()
    assert body["code"] == 0
    assert isinstance(body["data"], int)

    # 重复注册
    r = _post(client, "/api/user/register",
              {"username": "alice01", "password": "abcdef"})
    assert r.get_json()["code"] == 2001

    # 错误密码
    r = _post(client, "/api/user/login",
              {"username": "alice01", "password": "wrong1"})
    assert r.get_json()["code"] == 2003

    # 正确登录
    r = _post(client, "/api/user/login",
              {"username": "alice01", "password": "abcdef"})
    body = r.get_json()
    assert body["code"] == 0 and body["data"]["token"]


def test_browse_items_without_login(client):
    """未登录可浏览商品(种子数据)"""
    r = _post(client, "/api/item/list", {"page": 1, "size": 12})
    body = r.get_json()
    assert body["code"] == 0
    assert body["data"]["total"] >= 4


def test_buy_flow_with_anti_oversell(client):
    """完整下单链路 + 防超卖"""
    # 用 stu001 登录买家
    r = _post(client, "/api/user/login", {"username": "stu001", "password": "123456"})
    buyer_token = r.get_json()["data"]["token"]

    # 找一件库存=1 的商品
    items = _post(client, "/api/item/list", {"page": 1, "size": 50}).get_json()["data"]["records"]
    target = next(i for i in items if i["stock"] == 1)

    # 第一次下单成功
    r = _post(client, "/api/order/create",
              {"itemId": target["id"], "quantity": 1}, token=buyer_token)
    assert r.get_json()["code"] == 0

    # 第二次同商品下单应"商品已下架"或"库存不足"
    r2 = _post(client, "/api/order/create",
               {"itemId": target["id"], "quantity": 1}, token=buyer_token)
    assert r2.get_json()["code"] in (3002, 4002)

    # 我买的订单 >= 1
    my = _get(client, "/api/order/my/buy", token=buyer_token).get_json()
    assert my["code"] == 0 and len(my["data"]) >= 1


def test_message_send_and_inbox(client):
    """私信发送 + 收件箱"""
    r = _post(client, "/api/user/login", {"username": "stu001", "password": "123456"})
    a = r.get_json()["data"]["token"]
    r = _post(client, "/api/user/login", {"username": "stu002", "password": "123456"})
    b_uid = r.get_json()["data"]["userId"]
    b_tok = r.get_json()["data"]["token"]

    r = _post(client, "/api/message/send",
              {"receiverId": b_uid, "content": "在吗,书还在卖吗?"}, token=a)
    assert r.get_json()["code"] == 0

    inbox = _get(client, "/api/message/inbox", token=b_tok).get_json()
    assert inbox["code"] == 0
    assert any("还在卖吗" in m["content"] for m in inbox["data"])


def test_unauth_returns_1002(client):
    """未带 token 调用受保护接口"""
    r = _get(client, "/api/user/profile")
    assert r.get_json()["code"] == 1002



def test_item_list_filters_offline_items(client):
    """商品列表只展示在售商品，已下架商品不应出现"""
    r = _post(client, "/api/user/login",
              {"username": "stu002", "password": "123456"})
    token = r.get_json()["data"]["token"]

    r = _post(client, "/api/item/list", {"page": 1, "size": 50})
    items = r.get_json()["data"]["records"]
    target = items[0]

    _post(client, f"/api/item/offline/{target['id']}", token=token)

    r = _post(client, "/api/item/list", {"page": 1, "size": 50})
    after_ids = {item["id"] for item in r.get_json()["data"]["records"]}

    assert target["id"] not in after_ids, \
        f"BUG: 已下架的商品 id={target['id']} 仍然出现在列表中！"


def test_cannot_buy_own_item(client):
    """卖家不能购买自己的商品"""
    r = _post(client, "/api/user/login",
              {"username": "stu002", "password": "123456"})
    token = r.get_json()["data"]["token"]
    user_id = r.get_json()["data"]["userId"]

    # 找到 stu002 自己的商品（可能被前面测试消耗了）
    r = _post(client, "/api/item/list", {"page": 1, "size": 50})
    own_items = [i for i in r.get_json()["data"]["records"]
                 if i["sellerId"] == user_id]

    if not own_items:
        # 自己发布一件新的
        _post(client, "/api/item/create", {
            "title": "测试自有商品", "price": 10, "stock": 1,
            "categoryId": 9, "coverUrl": "http://localhost:5000/files/test.jpg"
        }, token=token)
        r = _post(client, "/api/item/list", {"page": 1, "size": 50})
        own_items = [i for i in r.get_json()["data"]["records"]
                     if i["sellerId"] == user_id]

    own_item = own_items[0]
    r = _post(client, "/api/order/create",
              {"itemId": own_item["id"], "quantity": 1}, token=token)
    assert r.get_json()["code"] == 1001  # PARAM: 不能购买自己的商品