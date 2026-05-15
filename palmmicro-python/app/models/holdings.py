"""
ETF持仓数据模型

对应 PHP 文件：
  - sql/sqlholdings.php → HoldingsSql extends KeySql

---

表清单：
  1. holdings — ETF基金的持仓明细（成分股 + 持仓比例）
"""

from sqlalchemy import Column, Integer, Float, UniqueConstraint, Index, ForeignKey
from app.database import Base


class Holdings(Base):
    """ETF基金持仓明细

    存储每只ETF基金的成分股及对应持仓比例。
    stock_id:   ETF基金的 stock.id
    holding_id: 成分股的 stock.id
    ratio:      持仓比例（0.0~1.0）

    例如：159915（创业板ETF）的持仓可能包含：
      - 300750 宁德时代 ratio=0.08
      - 300059 东方财富 ratio=0.05
      - ...

    用于 QDII 基金净值估算：根据标的ETF的持仓比例，
    结合各成分股实时价格计算估算净值。
    """
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False, comment="ETF基金的 stock.id")
    holding_id = Column(Integer, ForeignKey('stock.id'), nullable=False, comment="成分股的 stock.id")
    ratio = Column(Float, nullable=False, comment="持仓比例（0.0~1.0）")

    __table_args__ = (
        UniqueConstraint("stock_id", "holding_id", name="uq_holdings_stock_holding"),
        Index("idx_holdings_ratio", "ratio"),
    )

    def __repr__(self):
        return f"<Holdings(id={self.id}, fund_stock_id={self.stock_id}, holding_stock_id={self.holding_id}, ratio={self.ratio})>"
