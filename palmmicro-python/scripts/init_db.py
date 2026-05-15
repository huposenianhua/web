"""
数据库初始化脚本
创建数据库和所有表
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.models import stock, market_data, pair, trading, holdings


def create_tables():
    """创建所有表"""
    print("正在创建数据库表...")
    
    # 导入所有模型以确保它们被注册
    # Base.metadata.create_all(bind=engine) 会自动创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("数据库表创建完成！")


def init_sample_data():
    """初始化示例数据（可选）"""
    print("正在初始化示例数据...")
    
    db = SessionLocal()
    try:
        # 这里可以添加示例数据
        # 例如插入一些测试股票数据
        pass
    finally:
        db.close()
    
    print("示例数据初始化完成！")


if __name__ == "__main__":
    print("=" * 50)
    print("Palmmicro 数据库初始化")
    print("=" * 50)
    
    create_tables()
    init_sample_data()
    
    print("\n🎉 数据库初始化完成！")
