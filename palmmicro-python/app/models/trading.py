"""
投资组合 & 交易记录模型

对应 PHP 文件：
  - sql/sqlstockgroup.php      → StockGroupSql, StockGroupItemSql, GroupItemAmountSql, GroupItemExtraSql
  - sql/sqlkeystring.php       → KeyStringSql (基类)
  - sql/sqlstocktransaction.php → StockTransactionSql

重要变更：相比 PHP 原版，stockgroup 表去掉了 member_id 字段。
原因：本系统为个人使用，不需要多用户支持。

---

表清单：
  1. stockgroup      — 投资组合（去掉了 member_id）
  2. stockgroupitem  — 组合内的持仓项（stock_id → 股票，quantity → 数量，cost → 成本）
  3. stocktransaction— 交易记录（买卖操作）
  4. groupitemamount — 组合项目标金额（用于网格交易参考）
  5. groupitemextra  — 组合项额外数据（record 记录数，quantity 额外数量，cost 额外成本）
"""

from sqlalchemy import (
    Column, Integer, Float, String, UniqueConstraint, Index, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


# ============================================================
# 1. stockgroup — 投资组合
# ============================================================
# PHP: StockGroupSql extends KeyStringSql
# 原始建表：
#   member_id INT UNSIGNED NOT NULL,  ← 已删除
#   groupname VARCHAR(64) NOT NULL,
#   UNIQUE (groupname, member_id)     ← 改为 UNIQUE (groupname)

class StockGroup(Base):
    """投资组合

    每个组合代表一个投资策略或账户（如"网格交易"、"QDII套利"）。
    PHP 原版挂在 member 下面，现在去掉 member_id，直接作为顶级实体。
    groupname 全局唯一。
    """
    __tablename__ = "stockgroup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    groupname = Column(String(64), nullable=False, unique=True, comment="组合名称")

    # --- 关联关系 ---
    items = relationship("StockGroupItem", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StockGroup(id={self.id}, groupname='{self.groupname}')>"


# ============================================================
# 2. stockgroupitem — 组合持仓项
# ============================================================
# PHP: StockGroupItemSql extends KeyTableSql
# 原始建表：
#   stockgroup_id INT UNSIGNED NOT NULL,  FOREIGN KEY → stockgroup(id)
#   stock_id      INT UNSIGNED NOT NULL,
#   quantity      INT NOT NULL,
#   cost          DOUBLE(10,3) NOT NULL,
#   record        INT NOT NULL,
#   INDEX (record),
#   UNIQUE (stock_id, stockgroup_id)

class StockGroupItem(Base):
    """组合内的持仓项

    每条记录代表组合中持有的一只股票/基金。
    quantity: 持有数量（股数/份额）
    cost:     持仓成本
    record:   交易记录数（用于判断是否有交易历史，0=无交易）
    """
    __tablename__ = "stockgroupitem"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stockgroup_id = Column(Integer, ForeignKey('stockgroup.id'), nullable=False, comment="关联 stockgroup.id")
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=False, comment="关联 stock.id")
    quantity = Column(Integer, nullable=False, default=0, comment="持有数量")
    cost = Column(Float, nullable=False, default=0.0, comment="持仓成本")
    record = Column(Integer, nullable=False, default=0, comment="交易记录数（0=无交易）")

    # --- 关联关系 ---
    group = relationship("StockGroup", back_populates="items")
    transactions = relationship("StockTransaction", back_populates="group_item", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("stock_id", "stockgroup_id", name="uq_stockgroupitem_stock_group"),
        Index("idx_stockgroupitem_record", "record"),
    )

    def __repr__(self):
        return f"<StockGroupItem(id={self.id}, group_id={self.stockgroup_id}, stock_id={self.stock_id}, qty={self.quantity})>"


# ============================================================
# 3. stocktransaction — 交易记录
# ============================================================
# PHP: StockTransactionSql extends TableSql
# 原始建表：
#   groupitem_id INT UNSIGNED NOT NULL,  （关联 stockgroupitem.id）
#   quantity     INT NOT NULL,
#   price        DOUBLE NOT NULL,
#   fees         DOUBLE NOT NULL,
#   filled       DATETIME NOT NULL,      （成交日期时间）
#   remark       VARCHAR(8192) NOT NULL  （备注）

class StockTransaction(Base):
    """交易记录

    记录每笔买入/卖出操作。
    groupitem_id 指向 stockgroupitem，表示这笔交易属于哪个组合的哪只持仓。
    filled 存储成交的日期时间。
    quantity 正数=买入，负数=卖出（由业务逻辑控制）。
    """
    __tablename__ = "stocktransaction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    groupitem_id = Column(Integer, ForeignKey('stockgroupitem.id'), nullable=False, comment="关联 stockgroupitem.id")
    quantity = Column(Integer, nullable=False, comment="成交数量（正=买入，负=卖出）")
    price = Column(Float, nullable=False, comment="成交价格")
    fees = Column(Float, nullable=False, default=0.0, comment="手续费")
    filled = Column(String(19), nullable=False, comment="成交日期时间（YYYY-MM-DD HH:MM:SS）")
    remark = Column(String(8192), nullable=False, default="", comment="备注")

    # --- 关联关系 ---
    group_item = relationship("StockGroupItem", back_populates="transactions")

    __table_args__ = (
        Index("idx_stocktransaction_filled", "filled"),
    )

    def __repr__(self):
        return f"<StockTransaction(id={self.id}, groupitem_id={self.groupitem_id}, qty={self.quantity}, price={self.price})>"


# ============================================================
# 4. groupitemamount — 组合项目标金额
# ============================================================
# PHP: GroupItemAmountSql extends IntSql
# 表名：groupitemamount
# id 即为 stockgroupitem_id，num 存储目标金额
# 默认值 100000（10万元）

class GroupItemAmount(Base):
    """组合持仓项的目标金额

    用于网格交易等策略，记录每只持仓的目标投入金额。
    id 直接对应 stockgroupitem.id，每条持仓只有一条记录。
    默认 100000（10万元）。
    """
    __tablename__ = "groupitemamount"

    id = Column(Integer, primary_key=True, comment="直接对应 stockgroupitem.id")
    num = Column(Integer, nullable=False, default=100000, comment="目标金额（默认10万元）")

    def __repr__(self):
        return f"<GroupItemAmount(groupitem_id={self.id}, amount={self.num})>"


# ============================================================
# 5. groupitemextra — 组合项额外数据
# ============================================================
# PHP: GroupItemExtraSql extends IntSql
# 表名：groupitemextra
# id 即为 stockgroupitem_id
# 额外字段：record, quantity, cost

class GroupItemExtra(Base):
    """组合持仓项的额外数据

    存储持仓项的补充信息：
    record:   额外记录数
    quantity: 额外数量
    cost:     额外成本
    id 直接对应 stockgroupitem.id。
    """
    __tablename__ = "groupitemextra"

    id = Column(Integer, primary_key=True, comment="直接对应 stockgroupitem.id")
    record = Column(Integer, nullable=False, default=0, comment="额外记录数")
    quantity = Column(Integer, nullable=False, default=0, comment="额外数量")
    cost = Column(Float, nullable=False, default=0.0, comment="额外成本")

    def __repr__(self):
        return f"<GroupItemExtra(groupitem_id={self.id}, record={self.record}, qty={self.quantity}, cost={self.cost})>"
