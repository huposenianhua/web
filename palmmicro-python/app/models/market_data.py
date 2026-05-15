"""
市场数据模型 — 时间序列数据

对应 PHP 数据库表:
  dailystock, ema50, ema200, netvalue, calibration, fundest 等
"""

from sqlalchemy import (
    Column, Integer, BigInteger, Float, String, Date, Time, DateTime,
    DECIMAL, UniqueConstraint, Index, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class StockHistory(Base):
    """股票历史价格"""
    __tablename__ = "dailystock"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)

    stock = relationship("Stock")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_dailystock_stock_date"),
        Index("idx_dailystock_stock_date", "stock_id", "date"),
    )

    def __repr__(self):
        return f"<StockHistory(id={self.id}, stock_id={self.stock_id}, date={self.date}, close={self.close})>"


class StockEma50(Base):
    """50日指数移动平均线"""
    __tablename__ = "ema50"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_ema50_stock_date"),
    )


class StockEma200(Base):
    """200日指数移动平均线"""
    __tablename__ = "ema200"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_ema200_stock_date"),
    )


class NetValueHistory(Base):
    """基金净值历史"""
    __tablename__ = "netvalue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_netvalue_stock_date"),
    )


class CalibrationHistory(Base):
    """QDII基金校准历史
    
    PHP对应: calibrationhistory 表 (CalibrationSql extends DailyTimeSql)
    字段: stock_id, date, close(校准值), time(校准时间), num(当日校准次数)
    """
    __tablename__ = "calibrationhistory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)
    time = Column(String(10))
    num = Column(Integer)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_calhist_stock_date"),
    )

    def __repr__(self):
        return f"<CalibrationHistory(id={self.id}, stock_id={self.stock_id}, date={self.date}, close={self.close})>"


class FundEst(Base):
    """基金实时估算净值"""
    __tablename__ = "fundest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_fundest_stock_date"),
    )


class FundPosition(Base):
    """基金仓位比例"""
    __tablename__ = "fundposition"

    id = Column(Integer, primary_key=True, comment="直接对应 stock.id")
    close = Column(Float, nullable=False, default=1.0)

    def __repr__(self):
        return f"<FundPosition(stock_id={self.id}, position={self.close})>"


class LastCalibration(Base):
    """最近一次校准值"""
    __tablename__ = "lastcalibration"

    id = Column(Integer, primary_key=True, comment="直接对应 stock.id")
    close = Column(Float, nullable=False)

    def __repr__(self):
        return f"<LastCalibration(stock_id={self.id}, close={self.close})>"


class FuturePremium(Base):
    """期货溢价数据"""
    __tablename__ = "futurepremium"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_futurepremium_stock_date"),
    )


class StockSplit(Base):
    """拆股/合股记录"""
    __tablename__ = "stocksplit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stocksplit_stock_date"),
    )


class StockDividend(Base):
    """股票分红记录"""
    __tablename__ = "stockdividend"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockdividend_stock_date"),
    )


class QuarterReport(Base):
    """季度报告"""
    __tablename__ = "quarterreport"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(String(8192))

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_quarterreport_stock_date"),
    )


class SharesHistory(Base):
    """ETF份额历史"""
    __tablename__ = "shareshistory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_shareshistory_stock_date"),
    )


class SharesDiff(Base):
    """ETF份额日变动"""
    __tablename__ = "sharesdiff"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float)

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_sharesdiff_stock_date"),
    )


class StockTick(Base):
    """股票访问tick计数"""
    __tablename__ = "stocktick"

    id = Column(Integer, primary_key=True)
    tick = Column(Integer, nullable=False, default=0)


class StockHistoryDate(Base):
    """股票历史数据最早日期"""
    __tablename__ = "date"

    id = Column(Integer, primary_key=True, comment="直接对应 stock.id")
    date = Column(Date, nullable=False)


class HoldingsDate(Base):
    """基金持仓数据更新日期"""
    __tablename__ = "holdingsdate"

    id = Column(Integer, primary_key=True, comment="直接对应 stock.id")
    date = Column(Date, nullable=False)


class XopNavSsga(Base):
    """XOP净值 - SSGA官方NAV历史Excel

    来源: SSGA官网 navhist-us-en-xop.xlsx (State Street SPDR)
    URL: https://www.ssga.com/.../library-content/products/fund-data/etfs/us/navhist-us-en-xop.xlsx
    用途: premium_history 页面展示XOP净值（ETF净值非收盘价）
    """
    __tablename__ = "xop_nav_ssga"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    close = Column(DECIMAL(12, 6))  # 保留6位小数精度

    __table_args__ = (
        UniqueConstraint("date", name="uq_xop_nav_ssga_date"),
        Index("idx_xop_nav_ssga_date", "date"),
    )
