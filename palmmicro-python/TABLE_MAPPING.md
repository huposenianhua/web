# PHP → Python 数据库表映射文档

> **生成日期**: 2026-05-03
> **总表数**: **29** 张（PHP 原 40 张，去掉用户/站务 12 张，**新增 xop_nav_ssga 1 张**）

---

## 一、已翻译的 28 张表

### 1.1 股票基础（1张）

| PHP 类 | PHP 表名 | Python 模型 | Python 文件 | 说明 |
|--------|---------|-------------|------------|------|
| `StockSql` | `stock` | `Stock` | `stock.py` | 股票/基金基本信息（id, symbol, name） |

### 1.2 市场数据 - 时间序列（17张）

| PHP 类 | PHP 表名 | Python 模型 | Python 文件 | 说明 |
|--------|---------|-------------|------------|------|
| `StockHistorySql` | `stockhistory` | `StockHistory` | `market_data.py` | 历史价格（收盘、成交量、前复权） |
| `StockEmaSql(50)` | `stockema50` | `StockEma50` | `market_data.py` | 50日均线 |
| `StockEmaSql(200)` | `stockema200` | `StockEma200` | `market_data.py` | 200日均线 |
| `DailyCloseSql` | `netvaluehistory` | `NetValueHistory` | `market_data.py` | 基金净值历史 |
| `CalibrationSql` | `calibrationhistory` | `CalibrationHistory` | `market_data.py` | QDII校准历史（含均值逻辑） |
| `DailyTimeSql` | `fundest` | `FundEst` | `market_data.py` | 基金实时估算净值 |
| `FundPositionSql` | `fundposition` | `FundPosition` | `market_data.py` | 基金仓位比例 |
| `LastCalibrationSql` | `lastcalibration` | `LastCalibration` | `market_data.py` | 最近校准值 |
| `FuturePremiumSql` | `futurepremium` | `FuturePremium` | `market_data.py` | 期货溢价 |
| `StockSplitSql` | `stocksplit` | `StockSplit` | `market_data.py` | 拆股记录 |
| `StockDividendSql` | `stockdividend` | `StockDividend` | `market_data.py` | 分红记录 |
| `QuarterReportSql` | `quarterreport` | `QuarterReport` | `market_data.py` | 季报（文本型） |
| `SharesHistorySql` | `shareshistory` | `SharesHistory` | `market_data.py` | ETF份额历史 |
| `SharesDiffSql` | `sharesdiff` | `SharesDiff` | `market_data.py` | ETF份额变动 |
| `StockTickSql` | `stocktick` | `StockTick` | `market_data.py` | 爬虫检测计数 |
| `StockHistoryDateSql` | `stockhistorydate` | `StockHistoryDate` | `market_data.py` | 历史数据最早日期 |
| `HoldingsDateSql` | `holdingsdate` | `HoldingsDate` | `market_data.py` | 持仓数据日期 |
| — | **xop_nav_ssga** | **XopNavSsga** | **market_data.py** | **XOP SSGA官方NAV（仅展示用，非PHP原表）** |

### 1.3 投资组合 & 交易（5张）

| PHP 类 | PHP 表名 | Python 模型 | Python 文件 | 说明 |
|--------|---------|-------------|------------|------|
| `StockGroupSql` | `stockgroup` | `StockGroup` | `trading.py` | 投资组合（**已去掉 member_id**） |
| `StockGroupItemSql` | `stockgroupitem` | `StockGroupItem` | `trading.py` | 组合持仓项 |
| `StockTransactionSql` | `stocktransaction` | `StockTransaction` | `trading.py` | 交易记录 |
| `GroupItemAmountSql` | `groupitemamount` | `GroupItemAmount` | `trading.py` | 持仓目标金额 |
| `GroupItemExtraSql` | `groupitemextra` | `GroupItemExtra` | `trading.py` | 持仓额外数据 |

### 1.4 配对关系（4张）

| PHP 类 | PHP 表名 | Python 模型 | Python 文件 | 说明 |
|--------|---------|-------------|------------|------|
| `StockPairSql` | `abpair` | `AbPair` | `pair.py` | A股↔B股 |
| `StockPairSql` | `ahpair` | `AhPair` | `pair.py` | A股↔H股 |
| `StockPairSql` | `adrpair` | `AdrPair` | `pair.py` | H股↔ADR |
| `StockPairSql` | `fundpair` | `FundPair` | `pair.py` | 基金↔ETF |

### 1.5 持仓数据（1张）

| PHP 类 | PHP 表名 | Python 模型 | Python 文件 | 说明 |
|--------|---------|-------------|------------|------|
| `HoldingsSql` | `holdings` | `Holdings` | `holdings.py` | ETF成分股持仓比例 |

---

## 二、已丢弃的 12 张表（用户/站务相关）

| PHP 表名 | PHP 类 | 原用途 | 丢弃原因 |
|---------|--------|--------|---------|
| `member` / `member2` | `MemberSql` | 用户注册登录 | 不做用户系统 |
| `profile` | 函数式操作 | 用户资料 | 不做用户系统 |
| `page` | `PageSql` | 博客页面URI | 不做博客 |
| `pagecomment` | `PageCommentSql` | 博客评论 | 不做博客 |
| `visitor` | `VisitorSql` | 访客统计 | 不做站务 |
| `telegrambot` | `BotVisitorSql` | TG Bot日志 | Bot照常运行，不需要日志表 |
| `wechatbot` | `BotVisitorSql` | 微信Bot日志 | 同上 |
| `botmsg` | `BotMsgSql` | Bot消息文本 | 同上 |
| `botsrc` | `BotSrcSql` | Bot消息来源 | 同上 |
| `gb2312` | `GB2312Sql` | 编码转换 | Python原生支持Unicode |
| `ipaddress` | `IpAddressSql` | IP黑白名单 | 不做爬虫防护 |
| `commonphrase` | `CommonPhraseSql` | 常用短语 | 博客相关 |

