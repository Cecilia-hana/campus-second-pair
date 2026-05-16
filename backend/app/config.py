# -*- coding: utf-8 -*-
"""校园二手物品交易系统 · 全局配置"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "campus-second-dev-secret-change-me")
    # 默认 SQLite,零配置;若想用 MySQL 就改 DATABASE_URL 环境变量
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'campus_second.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET = SECRET_KEY
    JWT_EXPIRE_MINUTES = 60 * 12

    # 上传
    UPLOAD_DIR = str(UPLOAD_DIR)
    UPLOAD_BASE_URL = os.getenv("UPLOAD_BASE_URL", "http://localhost:5000/files")
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024
    ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
