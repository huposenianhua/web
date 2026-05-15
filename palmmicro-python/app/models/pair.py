"""
配对关系模型

对应 PHP 文件：
  - sql/sqlpair.php      → PairSql 基类
  - sql/sqlstockpair.php → StockPairSql (4个子类)

配对表用于记录不同市场间同一公司的关联股票：
  - abpair:  A股 ↔ B股
  - ahpair:  A股 ↔ H股（港股）
  - adrpair: A股 ↔ ADR（美股存托凭证）
  - fundpair: 基金 ↔ 跟踪标的ETF

数据结构：id 即为 stock_id，xxx_id 存储配对股票的 stock_id。
通过 stock_id 查找配对方，也可以反向查找。

---

表清单：
  1. abpair   — A股 ↔ B股配对
  2. ahpair   — A股 ↔ H股配对
  3. adrpair  — A股 ↔ ADR配对
  4. fundpair — 基金 ↔ ETF配对
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AbPair(Base):
    """A股 ↔ B股配对

    id = A股的 stock_id
    stock_id = B股的 stock_id
    可双向查询：给定A股找B股，或给定B股找A股。
    """
    __tablename__ = "abpair"

    id = Column(Integer, primary_key=True, comment="A股 stock.id")
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False, comment="B股 stock.id")

    def __repr__(self):
        return f"<AbPair(a_stock_id={self.id}, b_stock_id={self.stock_id})>"


class AhPair(Base):
    """A股 ↔ H股配对

    id = A股的 stock_id
    stock_id = H股的 stock_id
    用于计算 AH 溢价，判断跨市场套利机会。
    """
    __tablename__ = "ahpair"

    id = Column(Integer, primary_key=True, comment="A股 stock.id")
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False, comment="H股 stock.id")

    def __repr__(self):
        return f"<AhPair(a_stock_id={self.id}, h_stock_id={self.stock_id})>"


class AdrPair(Base):
    """A股 ↔ ADR配对

    id = H股的 stock_id
    stock_id = ADR的 stock_id
    ADR = American Depositary Receipt，美股上市的存托凭证。
    """
    __tablename__ = "adrpair"

    id = Column(Integer, primary_key=True, comment="H股 stock.id")
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False, comment="ADR stock.id")

    def __repr__(self):
        return f"<AdrPair(h_stock_id={self.id}, adr_stock_id={self.stock_id})>"


class FundPair(Base):
    """基金 ↔ ETF配对

    id = 基金的 stock_id
    stock_id = 跟踪标的ETF的 stock_id
    用于 QDII 基金套利：比较基金净值与标的ETF价格的偏差。
    """
    __tablename__ = "fundpair"

    id = Column(Integer, primary_key=True, comment="基金 stock.id")
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False, comment="标的ETF stock.id")

    def __repr__(self):
        return f"<FundPair(fund_stock_id={self.id}, etf_stock_id={self.stock_id})>"
