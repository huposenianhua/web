"""
Palmmicro Python — 数据库连接配置
从 .env 读取数据库密码，创建 SQLAlchemy engine 和 session
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 加载 .env 文件
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "n5gl0n39mnyn183l_camman")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    echo=False,       # 生产环境关闭SQL日志，调试时改为True
    pool_pre_ping=True,  # 自动检测断开连接
    pool_recycle=3600,   # 每小时回收连接
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


def get_db():
    """获取数据库会话（FastAPI 依赖注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表（首次运行时调用）"""
    Base.metadata.create_all(bind=engine)
