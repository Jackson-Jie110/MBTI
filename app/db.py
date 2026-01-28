from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


def _default_sqlite_url() -> str:
    return "sqlite:///./mbti.db"


# 获取环境变量，优先读取 MBTI_DATABASE_URL，其次是 DATABASE_URL，默认回退到本地 SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("MBTI_DATABASE_URL") or os.getenv("DATABASE_URL") or _default_sqlite_url()

# 修复 Vercel/Render 等平台 Postgres URL 以 "postgres://" 开头导致 SQLAlchemy 报错的问题
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 仅针对 SQLite 使用 check_same_thread 参数
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
