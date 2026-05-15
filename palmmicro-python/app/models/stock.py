"""
股票基础信息模型

对应 PHP 数据库表 stock
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Stock(Base):
    """股票/基金基本信息表"""
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(64), nullable=False, unique=True)
    name = Column(String(256))
    market = Column(String(32))
    type = Column(String(32))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<Stock(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"
