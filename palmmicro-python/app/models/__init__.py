"""
Palmmicro Python — 数据模型包
导出所有 SQLAlchemy ORM 模型

使用方式：
  from app.models import (
      Stock, StockHistory, StockEma50, StockEma200,
      NetValueHistory, CalibrationHistory, FundEst,
      FundPosition, LastCalibration, FuturePremium,
      StockSplit, StockDividend, QuarterReport,
      SharesHistory, SharesDiff, StockTick,
      StockHistoryDate, HoldingsDate,
      StockGroup, StockGroupItem, StockTransaction,
      GroupItemAmount, GroupItemExtra,
      AbPair, AhPair, AdrPair, FundPair,
      Holdings,
  )
"""

from app.models.stock import Stock

from app.models.market_data import (
    StockHistory,
    StockEma50,
    StockEma200,
    NetValueHistory,
    CalibrationHistory,
    FundEst,
    FundPosition,
    LastCalibration,
    FuturePremium,
    StockSplit,
    StockDividend,
    QuarterReport,
    SharesHistory,
    SharesDiff,
    StockTick,
    StockHistoryDate,
    HoldingsDate,
)

from app.models.trading import (
    StockGroup,
    StockGroupItem,
    StockTransaction,
    GroupItemAmount,
    GroupItemExtra,
)

from app.models.pair import (
    AbPair,
    AhPair,
    AdrPair,
    FundPair,
)

from app.models.holdings import Holdings

__all__ = [
    # 股票基础
    "Stock",
    # 市场数据（时间序列）
    "StockHistory",
    "StockEma50",
    "StockEma200",
    "NetValueHistory",
    "CalibrationHistory",
    "FundEst",
    "FundPosition",
    "LastCalibration",
    "FuturePremium",
    "StockSplit",
    "StockDividend",
    "QuarterReport",
    "SharesHistory",
    "SharesDiff",
    "StockTick",
    "StockHistoryDate",
    "HoldingsDate",
    # 投资组合 & 交易
    "StockGroup",
    "StockGroupItem",
    "StockTransaction",
    "GroupItemAmount",
    "GroupItemExtra",
    # 配对关系
    "AbPair",
    "AhPair",
    "AdrPair",
    "FundPair",
    # 持仓数据
    "Holdings",
]
