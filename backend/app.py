# -*- coding: utf-8 -*-
"""
启动入口 — `python app.py`
开发模式默认监听 0.0.0.0:5000,使用 threading 模式(零额外依赖,
SocketIO 走 simple-websocket / 长轮询,HTTP 与 WebSocket 共用同端口)。
"""
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from app import create_app
import app as app_pkg

flask_app = create_app()
socketio = app_pkg.socketio

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    print(f"\n  ✅ Campus-Second backend running at http://{host}:{port}")
    print(f"     · 测试账号: stu001/123456 (买家), stu002/123456 (卖家), admin/123456")
    print(f"     · API 文档见 README.md\n")
    socketio.run(flask_app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