---

## 三、关键设计变更

### 3.1 stockgroup 去掉 member_id

```
PHP:  stockgroup(id, member_id, groupname)  UNIQUE(member_id, groupname)
Python: stockgroup(id, groupname)            UNIQUE(groupname)
```

影响范围：
- `StockGroupSql.__construct()` 中 `TABLE_MEMBER` 参数 → 去掉
- `SqlGetStockGroupId(member_id, name)` → 改为 `SqlGetStockGroupId(name)`
- `SqlDeleteStockGroupByMemberId(member_id)` → 改为 `SqlDeleteAllGroups()`
- 其余表（stockgroupitem, stocktransaction）不受影响

### 3.2 配对表简化

PHP 中 4 种配对共用一个 `PairSql` 基类，Python 中各自独立模型，更清晰。

### 3.3 id 即 stock_id 的表

以下表的 `id` 直接就是某只股票的 `stock_id`，每只股票只有一条记录：
- `fundposition` → id = stock_id（仓位比例）
- `lastcalibration` → id = stock_id（最新校准值）
- `stocktick` → id = ip地址整数（爬虫计数）
- `groupitemamount` → id = stockgroupitem_id（目标金额）
- `groupitemextra` → id = stockgroupitem_id（额外数据）
- `stockhistorydate` → id = stock_id（最早日期）
- `holdingsdate` → id = stock_id（最早日期）

---

## 四、项目文件结构

```
palmmicro-python/
├── app/
│   ├── __init__.py           # 应用包初始化
│   ├── database.py           # SQLAlchemy 引擎 + 会话配置
│   └── models/
│       ├── __init__.py       # 导出所有 28 个模型
│       ├── stock.py          # 1 张表（Stock）
│       ├── market_data.py    # 17 张表（历史价格、EMA、校准等）
│       ├── trading.py        # 5 张表（组合、持仓、交易）
│       ├── pair.py           # 4 张表（AB/AH/ADR/基金配对）
│       └── holdings.py       # 1 张表（ETF持仓明细）
├── .env.example              # 环境变量模板
├── .gitignore
├── requirements.txt          # 依赖包
└── TABLE_MAPPING.md          # 本文档
```

---

## 五、EST计算流程设计决策（2026-05-07 新增）

### 5.1 XOP 双数据源设计

| 用途 | 数据源 | 表/来源 | 说明 |
|------|--------|---------|------|
| **EST计算**（factor校准 + 官方估值） | Yahoo收盘价 | `netvaluehistory` (symbol=XOP) | 与PHP作者一致 |
| **页面展示**（XOP净值栏） | SSGA官方NAV | `xop_nav_ssga` | Python新增，PHP无此表 |

**原因**: SSGA官方NAV是ETF真实净值（每日发布），与Yahoo收盘价有微小差异。作者用Yahoo收盘价做计算，我们保留SSGA数据用于展示，让用户看到更精确的XOP净值。

### 5.2 fundposition 默认值规则

```
fundposition.close 默认值:
  - LOF基金 (如162411): 0.95    ← 仓位95%，留5%给base_val平滑
  - 非LOF基金:         1.0      ← 全仓跟踪

Python代码位置: app/services/fundref.py → _get_position()
  1. 先查 fundposition 表（有记录则用记录值）
  2. 无记录时: is_lof_a() → 0.95, 否则 → 1.0
```

### 5.3 QDII日期映射规则

premium_history 页面每行数据的日期处理：

| 变量 | 含义 | 来源 | QDII特殊处理 |
|------|------|------|-------------|
| **his_date** | 页面显示日期 | `stockhistory.date` | T日（当天） |
| **nav_date** | 净值查询日期 | `netvaluehistory` 前一日 | **T-1日**（QDII延迟一天） |

**所有 NAV / EST / XOP / CNY 查询统一使用 nav_date（T-1）**，而非 his_date（T）。这是QDII基金溢价页面的核心日期映射逻辑。

### 5.4 factor 查询策略

```
PHP作者做法: LoadCalibration() → GetRecordNow() → 取 calibrationhistory 最新一条
Python实现: CalibrationHistory.query.filter(stock_id=xx).order_by(date.desc()).first()

★ 不是按日期匹配的 daily factor，而是全局最新一条
★ 原因: factor 是"之前某次校准"的结果，用于跨日预测
```

### 5.5 premium_history 路由核心流程

```
routes.py → premium_history(stock_symbol)

1. 查 stockhistory (his_date, price) — 页面每行基础数据
2. 对QDII: nav_date = his_date 前一交易日
3. 查 fundest(nav_date) → 有则直接用预存EST
4. 无fundest时实时计算:
   a. XOP_Yahoo = netvaluehistory(XOP, nav_date).close   ← Yahoo收盘价
   b. CNY      = netvaluehistory(USCNY, nav_date).close
   c. factor   = calibrationhistory 最新一条 .close
   d. raw_est  = qdii_get_val(XOP, CNY, factor)            ← XOP×CNY÷factor
   e. base_val = lastcalibration(stock_id).close
   f. est      = fund_adjust_position(position, raw_est, base_val)
5. NAV = netvaluehistory(162411, nav_date).close
6. error = (est / nav - 1) × 100%                          ← (EST/NAV-1)%
7. XOP展示 = xop_nav_ssga(nav_date).close                  ← SSGA官方NAV
```
