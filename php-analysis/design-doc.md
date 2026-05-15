# PHP 项目全量分析设计文档

> **项目路径**: `/Users/smithclinton/php` (php/) + `/Users/smithclinton/dev/web-master/res` (res/)
> **分析日期**: 2026-05-02
> **文件总数**: 135 (134 PHP + 1 TXT) + 26 (res/) = **161**
> **代码总行数**: ~44,500 行 (php/) + ~1,581 行 (res/) = **~46,081 行**
> **状态**: ✅ 全量分析完成（php/ ✅ + res/ ✅）

---

## 一、项目概览

### 1.1 项目性质
这是一个 **股票/基金数据分析和交易管理网站**（Palmmicro），由作者 Woody 开发，域名 palmmicro.com。核心功能包括：
- **中美港三地股票实时行情获取与展示**（通过新浪财经、Yahoo Finance API）
- **QDII基金净值估算**（根据海外ETF实时价格、汇率、持仓比例估算基金净值）
- **A股/B股/H股/ADR配对交易分析**（AH溢价、AB溢价、ADR溢价）
- **用户投资组合管理**（持仓、交易记录、盈亏计算、多币种汇总）
- **微信/Telegram Bot 自动查询**（输入股票代码返回实时数据）
- **博客评论系统 + 访客统计 + 爬虫防护**
- **数学分析工具**（线性回归、卡方检验、Benford定律、Cramer法则等）

### 1.2 技术栈
- **后端**: PHP (mysqli)，MySQL 数据库
- **前端**: 原生 HTML/CSS/JS，Google Analytics + Google AdSense
- **外部数据源**: 新浪财经 API、Yahoo Finance API、中国货币网、深交所/上交所
- **Bot 接口**: 微信公众号 API、Telegram Bot API
- **移动端适配**: Mobile Detect 库

### 1.3 语言支持
全站支持中英文双语切换，通过 URL 后缀 `.php`（英文）和 `cn.php`（中文）区分。

---

## 二、目录结构与模块划分

### 2.1 目录层级

```
php/
├── (根目录，46个文件)  — 核心功能、入口、工具函数、Bot入口
├── class/              — 3个文件 — 基础类（INI文件解析、多币种、日期时间）
├── sql/                — 26个文件 — 数据库操作层（ORM封装）
├── stock/              — 16个文件 — 股票数据源/引用/解析
├── test/               — 6个文件 — 数据更新脚本/测试
├── tutorial/           — 5个文件 — 数学算法教程
└── ui/                 — 35个文件 — UI展示组件
```

### 2.2 入口文件

| 入口文件 | 类型 | 功能 |
|---------|------|------|
| `telegram.php` | Bot 入口 | Telegram Bot webhook，接收消息并返回股票数据 |
| `weixincn.php` | Bot 入口 | 微信公众号 webhook，中文股票查询 |
| `test.php` | 调试入口 | 管理员工具页面，清理数据 |
| `_submitcomment.php` | 表单处理 | 博客评论提交/编辑/删除 |
| `_submitdelete.php` | 管理操作 | 管理员删除操作 |
| `_submitoperation.php` | 管理操作 | 管理员标记爬虫/恶意IP |
| `blogcomments.php` | 页面入口 | 博客评论展示页 |
| `usercomments.php` | 页面入口 | 用户评论页 |

---

## 三、依赖关系图

### 3.1 核心依赖层级（从底层到上层）

```
Layer 0 (最底层，无依赖):
  └── url.php              — URL处理、IP获取、cURL请求

Layer 1 (基础工具):
  ├── debug.php            — 调试日志、浮点数处理、文件路径管理
  ├── email.php            — HTML邮件发送
  ├── regexp.php           — 正则表达式辅助
  └── externalurl.php      — 外部URL常量定义

Layer 2 (数据库):
  ├── sql.php              — 数据库连接、CRUD基础、表名常量、错误处理
  ├── sql/_sqlcommon.php   — SQL构建辅助函数
  └── class/year_month_day.php — 日期时间处理（全局$g_now_ymd）

Layer 3 (链接/HTML):
  ├── httplink.php         — 内部链接生成、分页、菜单
  ├── internallink.php     — 账户/工具/访客链接
  ├── ui/htmlelement.php   — HTML元素生成
  └── ui/echohtml.php      — HTML输出

Layer 4 (股票核心):
  ├── stock/stocksymbol.php — 股票代码解析/分类（A股/H股/美股/基金/期货）
  ├── stock/yahoostock.php — Yahoo数据解析
  ├── stock/stockprefetch.php — 数据预获取（Sina API批量请求）
  ├── stock/stockref.php   — 股票引用基类
  ├── stock/mystockref.php — 自定义股票引用
  ├── stock/cnyref.php     — 人民币汇率
  ├── stock/netvalueref.php — 净值引用
  ├── stock/fundref.php    — 基金引用
  ├── stock/qdiiref.php    — QDII基金引用
  ├── stock/fundpairref.php — 配对基金引用
  ├── stock/holdingsref.php — 持仓引用
  ├── gb2312.php           — GB2312转UTF8
  ├── stock.php            — 股票核心聚合层
  └── externallink.php     — 股票外部链接生成

Layer 5 (业务逻辑):
  ├── account.php          — 用户账户/认证/爬虫防护（核心类Account）
  ├── switch.php           — 页面跳转/Session管理
  ├── stockbot.php         — Bot股票查询逻辑
  ├── stockdataarray.php   — 股票数据数组输出
  ├── stockgroup.php       — 股票分组/组合
  ├── stocktrans.php       — 交易记录
  └── stockhis.php         — 历史价格/SMA/Bollinger带

Layer 6 (UI展示):
  ├── layout.php           — 页面布局框架
  ├── menu.php             — 导航菜单
  ├── stocklink.php        — 股票相关链接
  ├── copyright.php        — 版权信息
  ├── analytics.php        — Google Analytics
  ├── adsense.php          — Google AdSense
  └── ui/*.php             — 各种段落/表格/图表展示

Layer 7 (Bot入口):
  ├── telegram.php         — Telegram Bot
  ├── weixincn.php         — 微信Bot（中文）
  └── weixin.php           — 微信Bot基类
```

### 3.2 数据库表结构

从 `sql.php` 中定义的常量提取：

| 表名常量 | 实际表名 | 用途 |
|---------|---------|------|
| TABLE_MEMBER | member | 用户会员 |
| TABLE_PAGE | page | 页面记录 |
| TABLE_PAGE_COMMENT | pagecomment | 页面评论 |
| TABLE_PROFILE | profile | 用户资料 |
| TABLE_STOCK_DIVIDEND | stockdividend | 股票分红 |
| TABLE_STOCK_GROUP | stockgroup | 股票分组 |
| TABLE_STOCK_GROUP_ITEM | stockgroupitem | 分组项 |
| TABLE_STOCK_SPLIT | stocksplit | 拆股合股 |
| TABLE_VISITOR | visitor | 访客记录 |
| TABLE_TELEGRAM_BOT | telegrambot | Telegram Bot |
| TABLE_WECHAT_BOT | wechatbot | 微信Bot |

其他表（从 sql/ 子目录推断）：
- stock — 股票基本信息
- stockhistory — 历史价格（adjclose）
- stockgroupitem — 分组持仓（quantity, cost, record）
- stocktransaction — 交易记录（quantity, price, fees, filled）
- netvaluehistory — 净值历史
- calibration — 校准数据
- fundest — 基金估算
- fundpurchase — 基金申购
- holdings — 基金持仓
- position — 仓位
- pair — 配对关系（AB/AH/ADR）
- ema50, ema200 — EMA数据
- ipaddress — IP地址（爬虫/恶意）
- ipvisit, iplogin — IP统计
- iptick — 爬虫tick
- blog/botmsg/botsrc/botvisitor — Bot消息
- gb2312 — GB2312编码映射
- primenumber — 质数表

---

## 四、逐文件分析

### 4.1 根目录文件（46个）

#### url.php — URL/HTTP 基础工具
- **优先级**: ⭐⭐⭐⭐⭐ 核心底层
- **依赖**: 无
- **功能**: IP获取（支持代理头）、cURL封装、URL解析、查询字符串处理
- **关键函数**: `UrlGetIp()`, `url_get_contents()`, `UrlGetServer()`, `UrlGetUri()`, `UrlGetPage()`, `UrlGetType()`, `UrlCleanString()`, `UrlGetQueryString()`
- **常量**: URL_PHP('.php'), URL_CNPHP('cn.php')

#### debug.php — 调试/日志/工具
- **优先级**: ⭐⭐⭐⭐⭐ 核心底层
- **依赖**: url.php
- **功能**: 调试日志写入、浮点数处理、日期时间格式化、文件路径管理
- **关键函数**: `DebugString()`, `DebugPrint()`, `strval_round()`, `mysql_round()`, `explode_float()`, `DebugGetPathName()`, `DebugGetImageName()`, `GetNowYMD()`, `GetNowTick()`
- **常量**: MIN_FLOAT_VAL(0.0000005), FLOAT_PRECISION(6), NETVALUE_PRECISION(4), SECONDS_IN_MIN/HOUR/DAY
- **全局**: 管理 debug/ 目录下的文件路径

#### email.php — 邮件发送
- **优先级**: ⭐⭐
- **依赖**: ui/htmlelement.php
- **功能**: 发送HTML格式邮件
- **关键函数**: `EmailHtml($strWho, $strSubject, $strContents)`
- **常量**: ADMIN_EMAIL('woody@palmmicro.com')

#### regexp.php — 正则表达式辅助
- **优先级**: ⭐⭐
- **依赖**: stock/stocksymbol.php
- **功能**: 正则表达式模板构建、调试
- **关键函数**: `RegExpBoundary()`, `RegExpSpace()`, `RegExpAll()`, `RegExpDate()`, `RegExpParenthesis()`, `RegExpStockSymbol()`, `PregMatchSquareBracket()`

#### externalurl.php — 外部URL常量
- **优先级**: ⭐⭐
- **依赖**: 无
- **功能**: 定义所有外部数据源URL（Yahoo、Sina、东方财富、雪球、集思录等）
- **关键函数**: `GetYahooStockUrl()`, `GetSinaDataUrl()`, `GetSinaFinanceUrl()`, `GetKraneUrl()`, `GetSseUrl()`, `GetSzseUrl()`, `GetChinaMoneyUrl()`, `GetCmeUrl()`, `GetIsharesEtfUrl()`, `GetSpdrUrl()`, `GetInvescoUrl()`

#### sql.php — 数据库核心
- **优先级**: ⭐⭐⭐⭐⭐ 核心底层
- **依赖**: debug.php, email.php, httplink.php, ui/htmlelement.php, class/year_month_day.php, 多个sql/子文件
- **功能**: 数据库连接、CRUD操作、表名定义、全局错误处理
- **关键函数**: `SqlConnectDatabase()`, `SqlGetTableData()`, `SqlGetSingleTableData()`, `SqlGetTableDataById()`, `SqlDeleteTableData()`, `SqlCountTableData()`, `SqlCreateDatabase()`, `SqlCleanString()`, `die_mysql_error()`, `SqlDieByQuery()`, `_errorHandler()`
- **全局变量**: `$g_link` (MySQL连接)
- **常量**: DB_DATABASE, TABLE_MEMBER, TABLE_PAGE, TABLE_PAGE_COMMENT, TABLE_STOCK_GROUP 等10+个表名常量
- **数据库**: MySQL (mysqli), 连接到 'mysql' 主机, 数据库 'n5gl0n39mnyn183l_camman'

#### account.php — 用户账户/认证核心
- **优先级**: ⭐⭐⭐⭐⭐ 核心业务
- **依赖**: switch.php, sql.php, ui/table.php, 多个sql/子文件
- **功能**: 用户认证、会话管理、IP黑白名单、爬虫检测、页面访问统计
- **类**:
  - `Account`: 基类，session_start() + SqlConnectDatabase() + IP检查 + 页面访问记录
    - `IsCrawler()`, `IsMalicious()`, `SetCrawler()`, `SetMalicious()`, `Auth()`, `GetLoginId()`, `GetMemberId()`, `IsPalmmicro()`, `IsAdmin()`, `AdminRun()`, `Run()`
  - `TitleAccount extends Account`: 带分页/查询的账户
    - `GetPage()`, `GetQuery()`, `GetStart()`, `GetNum()`

#### switch.php — 页面跳转/Session
- **优先级**: ⭐⭐⭐
- **依赖**: 无
- **功能**: HTTP重定向、Session URL保存/恢复
- **关键函数**: `SwitchToLink()`, `SwitchTo()`, `SwitchSetSess()`, `SwitchGetSess()`, `SwitchToSess()`

#### layout.php — 页面布局框架
- **优先级**: ⭐⭐⭐⭐
- **依赖**: account.php, menu.php, copyright.php, analytics.php, adsense.php, ui/echohtml.php, Mobile-Detect 库
- **功能**: 页面框架布局、移动端检测、图片缩放、响应式宽度
- **关键函数**: `LayoutIsMobilePhone()`, `LayoutTopLeft()`, `LayoutTail()`, `ResizeJpg()`, `GetWechatPay()`, `LayoutScreenWidthOk()`, `LayoutGetDisplayWidth()`

#### menu.php — 导航菜单
- **优先级**: ⭐⭐⭐
- **依赖**: ui/htmlelement.php, httplink.php(间接)
- **功能**: 菜单项渲染、标题导航（首页/上一页/下一页/末页）、分类菜单
- **关键函数**: `MenuGetLink()`, `MenuWriteLink()`, `MenuTitle()`, `MenuDirFirstLast()`, `MenuDirLoop()`, `MenuSet()`

#### httplink.php — 链接生成/分页
- **优先级**: ⭐⭐⭐
- **依赖**: ui/htmlelement.php, url.php(间接)
- **功能**: 内部/外部链接生成、分页菜单、删除确认链接
- **关键函数**: `GetInternalLink()`, `GetExternalLink()`, `GetPhpLink()`, `CopyPhpLink()`, `GetMenuLink()`, `GetNewLink()`, `GetEditLink()`, `GetCategoryLinks()`
- **常量**: PATH_STOCK('/woody/res/'), MENU_DIR_*, DEFAULT_PAGE_NUM(100)

#### internallink.php — 内部链接
- **优先级**: ⭐⭐
- **依赖**: sql.php(间接)
- **功能**: 账户工具链接、IP链接、访客链接、Bot显示名
- **关键函数**: `GetMemberLink()`, `GetAccountToolLinks()`, `GetIpLink()`, `GetVisitorLink()`, `GetAllVisitorLink()`, `GetAllCommentLink()`

#### stocklink.php — 股票链接
- **优先级**: ⭐⭐⭐
- **依赖**: ui/stocktable.php, stock/stocksymbol.php
- **功能**: 所有股票相关页面链接生成
- **关键函数**: `GetStockCategoryLinks()`, `GetMyStockLink()`, `GetFundLinks()`, `GetCalibrationHistoryLink()`, `GetHoldingsLink()`, `GetStockHistoryLink()`, `GetNetValueHistoryLink()`, `StockGetTransactionLink()`
- **常量**: 大量股票显示名称常量（QDII_DISPLAY, AH_HISTORY_DISPLAY 等）

#### externallink.php — 股票外部链接
- **优先级**: ⭐⭐
- **依赖**: stocklink.php, externalurl.php, stock/stocksymbol.php
- **功能**: 生成Yahoo/Sina/雪球/东方财富等外部股票页面链接
- **关键函数**: `GetOfficialLink()`, `GetYahooStockLink()`, `GetSinaStockLink()`, `GetXueqiuLink()`, `GetEastMoneyFundLink()`, `GetStockChartsLink()`

#### stock.php — 股票核心聚合层
- **优先级**: ⭐⭐⭐⭐⭐ 核心业务
- **依赖**: regexp.php, externallink.php, sql.php, gb2312.php, 多个stock/和sql/子文件
- **功能**: 股票代码解析、实时数据获取(Sina)、价格显示、配对关系、QDII分析
- **关键函数**: `StockGetSymbol()`, `GetInputSymbolArray()`, `GetSinaQuotes()`, `StockGetPriceDisplay()`, `StockGetPercentage()`, `StockPrefetchArrayExtendedData()`, `StockGetReference()`, `StockGetFundReference()`, `StockGetPairReferences()`, `GetStockHedge()`
- **核心逻辑**: `_getAllSymbolArray()` — 根据股票类型(A股/H股/美股/基金)递归查找所有关联代码（AB配对、AH配对、ADR配对、QDII标的、持仓成分等）

#### stockbot.php — Bot 股票查询
- **优先级**: ⭐⭐⭐⭐
- **依赖**: stock.php, sql/sqlbotvisitor.php, ui/stocktext.php
- **功能**: 微信/Telegram Bot 的股票查询核心逻辑
- **关键函数**: `StockBotGetStr($strText, $strVersion)`, `_botGetStockArray($strKey)`, `_botGetStockText($strSymbol)`, `LogBotVisit()`
- **逻辑**: 接收文本 → 清洗特殊字符 → 模糊匹配股票代码/名称 → 批量预获取数据 → 生成文本回复

#### stockdataarray.php — 股票数据数组
- **优先级**: ⭐⭐⭐
- **依赖**: stock.php
- **功能**: 将股票数据组织为数组格式（用于API输出）
- **关键函数**: `GetStockDataArray($strSymbols, $arRange)`
- **输出字段**: calibration, date, netvalue, position, symbol_hedge, hedge, CNY

#### stockgroup.php — 股票组合
- **优先级**: ⭐⭐⭐
- **依赖**: stocktrans.php, class/multi_currency.php
- **类**: `StockGroup`(币种金额汇总), `MyStockGroup extends StockGroup`(组合持仓管理)
- **功能**: 投资组合的持仓汇总、多币种盈亏计算

#### stocktrans.php — 交易记录
- **优先级**: ⭐⭐⭐
- **依赖**: 无（依赖在使用时通过stock.php引入）
- **类**: `StockTransaction`(基础交易), `MyStockTransaction extends StockTransaction`(带引用的交易)
- **关键函数**: `AddSqlTransaction()`, `UpdateStockGroupItemTransaction()`, `UpdateStockGroupItem()`

#### stockhis.php — 历史价格/技术分析
- **优先级**: ⭐⭐⭐⭐
- **依赖**: class/ini_file.php
- **类**: `MaxMin`(最大最小值), `StockHistory`(历史价格 + SMA/Bollinger带)
- **功能**: SMA均线计算（5/10/20日）、EMA（50/200日）、Bollinger带估算、二次方程求解、INI配置文件缓存
- **关键函数**: `_estSma()`, `_estBollingerBands()`, `GetQuadraticEquationRoot()`

#### gb2312.php — 编码转换
- **优先级**: ⭐⭐
- **依赖**: sql/sqlgb2312.php
- **功能**: GB2312 → UTF-8 编码转换
- **关键函数**: `GbToUtf8($str)`, `unicode_to_utf8($unicode_str)`

#### telegram.php — Telegram Bot
- **优先级**: ⭐⭐⭐⭐
- **依赖**: stockbot.php, stockdataarray.php
- **类**: `TelegramCallback`(基类), `TelegramStock extends TelegramCallback`
- **功能**: Telegram Bot webhook处理，支持token验证、IP白名单(91.108.5.6)

#### weixin.php — 微信Bot基类
- **优先级**: ⭐⭐⭐⭐
- **依赖**: 无
- **类**: `WeixinCallback`(基类)
- **功能**: 微信公众号消息处理框架（文本/语音/图片/视频/位置/链接/事件）

#### weixincn.php — 微信Bot中文
- **优先级**: ⭐⭐⭐⭐
- **依赖**: weixin.php, stockbot.php
- **类**: `WeixinStock extends WeixinCallback`
- **功能**: 中文股票查询、订阅管理、图片消息处理

#### imagefile.php — 图片生成基类
- **优先级**: ⭐⭐⭐
- **依赖**: debug.php, layout.php(间接)
- **类**: `ImageFile`(GD图片操作), `PageImageFile extends ImageFile`(坐标映射)
- **功能**: 动态生成JPG图表（文本/线/虚线/像素）、坐标轴绘制、折线图

#### benfordimagefile.php — Benford定律图表
- **优先级**: ⭐⭐
- **依赖**: imagefile.php, tutorial/math.php
- **类**: `BenfordImageFile extends PageImageFile`
- **功能**: Benford定律分析图表生成

#### dateimagefile.php — 日期价格图表
- **优先级**: ⭐⭐
- **依赖**: imagefile.php
- **类**: `DateImageFile extends PageImageFile`
- **功能**: 日期-价格对比图表

#### linearimagefile.php — 线性回归图表
- **优先级**: ⭐⭐
- **依赖**: imagefile.php, tutorial/math.php
- **类**: `LinearImageFile extends PageImageFile`
- **功能**: 线性回归散点图+拟合线

#### csvfile.php — CSV文件操作
- **优先级**: ⭐⭐
- **类**: `CsvFile`(读写), `DebugCsvFile extends CsvFile`, `PageCsvFile extends DebugCsvFile`
- **功能**: CSV文件读写、调试CSV、按列读取数据

#### deletestock.php — 股票删除
- **优先级**: ⭐⭐
- **关键函数**: `DeleteStock($strStockId)` — 级联删除股票及关联数据

#### iplookup.php — IP查询
- **优先级**: ⭐⭐⭐
- **类**: `IpLookupAccount extends CommentAccount`
- **功能**: IP地址查询（ipinfo.io）、会员登录记录、评论查询、访客统计

#### bloglink.php — 博客链接
- **功能**: 博客日期链接、照片链接、预设博客标题

#### blogcomments.php — 博客评论页
- **入口文件**: 实例化 `EditCommentAccount`

#### _blogcomments.php — 博客评论展示
- **功能**: 按页面ID展示评论列表

#### _editcommentform.php — 评论编辑表单
- **类**: `EditCommentAccount extends CommentAccount`
- **功能**: 评论编辑/新建表单渲染

#### _submitcomment.php — 评论提交处理
- **类**: `_SubmitCommentAccount extends EditCommentAccount`
- **功能**: 新建/编辑/删除评论 + 邮件通知

#### _submitdelete.php — 管理员删除
- **类**: `_AdminDeleteAccount extends Account`
- **功能**: 删除调试文件、股票分组、访客记录

#### _submitoperation.php — 管理员操作
- **类**: `_AdminOperationAccount extends Account`
- **功能**: 标记爬虫/恶意IP

#### _palmmicromenu.php — 站点菜单
- **功能**: Palmmicro 主站导航菜单（PA6488/PA3288/AR1688/PA1688 等）

#### ElmaBlogcomments.php — GB2312评论兼容
- **功能**: 空的 BlogComments() 函数（兼容旧的GB2312编码页面）

#### test.php — 调试页面
- **功能**: 管理员调试工具，清理数据，显示phpinfo()

#### visitorlogin.php — 访客登录提示
- **功能**: 显示登录/注册链接或已登录用户信息

#### usercomments.php — 用户评论页
- **功能**: 带表格边框的评论展示

#### analytics.php — Google Analytics
- **功能**: 输出 Google Analytics (gtag.js) 代码

#### adsense.php — Google AdSense
- **功能**: 多个 AdSense 广告位输出

#### copyright.php — 版权信息
- **功能**: 页脚版权声明 + 语言切换链接

### 4.2 class/ 目录（3个文件）

#### class/year_month_day.php — 日期时间核心
- **优先级**: ⭐⭐⭐⭐⭐ 核心底层
- **类**: `YearMonthDay`(时间处理), `StringYMD extends YearMonthDay`(字符串日期), `OldestYMD extends StringYMD`(最旧日期), `TickYMD extends YearMonthDay`(带时分), `NowYMD extends TickYMD`(当前时间)
- **关键函数**: `GetNowYMD()`, `GetNowTick()`
- **全局变量**: `$g_now_ymd = new NowYMD()`
- **功能**: 交易日判断、周末/节假日处理、时区管理、文件缓存过期检查

#### class/ini_file.php — INI文件解析
- **类**: `INIFile`
- **功能**: INI格式配置文件读写（用于SMA缓存）

#### class/multi_currency.php — 多币种
- **类**: `MultiCurrency`
- **功能**: CNY/HKD/USD 多币种金额管理，汇率转换

### 4.3 sql/ 目录（26个文件）

#### sql/_sqlcommon.php — SQL构建辅助
- **函数**: `_SqlBuildWhere()`, `_SqlBuildWhereOrArray()`, `_SqlBuildWhereAndArray()`, `_SqlBuildLimit()`, `_SqlOrderByDate()`, `_SqlComposeDateTimeIndex()`

#### sql/sqltable.php — 基础表操作类
- **类**: `TableSql`
- **功能**: 通用 CRUD 操作基类
  - `CreateTable()`, `AlterTable()`, `DeleteById()`, `GetRecordById()`, `GetAll()`, `CountData()`, `InsertId()`, `Update()`

#### sql/sqlkeyname.php — 键值表
- **类**: `KeyNameSql extends TableSql`
- **功能**: string key → id 映射

#### sql/sqlkey.php — 键值ID
- **类**: `KeySql extends KeyNameSql`
- **功能**: 通过string key获取/创建id

#### sql/sqlkeystring.php — 键值字符串
- **类**: `KeyStringSql extends KeySql`
- **功能**: key → string 存储

#### sql/sqlkeytable.php — 键表关联
- **类**: `KeyTableSql extends TableSql`
- **功能**: 外键关联表操作（如 groupitem）

#### sql/sqlval.php — 值存储
- **类**: `ValSql extends KeyTableSql`
- **功能**: key+stock → value 存储

#### sql/sqlint.php — 整数存储
- **类**: `IpIntSql extends IntSql`
- **功能**: IP → int 累计值

#### sql/sqlipaddress.php — IP地址管理
- **类**: `IpAddressSql extends TableSql`
- **功能**: IP地址黑白名单管理

#### sql/sqlmember.php — 会员管理
- **类**: `MemberSql extends TableSql`
- **功能**: 会员CRUD、邮箱/密码查询

#### sql/sqlblog.php — 博客
- **类**: `BlogSql extends TableSql`

#### sql/sqlvisitor.php — 访客统计
- **类**: `VisitorSql extends TableSql`
- **功能**: 页面访问来源/目标记录

#### sql/sqlbotvisitor.php — Bot访客
- **类**: `BotVisitorSql`, `BotMsgSql`, `BotSrcSql`
- **功能**: 微信/Telegram Bot 消息记录

#### sql/sqlstock.php — 股票核心SQL
- **类**: `StockSql extends TableSql`
- **功能**: 股票CRUD、名称查询、代码查询
- **全局函数**: `SqlGetStockId()`, `SqlGetStockSymbol()`, `SqlGetStockName()`, `InitGlobalStockSql()`, `GetStockSql()`

#### sql/sqlstocksymbol.php — 股票代码
- **类**: `StockSymbolSql extends TableSql`
- **功能**: 股票代码符号操作

#### sql/sqlstockgroup.php — 股票分组
- **类**: `StockGroupSql`, `StockGroupItemSql`, `StockTransactionSql`, `GroupItemAmountSql`
- **功能**: 投资分组CRUD

#### sql/sqlstockpair.php — 股票配对
- **类**: `PairSql`
- **函数**: `SqlGetAbPair()`, `SqlGetHaPair()`, `SqlGetAhPair()`, `SqlGetHadrPair()`, `SqlGetAdrhPair()`, `SqlGetBaPair()`, `SqlGetFundPair()`
- **功能**: A/B/AH/ADR/基金配对关系查询

#### sql/sqldailyclose.php — 每日收盘
#### sql/sqldailystring.php — 每日字符串
#### sql/sqldailytime.php — 每日时间
#### sql/sqldate.php — 日期操作
#### sql/sqlgb2312.php — GB2312编码
#### sql/sqlholdings.php — 持仓数据

### 4.4 stock/ 目录（16个文件）

#### stock/stocksymbol.php — 股票代码解析核心
- **优先级**: ⭐⭐⭐⭐⭐
- **类**: `StockSymbol`
- **功能**: 解析股票代码类型（A股/上海/深圳/港股/美股/指数/期货/基金/QDII等）
- **方法**: `IsSymbolA()`, `IsSymbolH()`, `IsFundA()`, `IsSinaFuture()`, `IsEastMoneyForex()`, `IsIndex()`, `GetYahooSymbol()`, `GetDigitA()`, `GetDisplay()`
- **核心逻辑**: 根据代码前缀/长度/特殊格式判断市场类型
- **常量**: 大量 `in_arrayQdii*()`, `in_arraySpyQdii()` 等硬编码数组函数

#### stock/stockref.php — 股票引用基类
- **类**: `StockRef`
- **功能**: 股票实时数据获取/解析/缓存的统一接口

#### stock/mystockref.php — 自定义股票引用
- **类**: `MyStockReference extends StockRef`
- **功能**: 从Sina API获取实时价格、计算涨跌显示

#### stock/yahoostock.php — Yahoo数据
- **函数**: `GetYahooHistoryData()`, `GetYahooNetValueData()`
- **功能**: Yahoo Finance API 数据获取

#### stock/stockprefetch.php — 数据预获取
- **函数**: `PrefetchSinaStockData()`, `GetAllSinaSymbol()`
- **功能**: 批量从Sina获取实时行情

#### stock/cnyref.php — 汇率引用
- **类**: `CnyReference extends StockRef`
- **功能**: 人民币汇率获取（USCNY/HKCNY等）

#### stock/netvalueref.php — 净值引用
- **类**: `NetValueReference extends StockRef`

#### stock/fundref.php — 基金引用
- **类**: `FundReference extends StockRef`
- **功能**: 基金数据获取（净值、溢价、估算）

#### stock/qdiiref.php — QDII基金引用
- **类**: `QdiiReference`, `QdiiHkReference`, `QdiiJpReference`, `QdiiEuReference`
- **功能**: QDII基金净值估算（不同市场的QDII有不同估算逻辑）

#### stock/fundpairref.php — 配对基金引用
- **类**: `FundPairReference`, `AbPairReference`, `AhPairReference`, `AdrPairReference`
- **功能**: 配对基金溢价分析

#### stock/holdingsref.php — 持仓引用
- **类**: `HoldingsReference extends StockRef`
- **功能**: ETF持仓数据获取和分析

#### stock/chinamoney.php — 中国货币网数据
- **函数**: `GetChinaMoney()`
- **功能**: 从chinamoney.com.cn获取人民币汇率数据

#### stock/kraneshares.php — Krane Shares ETF
- **函数**: `GetKraneHoldingsData()`, `GetKranePremiumDiscount()`
- **功能**: Krane Shares ETF 持仓和溢价数据

#### stock/szse.php — 深交所数据
- **函数**: `GetSzseEtfHoldings()`, `GetSzseNetValue()`

#### stock/mysqlref.php — MySQL数据引用
- **类**: `MySqlRef`
- **功能**: 从数据库读取历史数据

### 4.5 test/ 目录（6个文件）

- **_commonupdatestock.php**: 公共股票更新依赖
- **updatechinastock.php**: 更新A股数据（Sina API）
- **updateusstock.php**: 更新美股数据（Yahoo Finance）
- **updategbutf.php**: 更新GB2312编码表
- **updatesecondlisting.php**: 更新二次上市数据
- **gbkuni30.txt**: GBK→Unicode 编码映射表

### 4.6 tutorial/ 目录（5个文件）

- **math.php**: 数学工具（线性回归、Gamma函数、卡方检验、阶乘）
- **primenumber.php**: 质数分解（查表法 + 单遍法）
- **cramersrule.php**: Cramer法则解线性方程组
- **gaussianelimination.php**: 高斯消元法
- **dice.php**: 骰子组合枚举

### 4.7 ui/ 目录（35个文件）

- **htmlelement.php**: HTML元素生成核心（GetDivElement, GetLinkElement, GetImgElement, GetFontElement, GetRemarkElement, GetInfoElement, GetTableElement 等）
- **echohtml.php**: HTML输出封装（EchoHtmlElement, EchoDiv, EchoNewLine 等）
- **echoelement.php**: 元素输出封装
- **link.php**: 链接输出封装
- **plaintext.php**: 纯文本段落
- **table.php**: 表格生成工具（RefEchoTableColumn, EchoTableBegin/End/Head/Body）
- **stocktable.php**: 股票表格展示
- **stockdisp.php**: 股票展示组件（ImgAutoQuote, GetWoodyImgQuote）
- **stockcomm.php**: 股票公共函数（GetStockReferenceArray, RefEchoTableColumn）
- **stocktext.php**: Bot纯文本输出（TextFromStockReference, TextPairRatio）
- **editinputform.php**: 编辑表单
- **commentparagraph.php**: 评论段落（CommentAccount 类）
- **_disp.php/_dispcn.php**: 页面骨架模板
- **_edit.php/_editcn.php**: 编辑页面骨架
- **ahparagraph.php**: AH股比较
- **referenceparagraph.php**: 参考数据段落
- **calibrationhistoryparagraph.php**: 校准历史
- **fundestparagraph.php**: 基金估算
- **fundhistoryparagraph.php**: 基金历史
- **fundlistparagraph.php**: 基金列表
- **fundpurchaseparagraph.php**: 基金申购
- **fundshareparagraph.php**: 基金份额
- **netvaluecloseparagraph.php**: 净值收盘比较
- **netvaluehistoryparagraph.php**: 净值历史
- **portfolioparagraph.php**: 投资组合
- **pricepoolparagraph.php**: 价格池
- **smaparagraph.php**: SMA分析段落
- **stockgroupparagraph.php**: 股票分组
- **stockhistoryparagraph.php**: 股票历史
- **stockparagraph.php**: 股票详情
- **tradingparagraph.php**: 交易段落
- **transactionparagraph.php**: 交易记录
- **imagedisp.php**: 图片展示

---

## 五、模块层级总结

### 5.1 核心逻辑层（最高优先级）

| 文件 | 功能 | Python转化优先级 |
|------|------|----------------|
| `class/year_month_day.php` | 日期时间处理 | P0 |
| `url.php` | URL/HTTP工具 | P0 |
| `debug.php` | 调试/工具 | P0 |
| `sql.php` + `sql/` | 数据库层 | P0 |
| `stock/stocksymbol.php` | 股票代码解析 | P0 |
| `stock.php` | 股票核心聚合 | P0 |
| `account.php` | 用户认证 | P0 |
| `stockbot.php` | Bot查询 | P0 |

### 5.2 数据访问层

| 文件 | 功能 |
|------|------|
| `stock/mystockref.php` | Sina实时数据 |
| `stock/yahoostock.php` | Yahoo历史数据 |
| `stock/stockprefetch.php` | 批量预获取 |
| `stock/chinamoney.php` | 汇率数据 |
| `stock/kraneshares.php` | ETF持仓数据 |
| `stock/szse.php` | 深交所数据 |
| `stock/fundref.php` | 基金净值 |
| `stock/qdiiref.php` | QDII估算 |
| `stock/holdingsref.php` | ETF持仓 |
| `stock/fundpairref.php` | 配对分析 |

### 5.3 UI展示层

35个文件，主要分为：HTML元素生成、表格渲染、段落展示。

### 5.4 工具/辅助层

| 文件 | 功能 |
|------|------|
| `class/ini_file.php` | INI配置文件 |
| `class/multi_currency.php` | 多币种 |
| `gb2312.php` | 编码转换 |
| `csvfile.php` | CSV操作 |
| `regexp.php` | 正则辅助 |
| `tutorial/*.php` | 数学算法 |

---

## 六、全局变量与配置

| 变量/常量 | 值 | 用途 |
|----------|------|------|
| `$g_now_ymd` | `new NowYMD()` | 全局当前时间 |
| `$g_link` | MySQL连接 | 全局数据库连接 |
| `$acct` | Account实例 | 全局账户（每个页面创建） |
| ADMIN_EMAIL | woody@palmmicro.com | 管理员邮箱 |
| DB_DATABASE | n5gl0n39mnyn183l_camman | 数据库名 |
| DB_PASSWORD | (在_private.php) | 数据库密码 |

**私有配置文件**（不在源码中）：
- `_private.php` — 数据库密码等
- `_tgprivate.php` — Telegram Bot Token
- `_wxprivate.php` — 微信Token + 密钥

---

## 七、API/外部接口

| 数据源 | URL模式 | 数据类型 |
|--------|---------|---------|
| 新浪财经 | hq.sinajs.cn/list= | 实时行情（A股/H股/美股/指数/期货/外汇） |
| Yahoo Finance | query1.finance.yahoo.com | 历史价格/实时数据 |
| 中国货币网 | chinamoney.com.cn | 人民币中间价 |
| ipinfo.io | ipinfo.io/{ip}/json | IP地址信息 |
| 雪球 | xueqiu.com | 股票社区链接 |
| 深交所 | szse.cn | ETF持仓/净值 |
| 上交所 | sse.com.cn | ETF申购赎回 |
| Krane Shares | kraneshares.com | ETF持仓/溢价 |
| Google Analytics | googletagmanager.com | 流量统计 |
| Google AdSense | googlesyndication.com | 广告 |
| Telegram | api.telegram.org | Bot API |
| 微信公众号 | mp.weixin.qq.com | 公众号API |

---

## 八、作者设计意图总结

### 8.1 核心意图
作者 Woody 是一个个人投资者+程序员，建立了这个网站来：
1. **管理自己的投资组合**（持仓、交易记录、盈亏分析）
2. **自动化获取市场数据**（实时行情、历史数据、汇率）
3. **分析套利机会**（QDII溢价/折价、AH溢价、AB溢价、ADR溢价）
4. **通过Bot提供服务**（微信/Telegram 自动回复股票查询）
5. **知识分享**（博客+数学工具教程）

### 8.2 设计特点
- **PHP 5.x 时代的面向过程+混合面向对象风格**，大量全局函数
- **所有HTTP请求通过统一的 `url_get_contents()` 封装**（cURL）
- **数据库操作通过 mysqli**，ORM 简单封装
- **中英文双语**通过 URL 后缀切换
- **代码组织**：按功能分层（sql/stock/ui/），但根目录文件较多
- **大量硬编码**：股票列表、QDII分类、URL等
- **私有配置文件**分离：密码/Token 不在源码中

### 8.3 可优化方向（Python转化时考虑）
1. 使用 ORM（SQLAlchemy）替代手写SQL
2. 使用 requests/httpx 替代 cURL
3. 使用 asyncio 异步获取多个股票数据
4. 使用 pandas 替代手写数组处理
5. 配置文件使用 YAML/JSON 替代 INI
6. 使用类/模块组织代码，减少全局函数
7. 数据库密码使用环境变量
8. 前端使用模板引擎（Jinja2）替代 PHP 内嵌HTML

### 8.4 数据驱动架构（核心设计模式）

作者的数据获取采用**"自举"模式**：每次网页访问用上次已入库的数据来估算，同时更新本次数据供下次使用。

#### 8.4.1 两层驱动

| 层级 | 目录 | 触发方式 | 职责 |
|------|------|---------|------|
| **用户请求层** | `php/` | Telegram Bot / 微信 / API 查询 | 新浪实时行情 + 从DB读取慢数据 + 估算净值 |
| **网页展示层** | `woody/res/php/` | 用户访问公开网页 | 更新DB中的慢数据（汇率、Yahoo净值） + 展示HTML页面 |

> ⚠️ **注意**：`GetChinaMoney()`、`YahooUpdateNetValue()`、`UpdateYahooHistoryChart()` 不是"管理后台专用"，而是在**公开网页**中被调用。`_submithistory.php` 是唯一的管理员专用功能（手动提交历史数据）。

#### 8.4.2 162411（华宝油气）完整数据流

以用户访问 `/woody/qdii/SZ162411` 为例（`_qdii.php`）：

```
① StockPrefetchArrayExtendedData()       ← 批量预抓取新浪实时行情（含162411、XOP、杠杆ETF）
② new QdiiReference('SZ162411')          ← 构造函数中自动执行：
   ├─ FundReference::LoadSinaFundData()    ← ③ 从新浪缓存读取162411净值 → 写入netvaluehistory
   └─ EstNetValue()                        ← ④ 估算净值（用DB中已有的旧数据）：
        ├─ AdjustFactor()                   ← ⑤ 从DB读162411净值+XOP净值+汇率 → 计算校准因子
        ├─ CnyReference::GetClose()         ← ⑥ 从DB读汇率（可能是旧数据）
        └─ _getEstNetValue()                ← ⑦ 从DB读XOP净值（可能是旧数据）
⑧ QdiiCreateGroup($arLev)               ← 在EstNetValue()之后才执行：
   ├─ YahooUpdateNetValue(XOP)             ← ⑨ 从Yahoo获取XOP净值 → 写入netvaluehistory（去重+16:55检查）
   ├─ GetChinaMoney()                      ← ⑩ 从中国货币网获取汇率 → 写入netvaluehistory（去重+9:15检查）
   └─ YahooUpdateNetValue(杠杆ETF)         ← ⑪ 杠杆ETF净值 → 写入netvaluehistory
```

#### 8.4.3 关键设计细节

1. **执行顺序**：`EstNetValue()`（②）在 `QdiiCreateGroup()`（⑧）**之前**执行
   - 估算时用的是**之前某次访问已入库的旧数据**
   - `QdiiCreateGroup()` 更新的数据供**下一次**访问使用

2. **去重机制**：
   - `GetChinaMoney()`：`_chinaMoneyNeedData()` 检查DB是否已有该日期数据，有则跳过
   - `YahooUpdateNetValue()`：`$net_sql->GetRecord()` 检查DB是否已有该日期数据，有则跳过
   - `UpdateYahooHistoryChart()`：`$date_sql->ReadDate()` 检查是否已更新，已更新则跳过

3. **时间检查**：
   - `GetChinaMoney()`：`GetHourMinute() < 915` → 9:15前不获取（中国货币网9:15发布）
   - `YahooUpdateNetValue()`：`GetHourMinute() < 1655` → 16:55前不获取（美股16:55后收盘）

4. **数据分类**：
   - **快数据**（每次请求实时获取）：新浪行情（162411净值、XOP实时报价）
   - **慢数据**（每天更新一次）：汇率（中国货币网）、Yahoo净值（美盘收盘后）

5. **`StockPrefetchArrayExtendedData()` 自动扩展**：
   - 传入 `['SZ162411']`，`_getAllSymbolArray()` 自动扩展为 `['SZ162411', 'XOP', 'fx_susdcny', ...]`
   - 确保所有相关symbol的新浪数据都被预抓取

#### 8.4.4 Python复刻对应关系

| PHP函数/类 | Python对应 | 状态 |
|-----------|-----------|------|
| `StockPrefetchArrayExtendedData()` | `stock_prefetch_extended_data()` | ✅ 已有 |
| `QdiiReference` 构造 → `EstNetValue()` | `QdiiReference.__init__()` → `est_net_value()` | ✅ 已有 |
| `QdiiCreateGroup()` | `qdii_create_group()` | ✅ 2026-05-08 |
| `YahooUpdateNetValue()` | `yahoo_update_net_value()` | ✅ 2026-05-08（含去重+16:55检查） |
| `GetChinaMoney()` | `get_china_money()` | ✅ 已有（含去重+时间检查） |
| `SzseGetLofShares()` | `szse_get_lof_shares()` | ✅ 2026-05-08（含去重+9:15检查） |
| `DailyCalibration()` | `daily_calibration()` | ✅ 2026-05-08（杠杆ETF校准） |
| `UpdateYahooHistoryChart()` | `update_history_chart()` | ✅ 已有（YahooStockDB方法） |
| `_qdii.php` 网页入口 | `routes.py` `/stock/<symbol>` + `/api/stock/<symbol>` | ✅ 2026-05-08（已补QDII分支） |

---

## 九、PHP → Python 转化计划

### 9.1 推荐技术栈
- **Web框架**: FastAPI 或 Flask
- **ORM**: SQLAlchemy
- **HTTP请求**: httpx（异步）
- **数据处理**: pandas, numpy
- **图表**: matplotlib / plotly
- **Bot**: python-telegram-bot / wechatpy
- **任务调度**: APScheduler / Celery
- **前端**: Jinja2 模板 + HTMX 或 Vue.js

### 9.2 转化阶段
1. **Phase 1**: 底层工具（url, debug, email → requests, logging）
2. **Phase 2**: 数据层（sql/ → SQLAlchemy models + migrations）
3. **Phase 3**: 股票核心（stock/ → 数据获取 + 解析模块）
4. **Phase 4**: 业务逻辑（account, stockbot, stockgroup → API endpoints）
5. **Phase 5**: UI层（ui/ → Jinja2模板 + API）
6. **Phase 6**: Bot接口（telegram, weixin → Bot框架）

### 9.3 文件映射建议
```
php/           → app/
  class/       → app/core/
  sql/         → app/models/
  stock/       → app/services/
  ui/          → app/templates/
  tutorial/    → app/utils/math/
  test/        → scripts/
```

---

## 十一、res/ 目录分析 — Palmmicro 历史资源页面

> **路径**: `/Users/smithclinton/dev/web-master/res`
> **文件总数**: 26（16 HTML + 7 PHP + 2 JS + 1 子目录 apiguide/）
> **代码总行数**: ~1,581 行
> **与股票分析功能的关系**: ⚠️ **完全无关** — 属于 Palmmicro 硬件公司(VoIP芯片)时代的历史遗留页面

### 11.1 res/ 目录结构

```
res/
├── index.html          — Resources 主页（英文）—— 总索引
├── indexcn.html        — Resources 主页（中文）
├── res.js              — 资源区导航脚本（侧边栏菜单生成）
│
├── format.html         — 网页格式规范（英文）
├── formatcn.html       — 网页格式规范（中文）
├── translation.html    — 翻译指南（英文）
├── translationcn.html  — 翻译指南（中文）
│
├── sip2sip.html        — SIP2SIP VoIP 服务配置（英文）
├── sip2sipcn.html      — SIP2SIP VoIP 服务配置（中文）
├── voipdiscount.html   — VoipDiscount VoIP 服务配置（英文）
├── voipdiscountcn.html — VoipDiscount VoIP 服务配置（中文）
├── voiptalk.html       — VoIPtalk VoIP 服务配置（英文）
├── voiptalkcn.html     — VoIPtalk VoIP 服务配置（中文）
├── sipphone.html       — SIPphone/Gizmo5 服务配置（英文，已停运）
├── sipphonecn.html     — SIPphone/Gizmo5 服务配置（中文）
│
├── 20030111.html       — 2003年1月公司照片（英文）
├── 20030111cn.html     — 2003年1月公司照片（中文）
├── 20081024.html       — 2008年10月办公室照片（英文）
├── 20081024cn.html     — 2008年10月办公室照片（中文）
│
├── apiguide.php        — API 开发指南入口（英文）
├── apiguidecn.php      — API 开发指南入口（中文）
│
└── apiguide/
    ├── apiguide.js     — API指南子导航脚本
    ├── datatype.php    — API 数据类型/命名规则文档（英文）
    ├── datatypecn.php  — API 数据类型/命名规则文档（中文）
    ├── list.php        — T_LIST 链表 API 文档（英文）
    └── listcn.php      — T_LIST 链表 API 文档（中文）
```

### 11.2 文件分类

| 分类 | 文件数 | 文件列表 |
|------|--------|----------|
| VoIP 服务商配置页 | 10 | sip2sip*, voipdiscount*, voiptalk*, sipphone* |
| 公司图片相册 | 4 | 20030111*, 20081024* |
| 网站开发规范 | 4 | format*, translation* |
| API 开发指南 | 6 | apiguide*.php, apiguide/datatype*.php, apiguide/list*.php, apiguide/apiguide.js |
| 目录索引页 | 2 | index*, indexcn* |
| 导航脚本 | 1 | res.js |

### 11.3 逐文件详细分析

#### 11.3.1 index.html / indexcn.html（56/57行）— Resources 总索引页

**功能**: `res/` 目录的总入口页，分类链接到所有子页面。

**内容分区**（英文版）:
1. **Open Source Software**: Asterisk IP PBX, Linphone 软电话, SDCC 编译器(AR1688用), jEdit 编辑器
2. **Service Providers**: SIP2SIP, VoipDiscount+VoipRaider, VoIPtalk
3. **Gallery**: 2008-10-24 和 2003-01-11 公司照片
4. **Web Development**: 翻译规范、页面格式、Google Analytics、Google AdSense
5. **Other Companies**: 前Centrality成员创办的公司 — OLinkStar(北斗星通), UNICORE(和芯星通), Striiv, ZongMu Technology(纵目科技)

**作者意图**: 作为 Palmmicro 硬件公司的资源导航中心，整合开源软件推荐、VoIP服务商配置、技术文档和团队创业史。

**PHP→Python转化**: 无需转化，纯静态HTML页面。如果需要保留，可直接迁移为 Jinja2 模板或保持静态。

---

#### 11.3.2 res.js（37行）— 资源区导航脚本

**功能**: 提供3组侧边栏导航循环函数。

**核心函数** `ResMenu(iTotal, arLoops)`:
- 调用链: `NavBegin()` → `NavMenu0(level+1)` → `NavContinue()` → `NavMenu1(level, "res")` → `NavDirLoop(iTotal, arLoops)` → `NavSwitchLanguage(level+1)` → `NavEnd()`
- 参数: `iTotal`=子项数量, `arLoops`=子项名称数组

**3个快捷导航函数**:
```javascript
NavLoopImage()    → 遍历 ["20030111", "20081024"]           // 图片画廊
NavLoopService()  → 遍历 ["sip2sip","sipphone","voipdiscount","voiptalk"]  // VoIP服务
NavLoopWeb()      → 遍历 ["translation", "format"]           // Web开发
```

**依赖**: `../js/nav.js`（NavBegin/NavMenu0/NavMenu1/NavContinue/NavEnd/NavDirLoop/NavSwitchLanguage）, `../palmmicro.js`（PalmmicroMenu）

**作者意图**: 将导航菜单生成逻辑参数化，3个快捷函数对应3种内容分类的导航菜单。

---

#### 11.3.3 format.html / formatcn.html（53/45行）— 网页格式规范

**功能**: 记录 palmmicro.com 全站统一的排版格式约定。

**字体约定**:
| 场景 | 格式 | 示例 |
|------|------|------|
| 文件名/目录 | `<B>` 粗体 | `C:\SDCC\src\<B>font.c</B>` |
| 函数名 | `<i>` 斜体 | `<i>TaskOutgoingData</i>` |
| 编译器宏 | `<B><i>` 粗斜体 | `<B><i>SYS_IVR_G729</i></B>` |

**颜色约定**:
| 颜色 | 用途 | 示例 |
|------|------|------|
| blue | 设置选项 | Automatically Adjust Clock... |
| gray | 引用/来源 | "There's no importance whatsoever..." |
| magenta | 博客更新日期 | Updated on Feb 13, 2008 |
| olive | 数据类型 | BOOLEAN |
| orange | 版本号 | 1.21 |
| red | 错误/严重警告 | Not a valid Win32 application |

**作者意图**: 作为前端开发规范文档，确保整个网站内容排版风格一致。

---

#### 11.3.4 translation.html / translationcn.html（52/55行）— 翻译指南

**功能**: 英译中翻译规范，定义术语表。

**不翻译的缩写**: API, ASCII, BOM, DSP, LCD, LED, MIPS, RTOS, VoIP（保留英文原文）

**固定翻译词汇表**:
| 英文 | 中文 |
|------|------|
| Character LCD | 字符LCD |
| Bank switching | 存储体切换 |
| IP phone | IP电话 |
| Program flash | 程序闪存 |
| Safe mode | 安全模式 |
| Software API | 软件 API |

**作者意图**: 为双语网站的翻译工作建立统一术语表，避免同一技术术语出现多种翻译版本。

---

#### 11.3.5 VoIP 服务配置页（10个文件，每对约45-62行）

**文件**: sip2sip*, voipdiscount*, voiptalk*, sipphone*（各中英版）

**统一结构**: 网站链接 → SIP配置参数 → 使用说明 → AR1688/PA1688参考设置链接

**配置对比**:

| 服务商 | Registrar | Proxy | STUN | 端口 | 状态 |
|--------|-----------|-------|------|------|------|
| SIP2SIP | sip2sip.info | proxy.sipthor.net | - | 5060 | ✅ 运行中 |
| VoipDiscount | sip.voipdiscount.com | sip.voipdiscount.com | stun.voipdiscount.com | 5060 | ✅ 运行中 |
| VoIPtalk | voiptalk.org | nat.voiptalk.org | - | 5065 | ✅ 运行中 |
| SIPphone | proxy01.sipphone.com | proxy01.sipphone.com | stun01.sipphone.com:3478 | 5060 | ❌ 已停运 |

**特殊功能记录**:
- **SIP2SIP**: SIP Alias 33011668（允许硬件电话直拨数字号码）、Blink+AR1688的speex编解码器兼容性问题
- **VoipDiscount**: 用户名拨号技巧（存电话簿 + 快捷拨号 + #号确认）、VoipRaider共享配置
- **SIPphone**: 明确标注已停运(Discontinued)，链接到博客说明文章

**作者意图**: 为使用 Palmmicro 硬件（PA1688/AR1688 VoIP电话芯片）的用户提供第三方 VoIP 服务商的配置参考文档。

---

#### 11.3.6 公司照片页（4个文件，各约45-54行）

**20030111.html/cn**: 2003年1月11日的 Palmmicro 早期团队照片
- 人物: Woody(作者), Li Jing, Kingon, Li Yajing, Shen Wei, Zheng Shanshan, Andy
- 每人有缩略图(*_s.jpg) + 大图链接

**20081024.html/cn**: 2008年10月24日办公室照片
- 2张照片: 办公室外景(office.jpg) + 内景(office2.jpg)

**作者意图**: 记录公司历史和团队文化。

---

#### 11.3.7 apiguide.php / apiguidecn.php（44行）— API 开发指南入口

**功能**: Palmmicro 软件 API（PA3288/PA6488 方案共用）开发指南的目录页。

**PHP逻辑**: `require("../php/usercomments.php") + UserComments()` — 与 php/ 目录的唯一交互点

**子链接**: 数据类型(datatype.php) + T_LIST链表(list.php)

**作者意图**: 为芯片方案的软件开发者提供 BSD 许可证的开源 API 文档入口。

---

#### 11.3.8 apiguide/apiguide.js（22行）— API 指南子导航

**功能**: API 指南页面的专用侧边栏导航。

**导航路径**: Menu(0级) → res(1级) → apiguide(1级) → [datatype/list](2级)

**语言适配**: 英文显示 "API Guide"，中文通过 `FileTypeCnPhp()` 自动生成文件名后缀。

---

#### 11.3.9 apiguide/datatype.php / datatypecn.php（56行）— API 数据类型文档

**功能**: 定义 Palmmicro 嵌入式 C 代码的统一命名规则（匈牙利命名法变体）。

**命名规则体系**:

| 前缀 | 类型 | 示例 |
|------|------|------|
| `c` | 8位 (UCHAR/char) | `cHardwareLen` |
| `s` | 16位 (USHORT/short) | `sCheckSum` |
| `i` | 32位 (UINT/int) | `iMustBeZero` |
| `b` | BOOLEAN | `bFinAcked` |
| `p` | 指针 | `pcDst[HW_ALEN]`, `*pcBuf` |
| `pp` | 二级指针 | — |
| `r` | 32位寄存器 | `rStall` |
| `rc` | 8位寄存器 | `rc` |
| `t` | 结构体 (T_XXXX_XXXX) | `ptNext` |
| `u` | 联合体 (U_XXXX_XXXX) | — |
| `f` | 函数指针 (F_XXXX_XXXX) | `fCallBack` |
| `c_` | const 常量 | `c_pcLoop[]` |
| `g_` | 全局变量 | `g_iCurrentTime` |
| `_` | 文件内静态 | `_bTimer` |

**关联链接**: PA3288/PA6488 各自的数据结构文档

**作者意图**: 为嵌入式软件开发团队建立严格的代码命名规范，提高可读性和协作效率。

---

#### 11.3.10 apiguide/list.php / listcn.php（48行）— T_LIST 链表 API 文档

**功能**: 介绍 Palmmicro TCP/IP 协议栈中链表框架的使用方法。

**核心数据结构**:
- `T_LIST` — 基础链表（ptNext 为首元素，struct 从 heap malloc）
- `T_BUF_LIST` — 缓冲区链表（buflist.c，最直接的使用示例）
- `F_LIST_ITERATE` — 遍历回调函数类型

**核心函数**:
- `ListIterate()` — 遍历链表所有节点，回调返回 TRUE 中断并返回当前节点指针，否则返回 NULL
- `ListRemoveItem()` — 可在 F_LIST_ITERATE 回调中安全调用的节点删除函数

**作者意图**: 帮助芯片方案的开发者理解并复用 TCP/IP 协议栈的链表组件。

### 11.4 res/ 与 php/ 的交互关系

| 交互点 | 说明 |
|--------|------|
| `require("../php/usercomments.php")` | apiguide.php/cn.php, list.php/cn.php, datatype.php/cn.php 共6个PHP文件 |
| `UserComments()` | 在上述6个文件中调用，渲染用户评论区域 |
| JS依赖 `../js/nav.js`, `../palmmicro.js` | 全部页面共用的导航基础设施 |
| CSS依赖 `../common/style.css` | 全站统一样式表 |
| 图片路径 `../image/image_palmmicro.jpg` | 全站共用Logo |

**结论**: res/ 中只有6个 `.php` 文件通过 `usercomments.php` 与 php/ 目录有依赖关系，其余20个文件为纯静态 HTML/JS。

### 11.5 作者设计意图分析

**Palmmicro 的业务转型历史**:

通过 res/ 目录可以清晰看出作者 Woody 的业务演进：
1. **早期 (2003-2011)**: Palmmicro 是 VoIP IP电话芯片公司（PA1688/AR1688），开发嵌入式C固件
2. **中期**: 维护硬件产品网站，提供技术文档、用户配置指南、API 开发指南
3. **后期 (至今)**: 转型为股票/基金数据分析网站，复用了同一域名和部分基础设施

**res/ 的设计模式**:
- **严格双语**: 每个内容页都有中英文两个版本，命名约定 `xxx.html`(英) + `xxxcn.html`(中)
- **统一模板**: 所有页面共享 HTML 布局（蓝色头部 #049ACC + 绿色侧边栏 #66CC66 + 白色内容区）
- **JS导航系统**: 通过 `res.js` 的参数化菜单生成器，避免在每个页面中硬编码导航
- **SEO优化**: 每页都有 `<meta name="description">` 和结构化标题
- **用户评论**: PHP页面统一嵌入 `UserComments()` 实现评论功能

### 11.6 Python 转化建议

**res/ 目录的转化优先级: ⚠️ 低优先级（与股票分析功能无关）**

| 策略 | 说明 |
|------|------|
| **方案A: 静态迁移** | 纯HTML文件直接保留为静态资源，无需转化为 Python |
| **方案B: Jinja2模板化** | 如果希望统一到 Python 项目中，可转为 Jinja2 模板 |
| **方案C: 归档** | 如果不维护硬件业务页面，可直接归档或删除 |
| **唯一转化点** | `usercomments.php` 的评论功能已在 php/ 分析中覆盖 |

**建议**: 采用方案A或C。res/ 的内容与当前股票分析业务完全无关，是 Palmmicro 硬件公司时代的历史遗产。

---

## 十二、附件

- **完整源码文件**: `full-source-dump.md`（php/ 44,498行 + res/ 追加）
- **文件树JSON**: `file-tree.json`
- **状态**: php/ ✅ 完成 + res/ ✅ 完成 + python/ ✅ 完成 + woody/res/ ✅ 完成 = **全量分析 100% 完成**

---

## 十三、palmmicro-python/ 目录分析 — Python 复刻项目

> **路径**: `/Users/smithclinton/dev/web-master/palmmicro-python`
> **文件总数**: 21 个 Python 文件（+ 配置文件）
> **代码总行数**: ~1,500 行（不含注释/空行）
> **状态**: 🟡 **进行中** — Phase 1 和 Phase 2 已完成，Phase 3 待实现
> **最后更新**: 2026-05-07

### 13.1 项目定位

这是作者正在进行的 PHP→Python 复刻项目，目标是使用现代 Python 技术栈重写原有的股票/基金数据分析系统。与 `python/` 目录下的自动交易系统不同，本项目专注于数据获取、分析和展示层。

### 13.2 推荐技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| Web框架 | FastAPI | 高性能异步框架，自动生成 OpenAPI |
| ORM | SQLAlchemy 2.0 | 类型安全的数据库操作 |
| HTTP请求 | httpx | 异步HTTP客户端 |
| 数据处理 | pandas, numpy | 时间序列分析 |
| 配置管理 | python-dotenv | 环境变量管理 |
| 数据库 | MySQL (pymysql) | 与原项目兼容 |

### 13.3 文件结构

```
palmmicro-python/
├── app/                    # 应用核心代码
│   ├── __init__.py         # 包初始化 ✅
│   ├── database.py         # SQLAlchemy引擎配置 ✅
│   ├── models/             # ORM模型（28张表）✅
│   │   ├── __init__.py     # 导出所有模型
│   │   ├── stock.py        # 股票基础信息
│   │   ├── market_data.py  # 市场数据（17张表）
│   │   ├── trading.py      # 投资组合与交易
│   │   ├── pair.py         # 配对关系
│   │   └── holdings.py     # ETF持仓
│   ├── services/           # 股票服务模块 ✅
│   │   ├── stocksymbol.py  # 股票代码解析与分类
│   │   ├── stockref.py     # 股票引用基类
│   │   ├── mystockref.py   # Sina实时数据获取
│   │   ├── yahoostock.py   # Yahoo Finance历史数据
│   │   ├── stockprefetch.py # 批量数据预获取与缓存
│   │   ├── cnyref.py       # 人民币汇率
│   │   ├── fundref.py      # 基金数据
│   │   ├── qdiiref.py      # QDII基金估算
│   │   ├── holdingsref.py  # ETF持仓数据
│   │   └── chinamoney.py   # 中国货币网数据
│   └── utils/              # 工具模块 ✅
│       ├── __init__.py     # 导出所有工具
│       ├── config_file.py  # INI文件解析
│       ├── currency.py     # 多币种转换
│       ├── date_utils.py   # 日期时间处理
│       ├── email_sender.py # 邮件发送
│       ├── http_client.py  # HTTP请求封装
│       ├── logger.py       # 日志与调试
│       └── regex_patterns.py # 正则辅助
├── .env.example            # 环境变量模板 ✅
├── .gitignore              # Git忽略配置 ✅
├── requirements.txt        # 依赖包 ✅
└── TABLE_MAPPING.md        # 数据库表映射文档 ✅
```

### 13.4 已完成模块

#### 13.4.1 工具层（Phase 1 — ✅ 完成）

| PHP文件 | Python文件 | 状态 | 说明 |
|---------|-----------|------|------|
| `url.php` | `app/utils/http_client.py` | ✅ | HTTP请求、IP提取、URL解析 |
| `debug.php` | `app/utils/logger.py` | ✅ | 日志、浮点数处理、日期格式化 |
| `email.php` | `app/utils/email_sender.py` | ✅ | HTML邮件发送 |
| `regexp.php` | `app/utils/regex_patterns.py` | ✅ | 正则表达式辅助 |
| `class/ini_file.php` | `app/utils/config_file.py` | ✅ | INI文件读写 |
| `class/multi_currency.php` | `app/utils/currency.py` | ✅ | CNY/HKD/USD转换 |
| `class/year_month_day.php` | `app/utils/date_utils.py` | ✅ | 交易日判断、时区处理 |

#### 13.4.2 数据层（Phase 2 — ✅ 完成）

| 模块 | 表数量 | Python文件 | 说明 |
|------|--------|-----------|------|
| 股票基础 | 1 | `stock.py` | Stock（股票代码/名称） |
| 市场数据 | 17 | `market_data.py` | 历史价格、EMA、校准、基金净值等 |
| 投资组合 | 5 | `trading.py` | 组合、持仓、交易记录 |
| 配对关系 | 4 | `pair.py` | AB/AH/ADR/基金配对 |
| ETF持仓 | 1 | `holdings.py` | 成分股持仓比例 |

**已丢弃的表（12张）**: 用户系统(member/profile)、博客(page/pagecomment)、爬虫防护(ipaddress/stocktick)、GB2312编码等

### 13.5 与 PHP 原版的差异对比

#### 13.5.1 架构改进

| 维度 | PHP原版 | Python复刻 |
|------|---------|-----------|
| 数据库 | mysqli + 手写SQL | SQLAlchemy ORM |
| HTTP请求 | cURL + 同步 | httpx + 异步 |
| 配置管理 | 私有PHP文件 | 环境变量 + .env |
| 代码组织 | 全局函数为主 | 类/模块组织 |
| 用户系统 | 多用户支持 | 单用户（移除member_id） |

#### 13.5.2 关键设计变更

**1. stockgroup 表简化**
```
PHP:  stockgroup(id, member_id, groupname)  UNIQUE(member_id, groupname)
Python: stockgroup(id, groupname)            UNIQUE(groupname)
```

**2. 配对表独立化**
- PHP：4种配对共用 `PairSql` 基类
- Python：`AbPair`, `AhPair`, `AdrPair`, `FundPair` 各自独立模型

**3. 日期处理**
- PHP：依赖全局 `$g_now_ymd`
- Python：使用 `zoneinfo` + `datetime`，时区感知

#### 13.5.3 性能优化

| 优化项 | PHP实现 | Python实现 |
|--------|---------|-----------|
| 并发请求 | 串行 cURL | 异步 httpx |
| 数据库连接 | 每次请求新建 | 连接池 |
| 数据缓存 | 文件缓存（60秒间隔） | 文件缓存（60秒间隔） ✅ 2026-05-08 |

### 13.6 新增功能和改进

| 功能 | 说明 | 状态 |
|------|------|------|
| 类型提示 | 全量类型标注，IDE智能提示 | ✅ |
| 异步支持 | HTTP请求支持异步调用 | ✅ |
| FastAPI集成 | 自动生成API文档和客户端 | ⏳ 待实现 |
| 依赖管理 | pip + requirements.txt | ✅ |
| 配置安全 | 敏感信息使用环境变量 | ✅ |

### 13.7 待完成任务清单

#### Phase 3：股票核心模块（✅ 已完成）

| 优先级 | PHP文件 | Python文件 | 功能 | 状态 |
|--------|---------|-----------|------|------|
| P0 | `stock/stocksymbol.php` | `app/services/stocksymbol.py` | 股票代码解析（A股/H股/美股/基金分类） | ✅ |
| P0 | `stock/stockref.php` | `app/services/stockref.py` | 股票引用基类 | ✅ |
| P0 | `stock/mystockref.php` | `app/services/mystockref.py` | Sina实时数据获取 | ✅ |
| P0 | `stock/yahoostock.php` | `app/services/yahoostock.py` | Yahoo Finance数据 | ✅ |
| P0 | `stock/stockprefetch.php` | `app/services/stockprefetch.py` | 批量数据预获取 | ✅ |
| P1 | `stock/cnyref.php` | `app/services/cnyref.py` | 人民币汇率 | ✅ |
| P1 | `stock/fundref.php` | `app/services/fundref.py` | 基金引用 | ✅ |
| P1 | `stock/qdiiref.php` | `app/services/qdiiref.py` | QDII基金估算 | ✅ |
| P1 | `stock/holdingsref.php` | `app/services/holdingsref.py` | ETF持仓数据 | ✅ |
| P1 | `stock/chinamoney.php` | `app/services/chinamoney.py` | 中国货币网数据 | ✅ |

#### Phase 4：业务逻辑（进行中）

| 优先级 | PHP文件 | Python文件 | 功能 | 状态 |
|--------|---------|-----------|------|------|
| P0 | `stock.php` | `app/services/stock.py` | 股票核心聚合层 | ✅ |
| P0 | `stockbot.php` | `app/services/stockbot.py` | Bot股票查询逻辑 | ✅ |
| P1 | `stockgroup.php` | `app/services/stockgroup.py` | 投资组合管理 | ✅ |
| P1 | `stocktrans.php` | `app/services/stocktrans.py` | 交易记录处理 | ✅ |
| P1 | `stockhis.php` | `app/services/stockhis.py` | 历史价格与技术分析 | ✅ |

#### Phase 5：UI展示层（进行中）

| 优先级 | PHP文件 | Python文件 | 功能 | 状态 |
|--------|---------|-----------|------|------|
| P0 | `ui/stocktext.php` | `app/ui/stocktext.py` | 股票数据文本格式化 | ✅ |
| P0 | `ui/htmlelement.php` | `app/ui/stockhtml.py` | HTML元素生成工具 | ✅ |
| P1 | Flask应用 | `app/__init__.py`, `app/routes.py` | Web应用框架 | ✅ |
| P1 | Jinja2模板 | `app/templates/` | 页面模板渲染 | ✅ |

#### Phase 6：Bot接口层（完成）

| 优先级 | PHP文件 | Python文件 | 功能 | 状态 |
|--------|---------|-----------|------|------|
| P0 | `telegram.php` | `app/bot/telegram.py` | Telegram Bot | ✅ |
| P0 | `weixin.php` | `app/bot/weixin.py` | 微信公众号 | ✅ |

---

### 🎉 项目完成总结

所有核心功能模块已完成！

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 1: 工具层 | ✅ | 7个工具模块 |
| Phase 2: 数据层 | ✅ | 28张数据库表模型 |
| Phase 3: 股票核心服务 | ✅ | 10个服务模块 |
| Phase 4: 业务逻辑层 | ✅ | 5个业务模块 |
| Phase 5: UI展示层 | ✅ | Flask Web应用 |
| Phase 6: Bot接口层 | ✅ | Telegram + 微信 |

### 13.8 依赖包清单

```txt
sqlalchemy>=2.0      # ORM
pymysql>=1.1         # MySQL驱动
cryptography>=42.0   # 加密
python-dotenv>=1.0   # 环境变量
httpx>=0.27          # HTTP客户端（异步）
pandas>=2.2          # 数据处理（待添加）
numpy>=1.26          # 数值计算（待添加）
```

---

## 十四、python/ 目录分析 — 作者已有的自动交易系统

> **路径**: `/Users/smithclinton/dev/web-master/python`
> **文件总数**: 6 个 Python 文件（+ 2 个 VS 项目文件）
> **总行数**: ~350 行（不含注释/空行）
> **状态**: ⚠️ **极其重要** — 这是作者自己开始写的 PHP→Python 转化，是实际可运行的**自动交易系统**

### 13.1 文件清单

```
python/
├── TWS/
│   ├── TWS.py          — Interactive Brokers 自动交易核心（~425行）
│   ├── palmmicro.py    — 数据获取 + 套利计算 + 消息推送（~390行）
│   ├── nyc_time.py     — 时区工具（NYSE/深圳时区判断）（~30行）
│   ├── _tgprivate.py   — 私有配置（TOKEN等，不在源码中）
│   ├── TWS.pyproj      — Visual Studio 项目文件
│   └── TWS.sln         — Visual Studio 解决方案
├── auto/
│   ├── main.py         — 测试入口（年化收益率计算 + 数据拉取）
│   ├── telegram.py     — Telegram Bot 消息发送封装
│   └── _mytoken.py     — 私有TOKEN配置
└── jokes.py            — 笑话脚本（无关）
```

### 13.2 TWS.py — 自动交易核心（最关键文件）

**功能**: 连接 Interactive Brokers TWS (Trader Workstation)，实现**实时自动交易**。

**核心架构**:
- `MyEWrapper(EWrapper)` — IB API 回调处理器
- `MyEClient(EClient)` — IB API 客户端封装
- 连接 `127.0.0.1:7497`（TWS 本地端口）

**交易标的与策略**:

| 标的 | 类型 | 策略 |
|------|------|------|
| KWEB, GLD, IEO, QQQ, SLV, SPY, USO, XBI, XLY, XOP | ETF | 中国A股开盘时交易 |
| SPX | 指数 | 美股开盘时监控 |
| MES+合约月份 | 期货 | SPX的4倍迷你期货，基于SPX校准 |

**交易逻辑**（基于价格阶梯的网格交易）:
1. **GetOrderArray(arPrice, iSize, iBuyPos, iSellPos)** — 定义价格阶梯数组
2. **AskPriceTrade()** — Ask价 > 买入目标价 → 下买单
3. **BidPriceTrade()** — Bid价 < 卖出目标价 → 下卖单
4. **orderStatus()** — 买单成交后自动挂卖单，卖单成交后自动挂买单（循环交易）
5. **VWAP监控** — 当VWAP价格穿过卖出目标时触发条件单

**QDII套利监控**（中国市场开盘时）:
```python
self.arQDII = {'SH501018', 'SZ160719', 'SZ160723', 'SZ161116', 'SZ161125', 'SZ161127',
               'SZ161129', 'SZ161130', 'SZ161226', 'SZ162411', 'SZ162415', 'SZ164701',
               'SZ164906', 'SZ165513'}
```
- 通过 `_CheckPriceAndSize()` 检测QDII ETF的买卖价和规模
- 调用 `palmmicro.CalcCalibrationArbitrage()` 和 `CalcHoldingsArbitrage()` 计算套利空间
- 满足阈值时发送消息通知（微信/Telegram）

**MES期货校准**:
- 基于 SPX 指数实时价格，通过 `Calibration` 类计算 MES 期货的合理价格
- 当偏差 > 0.01 时自动调整挂单价格

### 13.3 palmmicro.py — 数据获取与套利计算

**功能**: 获取行情数据、计算套利空间、发送消息通知。

**数据获取**:
- `_fetchSinaData()` — 通过新浪财经API获取人民币汇率(fx_susdcny)、白银期货(nf_AG0)、A股行情
- `_fetchPalmmicroData()` — 调用自己的 `palmmicro.com/php/telegram.php` 获取QDII基金详细数据（持仓、净值、校准系数等）

**套利计算**:
- `CalcCalibrationArbitrage()` — 基于校准系数的套利计算
  - 核心公式: `fRatio = fHedgePrice / fMktPrice - 1.0`（溢价率）
  - 支持2级杠杆（如纳斯达克100 ETF 挂钩沪深300 ETF）
- `CalcHoldingsArbitrage()` — 基于持仓明细的套利计算
  - 遍历基金持有的每只成分股，按比例计算对冲所需股数
  - 支持 `^` 开头的虚拟代码（如 `^SPY`）

**辅助函数**:
- `fund_adjust_position()` / `fund_reverse_adjust_position()` — 基金仓位系数正反算
- `qdii_get_peer_val()` — QDII等价值计算
- `_get_hedge_quantity()` — 对冲数量计算（向下取整到100股）

**消息推送**:
- `SendTelegramMsg()` — Telegram群消息（chat_id: -1001346320717）
- `SendWechatMsg()` — 企业微信Webhook推送
- 16个独立的微信推送频道（每个QDII基金一个），每个频道6秒节流
- 消息去重 + 批量合并（每6秒发送一次）

**基金费率硬编码**:
```python
def StockGetFundFeeRatio(strSymbol):
    case 'SZ160416': return 0.0      # 免赎回费
    case 'SZ161116': return 0.0
    case 'SZ161226': return 0.01     # 1%
    case 'SH501018': return 0.012    # 1.2%
    case 'SZ161815': return 0.016    # 1.6%
    default: return 0.015            # 1.5%
```

### 13.4 nyc_time.py — 时区工具

**功能**: 判断美股/中国市场的开盘状态。
- `GetExchangeTime('NYSE')` — 返回纽约时间HHMM，自动处理夏令时（3月第2个周日→11月第1个周日）
- `GetExchangeTime('SZSE')` — 返回北京时间HHMM
- `GetBeijingTimeDisplay()` — 返回北京时间字符串

### 13.5 auto/telegram.py — Telegram Bot封装

**功能**: 构造Telegram消息格式，调用 `palmmicro.com/php/telegram.php` 发送。
- `FetchPalmmicroData(strSymbols)` — 发送股票代码到telegram.php获取数据
- `post_json_array_to_telegram()` — 通用Telegram JSON发送

### 13.6 与 PHP 代码的对应关系

| Python 函数 | PHP 对应 |
|------------|----------|
| `_fetchSinaData()` | `php/stock/yahoostock.php` (新浪部分) |
| `_fetchPalmmicroData()` | `php/telegram.php` (Bot查询) |
| `CalcCalibrationArbitrage()` | `php/stock/qdiiref.php` (校准套利) |
| `CalcHoldingsArbitrage()` | `php/stock/holdingsref.php` (持仓套利) |
| `StockGetFundFeeRatio()` | `php/stock/fundref.php` (基金费率) |
| `SendTelegramMsg()` | `php/telegram.php` |
| `SendWechatMsg()` | `php/weixincn.php` |
| `Calibration` 类 | `php/stock/qdiiref.php` 校准逻辑 |

### 13.7 作者设计意图

**这是一个正在运行的实时自动交易系统**，核心特点：
1. **混合架构**: Python做交易执行 + 数据监控，PHP做数据服务端（telegram.php作为API）
2. **渐进式转化**: 作者没有一次性重写，而是用Python调用PHP API的方式逐步迁移
3. **实盘运行**: 代码中包含具体的期货合约月份(202606/202609)、具体的QDII基金代码列表、具体的chat_id
4. **风控意识**: 每个微信频道6秒节流、批量合并消息、订单状态跟踪

---

## 十四、woody/res/ 目录深入分析 — 前端展示页面层

> **路径**: `/Users/smithclinton/dev/web-master/woody/res`
> **文件总数**: 246 个 PHP 文件（~9,779 行）
> **状态**: ⚠️ **关键目录** — 这是所有股票分析功能的**实际前端展示层**

### 14.1 架构模式

**极度精简的MVC模式**:

```
woody/res/xxxcn.php (入口，仅2行)
  ↓ require('php/_mystockgroup.php')
  ↓ require('../../php/ui/_dispcn.php')
  ↓
php/_mystockgroup.php (Controller，含GetTitle/GetMetaDescription/EchoAll)
  ↓ require('../../php/stock.php') 等业务逻辑
  ↓ require('../../php/ui/xxxparagraph.php') 等UI组件
  ↓
php/ui/_dispcn.php (Layout模板，输出HTML框架)
  ↓ 调用 GetTitle(), EchoAll(), _LayoutTopLeft(), _LayoutBottom()
```

绝大多数页面入口文件只有 **2行代码**：
```php
<?php
require('php/_mystockgroup.php');
require('../../php/ui/_dispcn.php');
?>
```

### 14.2 页面分类

#### 14.2.1 配对交易分析页（核心功能）
| 页面 | 说明 |
|------|------|
| `ahcomparecn.php` | A/H 股溢价对比（A股 vs H股） |
| `abcomparecn.php` | A/B 股溢价对比（A股 vs B股） |
| `adrhcomparecn.php` | ADR/H 股溢价对比（美股ADR vs H股） |
| `ahhistorycn.php` | AH溢价历史走势 |

#### 14.2.2 QDII基金分类页（批量展示）
| 页面 | 分类 | 基金示例 |
|------|------|----------|
| `qdiicn.php` | 全部QDII | SH501018, SZ160719... |
| `qdiieucn.php` | 欧洲方向 | SZ161116, SZ161125... |
| `qdiihkcn.php` | 香港方向 | SH501018, SZ160723... |
| `qdiijpcn.php` | 日本方向 | SZ159866 |
| `qdiimixcn.php` | 混合方向 | SZ161127, SZ161130... |

#### 14.2.3 行业/主题基金页
| 页面 | 说明 |
|------|------|
| `biotechcn.php` | 生物科技（XBI对标 SZ159502/SZ161127） |
| `qqqfundcn.php` | 纳斯达克100（QQQ对标） |
| `spyfundcn.php` | 标普500（SPY对标） |
| `oilfundcn.php` | 石油基金（USO对标） |
| `hangsengcn.php` | 恒生指数（^HSI对标） |
| `hsharescn.php` | H股板块 |
| `hstechcn.php` | 恒生科技 |
| `chinaindexcn.php` | 中国指数 |
| `chinainternetcn.php` | 中概互联网 |
| `chinafuturecn.php` | 中国期货 |
| `commoditycn.php` | 大宗商品 |
| `mscius50cn.php` | MSCI美国50 |

#### 14.2.4 单只基金详情页（~150+个）
每个QDII/LOF基金都有一个独立页面：
- `sh501018cn.php`, `sh501025cn.php`, ... `sh513990cn.php`（上交所基金）
- `sz159501cn.php`, `sz159502cn.php`, ... `sz165513cn.php`（深交所基金）

#### 14.2.5 投资组合管理页
| 页面 | 说明 |
|------|------|
| `mystockcn.php` | 个股详情（行情+交易+分组+盈亏） |
| `mystockgroupcn.php` | 自选股组（所有基金/股票的聚合展示） |
| `myportfoliocn.php` | 投资组合总览 |
| `mystocktransactioncn.php` | 交易记录 |
| `fundaccountcn.php` | 基金账户 |

#### 14.2.6 数据管理页（管理员）
| 页面 | 说明 |
|------|------|
| `editcalibrationcn.php` | 编辑校准数据 |
| `editfundcn.php` | 编辑基金信息 |
| `editnetvaluecn.php` | 编辑净值 |
| `editpremiumcn.php` | 编辑溢价 |
| `editstockahcn.php` | 编辑AH对 |
| `editstockadrcn.php` | 编辑ADR对 |
| `editstockgroupcn.php` | 编辑股票分组 |
| `editstocktransactioncn.php` | 编辑交易记录 |
| `submittransaction.php` | 提交交易 |
| `submithistory.php` | 提交历史数据 |
| `submitholdings.php` | 提交持仓 |
| `submitdividend.php` | 提交分红 |
| `uploadfile.php` | 上传文件 |

#### 14.2.7 特殊功能页
| 页面 | 说明 |
|------|------|
| `btbondcn.php` | 可转债分析 |
| `cateyescn.php` | 猫眼（作者的自有产品） |
| `autotractorcn.php` | 自动拖拉机（网格交易工具） |
| `overnightcn.php` | 夜盘LOF |
| `lofcn.php` | LOF基金列表 |
| `calibrationhistorycn.php` | 校准历史 |
| `netvaluehistorycn.php` | 净值历史 |
| `fundlistcn.php` | 基金列表 |
| `thanousparadoxcn.php` | Thano's Paradox（哲学/数学） |

### 14.3 php/ 子目录辅助文件（49个）

**核心控制器**:
- `_mystockgroup.php` — 最核心的控制器，处理所有分类页的渲染逻辑
- `_mystock.php` — 个股详情控制器
- `_stock.php` — 股票基础工具函数集
- `_stockgroup.php` — 投资分组类(GroupAccount)

**辅助文件按功能**:
| 分类 | 文件 |
|------|------|
| 布局 | `_res.php`, `_woodymenu.php` |
| 表单 | `_edittransactionform.php`, `_editgroupform.php`, `_editmergeform.php`, `_editstockoptionform.php` |
| 数据更新 | `_updateholdings.php`, `_updateinvesconetvalue.php`, `_uploadfile.php` |
| CSV导入 | `_holdingscsvfile.php`, `_kraneholdingscsv.php`, `_yahoohistorycsv.php`, `_spdrnetvaluexls.php` |
| 持仓获取 | `_sseholdings.php`, `_szseholdings.php`, `_etfholdings.php` |
| 特殊页面 | `_qdii.php`, `_qdiieu.php`, `_qdiihk.php`, `_qdiijp.php`, `_qdiimix.php`, `_chinafuture.php`, `_chinaindex.php`, `_ahhistory.php` |

### 14.4 btbond/ 和 cateyes/ 子目录

- **btbond/** — 可转债分析（coinwifi.php, php/ 子目录）
- **cateyes/** — 猫眼产品（alexandrite389, baozi, emerald594 — 宝石产品页面）

### 14.5 与 php/ 目录的依赖关系

```
woody/res/php/_stock.php
  → ../../php/stock.php          (股票核心)
  → ../../php/stocktrans.php     (交易)
  → ../../php/csvfile.php        (CSV工具)
  → ../../php/ui/*paragraph.php  (所有UI组件)
  → ../../php/sql/*              (所有SQL操作)
```

**woody/res 是 php/ 的消费者**，它不定义任何业务逻辑，纯粹调用 php/ 中的函数和类来渲染页面。

### 14.6 Python 转化建议

**woody/res 的转化策略**: 在 Python 项目中用 **API + 前端框架** 替代：
1. `php/` → Python 后端 API（FastAPI）
2. `woody/res/` → React/Vue 前端或 Jinja2 模板
3. 不需要逐文件翻译，因为每个页面只是2行 require + 控制器输出

---

## 十五、项目全景总结

### 目录重要性分级

| 优先级 | 目录 | 文件数 | 说明 |
|--------|------|--------|------|
| 🔴 最高 | `php/` | 135 | 后端核心逻辑（已全量分析） |
| 🔴 最高 | `python/` | 6 | 已有的Python转化代码（自动交易系统） |
| 🟡 高 | `woody/res/` | 246 | 前端展示页面层 |
| 🟡 高 | `account/` | 59 | 用户账户系统 |
| ⚪ 低 | `res/` | 26 | 硬件公司历史页面（已分析） |
| ⚪ 无 | 其余目录 | ~700 | 博客/芯片文档/C++工具等 |

### 转化路线图

```
阶段0（已完成）: python/TWS/ — 自动交易系统已在运行
阶段1: php/核心 → Python API
阶段2: woody/res/ → 前端页面
阶段3: account/ → 用户系统
```

---

## 十六、palmmicro-python 详细实现文档

> **最后更新**: 2026-05-08
> **状态**: 🟡 进行中 — 核心功能已完成，数据源层完善中
> **框架**: Flask + SQLAlchemy

### 16.1 项目结构总览

```
palmmicro-python/
├── app/                          # 应用核心
│   ├── __init__.py               # Flask应用工厂 ✅
│   ├── database.py               # SQLAlchemy配置 ✅
│   ├── routes.py                 # 路由定义 ✅
│   │
│   ├── models/                   # 数据模型层 ✅
│   │   ├── __init__.py           # 模型导出
│   │   ├── stock.py              # Stock（1张表）
│   │   ├── market_data.py        # 市场数据（17张表）
│   │   ├── trading.py            # 交易组合（5张表）
│   │   ├── pair.py               # 配对关系（4张表）
│   │   └── holdings.py           # ETF持仓（1张表）
│   │
│   ├── services/                 # 服务层
│   │   ├── stocksymbol.py        # 股票代码解析 ✅
│   │   ├── stockref.py           # 股票引用基类 ✅
│   │   ├── mystockref.py         # Sina实时数据 ✅
│   │   ├── yahoostock.py         # Yahoo历史数据 ✅
│   │   ├── stockprefetch.py      # 批量预获取 ✅
│   │   ├── stock.py              # 股票核心聚合 ✅
│   │   ├── stockbot.py           # Bot查询逻辑 ✅
│   │   ├── stockgroup.py         # 投资组合 ✅
│   │   ├── stockhis.py           # 历史价格 ✅
│   │   ├── stocktrans.py         # 交易记录 ✅
│   │   ├── cnyref.py             # 人民币汇率 ✅
│   │   ├── fundref.py            # 基金净值 ✅
│   │   ├── qdiiref.py            # QDII估算 ✅
│   │   ├── holdingsref.py        # ETF持仓 ⏳
│   │   └── chinamoney.py         # 中国货币网 ✅
│   │
│   ├── bot/                      # Bot接口层 ✅
│   │   ├── telegram.py           # Telegram Bot
│   │   └── weixin.py             # 微信公众号
│   │
│   ├── ui/                       # UI组件层
│   │   ├── stockhtml.py          # HTML展示 ⏳
│   │   └── stocktext.py          # 文本格式化 ✅
│   │
│   ├── templates/                # Jinja2模板
│   │   ├── base.html             # 基础布局 ✅
│   │   ├── _table.html           # 可复用表格组件（render_table宏）✅
│   │   ├── index.html            # 首页 ✅
│   │   ├── stock_detail.html     # 股票详情页（含QDII+数据明细链接）✅
│   │   ├── calibration_history.html # 校准记录页 ✅
│   │   ├── netvalue_history.html # 净值历史页（通用:XOP/USCNY/基金）✅
│   │   └── about.html            # 关于页 ✅
│   │
│   ├── static/css/               # 静态资源 ✅
│   │   └── style.css
│   │
│   └── utils/                    # 工具层 ✅
│       ├── config_file.py        # INI配置
│       ├── currency.py           # 多币种
│       ├── date_utils.py         # 日期处理
│       ├── email_sender.py       # 邮件发送
│       ├── http_client.py        # HTTP客户端
│       ├── logger.py             # 日志
│       └── regex_patterns.py     # 正则辅助
│
├── scripts/                      # 脚本
│   ├── init_db.py                # 数据库初始化 ✅
│   └── init_db.sql               # SQL脚本 ✅
│
├── .env                          # 环境变量
├── .env.example                  # 环境变量模板 ✅
├── requirements.txt              # 依赖包 ✅
├── test_services.py              # 测试文件 ✅
├── DATABASE_SETUP.md             # 数据库设置 ✅
└── TABLE_MAPPING.md              # 表映射文档 ✅
```

### 16.2 实现进度详情

#### 16.2.1 Phase 1: 工具层 ✅ 完成

| 文件 | PHP来源 | 行数 | 功能描述 |
|------|---------|------|----------|
| `http_client.py` | `url.php` | ~80 | HTTP请求封装、IP提取、URL解析 |
| `logger.py` | `debug.php` | ~60 | 日志记录、浮点数处理 |
| `email_sender.py` | `email.php` | ~40 | HTML邮件发送 |
| `regex_patterns.py` | `regexp.php` | ~50 | 正则表达式辅助函数 |
| `config_file.py` | `class/ini_file.php` | ~45 | INI配置文件读写 |
| `currency.py` | `class/multi_currency.py` | ~70 | CNY/HKD/USD多币种转换 |
| `date_utils.py` | `class/year_month_day.php` | ~100 | 交易日判断、时区处理 |

**关键改进**:
- 使用 `zoneinfo` 替代 PHP 的时区处理
- 支持 `async/await` 异步HTTP请求
- 类型提示全覆盖

#### 16.2.2 Phase 2: 数据模型层 ✅ 完成

**28张数据库表映射**:

| 分类 | 文件 | 表数量 | 主要表 |
|------|------|--------|--------|
| 股票基础 | `stock.py` | 1 | stock |
| 市场数据 | `market_data.py` | 17 | stockhistory, stockema50/200, netvaluehistory, calibration, fundest... |
| 投资组合 | `trading.py` | 5 | stockgroup, stockgroupitem, stocktransaction, groupitemamount |
| 配对关系 | `pair.py` | 4 | abpair, ahpair, adrpair, fundpair |
| ETF持仓 | `holdings.py` | 1 | holdings |

**已丢弃的12张表**:
- 用户系统: member, profile
- 博客系统: page, pagecomment
- 爬虫防护: ipaddress, stocktick
- 编码转换: gb2312
- Bot日志: telegrambot, wechatbot, botmsg, botsrc, botvisitor

#### 16.2.3 Phase 3: 股票核心服务 ✅ 完成

| 文件 | PHP来源 | 核心类/函数 | 功能 |
|------|---------|------------|------|
| `stocksymbol.py` | `stock/stocksymbol.php` | `StockSymbol` | 股票代码解析与分类（A股/H股/美股/基金/期货） |
| `stockref.py` | `stock/stockref.php` | `StockRef`, `StockRefFactory` | 股票引用抽象基类 |
| `mystockref.py` | `stock/mystockref.php` | `MyStockReference` | Sina Finance实时数据获取 |
| `yahoostock.py` | `stock/yahoostock.php` | `YahooStock`, `YahooStockDB` | Yahoo Finance历史数据（JSON chart API + 数据库持久化） |
| `stockprefetch.py` | `stock/stockprefetch.py` | `prefetch_sina_stock_data()` | 批量数据预获取 |
| `stock.py` | `stock.php` | `stock_get_reference()` | 股票核心聚合层 |

**StockSymbol 类核心方法**:
```python
class StockSymbol:
    def is_symbol_a(self) -> bool      # 判断A股
    def is_symbol_h(self) -> bool      # 判断H股
    def is_symbol_us(self) -> bool     # 判断美股
    def is_fund_a(self) -> bool        # 判断A股基金
    def is_fund_qdii(self) -> bool     # 判断QDII基金
    def get_yahoo_symbol(self) -> str  # 获取Yahoo格式代码
    def get_sina_symbol(self) -> str   # 获取Sina格式代码
    def get_type(self) -> str          # 获取类型字符串
```

**MyStockReference 数据解析**:
- 支持A股/H股/美股/指数/期货/外汇等多种数据格式
- 自动识别Sina返回的数据结构
- 异步批量获取支持

#### 16.2.4 Phase 4: 业务逻辑层 ✅ 完成

| 文件 | PHP来源 | 功能 |
|------|---------|------|
| `stockbot.py` | `stockbot.php` | Bot股票查询逻辑，支持模糊匹配 |
| `stockgroup.py` | `stockgroup.py` | 投资组合管理，多币种汇总 |
| `stockhis.py` | `stockhis.py` | 历史价格、SMA/EMA计算 |
| `stocktrans.py` | `stocktrans.py` | 交易记录处理 |

#### 16.2.5 Phase 5: Bot接口层 ✅ 完成

**Telegram Bot** (`bot/telegram.py`):
```python
class TelegramStock(TelegramCallback):
    def on_text(self, text: str, message_id: str, chat_id: str) -> str:
        # 处理股票查询，返回格式化文本
```

**微信公众号** (`bot/weixin.py`):
```python
class WeixinStock(WeixinCallback):
    def on_text(self, text: str) -> str:
        # 处理微信消息，返回XML响应
```

#### 16.2.6 Phase 6: UI层 ⏳ 进行中

| 文件 | 状态 | 说明 |
|------|------|------|
| `ui/stocktext.py` | ✅ | 股票数据文本格式化 |
| `ui/stockhtml.py` | ⏳ | HTML表格/图表生成 |
| `templates/base.html` | ✅ | 基础布局模板 |
| `templates/_table.html` | ✅ | 可复用表格组件（render_table/render_simple_table宏） |
| `templates/index.html` | ✅ | 首页 |
| `templates/stock_detail.html` | ✅ | 股票详情页（含QDII估算+校准记录+数据明细超链接） |
| `templates/calibration_history.html` | ✅ | 校准历史页（日期/校准值/时间/次数） |
| `templates/netvalue_history.html` | ✅ | 净值历史页（通用:XOP收盘价/汇率中间价/基金净值，动态精度） |
| `templates/about.html` | ✅ | 关于页 |

#### 16.2.7 Phase 7: 数据源层 ⏳ 进行中

| 文件 | 状态 | PHP来源 | 功能 |
|------|------|---------|------|
| `cnyref.py` | ✅ | `stock/cnyref.php` + `stock/chinamoney.php` | 人民币汇率（中国货币网官方中间价 + 数据库存储） |
| `fundref.py` | ✅ | `stock/fundref.php` | 基金净值获取（Sina + 数据库存储） |
| `qdiiref.py` | ✅ | `stock/qdiiref.php` | QDII基金净值估算（继承FundReference + 数据库存储） |
| `holdingsref.py` | ⏳ | `stock/holdingsref.php` | ETF持仓数据获取 |
| `chinamoney.py` | ⏳ | `stock/chinamoney.py` | 中国货币网数据 |

### 16.3 与PHP原版的差异对比

#### 16.3.1 架构差异

| 维度 | PHP原版 | Python复刻 |
|------|---------|-----------|
| **框架** | 原生PHP | Flask |
| **数据库** | mysqli + 手写SQL | SQLAlchemy ORM |
| **HTTP请求** | cURL + 同步 | requests/httpx + 异步支持 |
| **配置管理** | `_private.php` 私有文件 | `.env` 环境变量 |
| **代码组织** | 全局函数为主 | 类/模块组织 |
| **类型系统** | 无类型提示 | 全量类型标注 |
| **用户系统** | 多用户(member_id) | 单用户(移除member_id) |

#### 16.3.2 数据库设计变更

**stockgroup表简化**:
```
PHP:  stockgroup(id, member_id, groupname)  UNIQUE(member_id, groupname)
Python: stockgroup(id, groupname)            UNIQUE(groupname)
```

**配对表独立化**:
```
PHP:  PairSql 基类，通过参数区分类型
Python: AbPair, AhPair, AdrPair, FundPair 各自独立模型
```

#### 16.3.3 功能差异

| 功能 | PHP实现 | Python实现 |
|------|---------|-----------|
| 实时行情 | Sina API同步请求 | Sina API + 异步批量 |
| 历史数据 | Yahoo Finance JSON chart API → 存入MySQL | Yahoo Finance JSON chart API → 存入MySQL ✅ |
| 汇率获取 | 中国货币网官方中间价 → 存入MySQL | 中国货币网官方中间价 → 存入MySQL ✅ |
| 基金净值 | Sina Finance → 存入MySQL netvaluehistory | Sina Finance → 存入MySQL netvaluehistory ✅ 2026-05-08 |
| QDII估算 | 多数据源计算 + 数据库存储 | 多数据源计算 + 数据库存储 ✅ 2026-05-08 |
| 用户认证 | Session + Cookie | 移除（单用户） |
| 爬虫防护 | IP黑白名单 | 移除 |

### 16.4 新增功能和改进

| 功能 | 说明 | 状态 |
|------|------|------|
| **类型提示** | 全量类型标注，IDE智能提示 | ✅ |
| **异步支持** | HTTP请求支持async/await | ✅ |
| **API文档** | Flask路由自动生成API | ✅ |
| **依赖管理** | pip + requirements.txt | ✅ |
| **配置安全** | 敏感信息使用环境变量 | ✅ |
| **测试支持** | pytest测试框架 | ✅ |
| **日志系统** | Python logging模块 | ✅ |
| **错误处理** | 异常捕获和日志记录 | ✅ |
| **YahooStock DB持久化** | 与PHP一致使用JSON chart API + 数据库存储 | ✅ 2026-05-08 |
| **文件缓存限流** | 与PHP一致60秒间隔防止重复请求（debug_json） | ✅ 2026-05-08 |
| **汇率中国货币网** | 与PHP一致使用中国货币网官方中间价 + 数据库存储 | ✅ 2026-05-08 |
| **基金净值存储** | 与PHP一致使用Sina Finance + netvaluehistory数据库存储 | ✅ 2026-05-08 |
| **QDII估算重构** | 与PHP一致继承FundReference + 数据库存储 + XOP标的 | ✅ 2026-05-08 |
| **数据驱动架构** | 与PHP一致自举模式：yahoo_update_net_value + qdii_create_group + 路由QDII分支 | ✅ 2026-05-08 |
| **完整数据驱动** | 与PHP完全一致：szse_get_lof_shares + daily_calibration + 所有功能整合 | ✅ 2026-05-08 |
| **校准记录加权平均** | `CalibrationSql::WriteDailyAverage()` 完全对齐：(n×old+new)/(n+1)，阈值MIN_FLOAT_VAL=0.0000005 | ✅ 2026-05-10 |
| **校准记录表格组件** | `_table.html` 可复用宏组件（render_table/render_simple_table），支持标题链接、外框线、列宽/对齐/颜色 | ✅ 2026-05-10 |
| **校准历史页面** | `/stock/<symbol>/calibration` HTML页 + `/api/stock/<symbol>/calibration` JSON API，显示日期/校准值/时间/次数4列 | ✅ 2026-05-10 |
| **数据明细超链接** | XOP收盘价 + 美元人民币汇率中间价 + 基金净值记录三个页面，对应作者 YahooNetValueLink/CnyRefLink/NetValueHistoryLink | ✅ 2026-05-10 |
| **净值历史通用模板** | `netvalue_history.html` 通用模板 + HTML/API双路由，按股票类型动态决定精度（FundA→3, Forex→4, 默认→2） | ✅ 2026-05-10 |
| **前端精度统一** | 全部数值展示与作者PHP对齐：校准因子4位/基金净值3位/XOP价格2位/汇率4位/仓位2位 | ✅ 2026-05-10 |
| **is_forex()修复** | 补充作者 IsEastMoneyForex() 符号集(USCNY/EUCNY/JPCNY/HKCNY)，修复汇率精度错误 | ✅ 2026-05-10 |

### 16.5 待完成任务清单

#### 高优先级

| ID | 模块 | 任务 | PHP来源 |
|----|------|------|---------|
| PT-001 | `services/cnyref.py` | ~~完善人民币汇率获取逻辑~~ ✅ 已完成 | `stock/cnyref.php` |
| PT-003 | `services/qdiiref.py` | ~~完善QDII基金净值估算~~ ✅ 已完成 | `stock/qdiiref.php` |
| PT-003 | `services/qdiiref.py` | 完善QDII基金净值估算 | `stock/qdiiref.php` |

#### 中优先级

| ID | 模块 | 任务 | PHP来源 |
|----|------|------|---------|
| PT-004 | `services/holdingsref.py` | 完善ETF持仓数据获取 | `stock/holdingsref.php` |
| PT-005 | `services/chinamoney.py` | ~~完善中国货币网数据获取~~ ✅ 已合并到cnyref.py | `stock/chinamoney.php` |
| PT-006 | `ui/stockhtml.py` | 完善HTML展示组件 | `ui/stocktable.php` |

#### 校准记录审计发现（2026-05-10）

对作者PHP校准代码完整链路审计后，以下细节我们尚未实现：

| 缺失项 | 作者实现 | PHP来源 | 优先级 |
|--------|---------|---------|--------|
| **净值列（第5列）** | FundA类型基金显示 `$ref->GetNetValue($strDate)`，从netvaluehistory表读取该日实际净值，精度NETVALUE_PRECISION=4 | `calibrationhistoryparagraph.php:11` | P1 |
| **对冲值列（第6列）** | `StockCalcHedge($fCalibration, $fPosition) = $fCalibration / $fPosition`，颜色navy | `stock.php:384-387` + `stocktable.php:95-101` | P1 |
| **基金倍数映射** | SH518800/SH518880/SZ159934/SZ159937→×1000; SZ159985→×10; SZ161226→×15; 默认×1 | `calibrationhistoryparagraph.php:46-65` | P1 |
| **FundA判断** | 仅FundA类型显示净值+对冲值两列，非FundA只显示4列 | `calibrationhistoryparagraph.php:34-43` | P1 |
| **时间格式GetHM()** | `substr($strHMS, 0, 5)` 取前5位(HH:MM) | `debug.php:116-118` | P2 |

**已对齐项**：

| 特性 | 状态 |
|------|------|
| 加权平均公式 `(n×old+new)/(n+1)` | ✅ 完全一致 |
| num递增逻辑 | ✅ 一致 |
| time每次更新 | ✅ 一致 |
| 值相同跳过（阈值MIN_FLOAT_VAL=0.0000005） | ✅ 已统一 |
| 表名 calibrationhistory | ✅ 一致 |
| 字段 stock_id/date/close/time/num | ✅ 一致 |

#### 低优先级

| ID | 模块 | 任务 | 说明 |
|----|------|------|------|
| PT-007 | `templates/` | 扩展更多页面模板 | 基金列表、组合详情等 |
| PT-008 | `tests/` | 添加单元测试 | pytest测试用例 |
| PT-009 | `docs/` | API文档生成 | Swagger/OpenAPI |

### 16.6 同步更新机制

**每次修改Python代码时，需同步更新以下文档**:

1. **file-tree.json** — 更新文件状态和进度
2. **design-doc.md** — 更新本章节内容
3. **TABLE_MAPPING.md** — 如涉及数据库模型变更

**更新模板**:

```markdown
### [日期] 更新记录

**修改文件**: `app/services/xxx.py`

**修改内容**:
- 新增功能A
- 修复bug B
- 优化性能C

**PHP对应**: `stock/xxx.php`

**测试结果**: ✅ 通过 / ❌ 失败

**待办事项**:
- [ ] 任务1
- [ ] 任务2
```

---

## 附录：文档维护指南

### A. 文档结构

| 文件 | 用途 | 更新时机 |
|------|------|----------|
| `file-tree.json` | 项目文件结构元数据 | 新增/删除文件时 |
| `design-doc.md` | 设计文档（本文档） | 修改代码逻辑时 |
| `TABLE_MAPPING.md` | 数据库表映射 | 修改模型时 |
| `full-source-dump.md` | PHP源码完整导出 | 仅参考，不更新 |

### B. 状态标记说明

| 标记 | 含义 |
|------|------|
| ✅ | 已完成 |
| ⏳ | 进行中 |
| ❌ | 已放弃 |
| 🔴 | 高优先级 |
| 🟡 | 中优先级 |
| ⚪ | 低优先级 |

### C. 版本历史

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-05-08 | v1.8 | 完整数据驱动：szse_get_lof_shares() + daily_calibration() + 所有功能整合，与PHP完全一致 |
| 2026-05-08 | v1.7 | 数据驱动架构实现：yahoo_update_net_value() + qdii_create_group() + routes.py QDII分支 |
| 2026-05-08 | v1.6 | qdiiref.py重写：继承FundReference + 数据库存储 + 正确使用XOP标的，与PHP原版一致 |
| 2026-05-08 | v1.5 | fundref.py重写：改用Sina Finance + netvaluehistory数据库存储，与PHP原版一致 |
| 2026-05-08 | v1.4 | cnyref.py重写：改用中国货币网官方中间价 + 数据库存储，与PHP原版一致 |
| 2026-05-08 | v1.3 | 新增 utils/file_cache.py 文件缓存限流（60秒间隔），与PHP原版一致 |
| 2026-05-08 | v1.2 | yahoostock.py重构：改用JSON chart API + 数据库持久化，与PHP原版一致 |
| 2026-05-08 | v1.1 | 新增第十六章Python详细实现文档，建立同步更新机制 |
| 2026-05-08 | v1.0 | 初始版本，PHP全量分析完成 |
| 2026-05-10 | v1.9 | 校准记录功能完善：加权平均实现与PHP对齐、MIN_FLOAT_VAL阈值统一、表格组件优化（外框线+仅显示最新1行+去掉箭头）、作者代码完整审计（发现缺少净值/对冲值列及倍数映射） |
| 2026-05-10 | v2.0 | 三个数据明细超链接页面（XOP收盘价/美元人民币汇率中间价/基金净值记录）、netvalue_history模板（修复Jinja2 zip过滤器错误，改用Python端预构建cells结构）、前端展示精度统一对齐作者PHP规则（校准因子4位/基金净值3位/XOP价格2位/汇率4位/仓位2位）、is_forex()修复补充EastMoney外汇符号集(USCNY/EUCNY/JPCNY/HKCNY) |

---

## 十七、前端展示精度规范

> **建立日期**: 2026-05-10
> **来源**: 作者 PHP 源码 `debug.php`, `stock.php`, `stocksymbol.php`, `calibrationhistoryparagraph.php`, `fundestparagraph.php`, `stocktext.php`

### 17.1 精度规则总表

所有数值展示精度必须与作者 PHP 原版完全一致。核心常量定义：

```php
// debug.php
define('NETVALUE_PRECISION', 4);    // 净值类数据默认精度
define('FLOAT_PRECISION', 6);       // 浮点存储精度
define('MIN_FLOAT_VAL', 0.0000005); // 最小浮点差值阈值
```

### 17.2 按字段分类的精度

| 字段 | 精度 | PHP 实现方式 | Python 对应 |
|------|------|-------------|------------|
| **校准因子 (factor)** | **4位小数** | `number_format($fCalibration, NETVALUE_PRECISION)` → `number_format($val, 4)` | `'%.4f'|format(val)` 或 `round(val, 4)` |
| **基金净值 (162411等)** | **3位小数** | `$ref->GetPriceDisplay()` → `$this->GetPrecision()` → `IsFundA()` 返回 3 | `sym.get_precision()` → `is_fund_a()` 返回 3 |
| **XOP 收盘价 / 股票价格** | **2位小数** | `GetPrecision()` 默认返回 2 | `sym.get_precision()` 默认返回 2 |
| **汇率 USD/CNY (USCNY)** | **4位小数** | `GetPrecision()` → `IsForex()` 返回 4 | `sym.get_precision()` → `is_forex()` 返回 4 |
| **仓位 Position** | **2位小数** | `number_format($fPosition, 2)` | `'%.2f'|format(pos)` |
| **涨幅百分比 Change%** | **2位小数** | `number_format(floatval($str), 2).'%'` | `'%.2f'|format(pct)` |
| **份额 Shares** | **2位小数** | `number_format($fShare, 2)` | `round(val, 2)` |
| **比价 Ratio** | **4位小数** | `GetRatioDisplay($fVal, $iPrecision = 4)` | — |

### 17.3 GetPrecision() 判定逻辑

作者 PHP `StockSymbol::GetPrecision()` 的完整判定链：

```
IsFundA() || IsSinaFund() || IsStockB()  → 3    （A股基金/B股）
IsForex()                                 → 4    （外汇: USCNY/EUCNY/JPCNY/HKCNY + FX_前缀）
默认                                      → 2    （美股/A股/H股/指数/期货）
```

Python 对应 `StockSymbol.get_precision()`：

```python
def get_precision(self) -> int:
    if self.is_fund_a():
        return 3
    if self.is_forex():
        return 4
    return 2
```

### 17.4 IsForex() 符号集

作者 PHP 的外汇判定由两部分组成：

```php
// stocksymbol.php:729-733
function IsForex()
{
    if ($this->IsEastMoneyForex())  return true;   // 东方财富外汇符号
    if ($this->IsSinaForex())        return true;   // 新浪外汇符号(FX_前缀)
    return false;
}

// stocksymbol.php:694-705
function IsEastMoneyForex()
{
    switch ($this->strSymbol)
    {
    case 'USCNY': case 'EUCNY': case 'JPCNY': case 'HKCNY':
        return true;
    }
    return false;
}
```

Python 对应实现：

```python
def is_forex(self) -> bool:
    eastmoney_forex = {'USCNY', 'EUCNY', 'JPCNY', 'HKCNY'}
    if s in eastmoney_forex:
        return True
    return s.startswith('FX_')
```

> ⚠️ **历史问题**: 早期 Python 版本 `is_forex()` 只识别 `FX_` 前缀，遗漏了 EastMoney 符号集（特别是 `USCNY`），导致汇率页面精度错误地显示为2位而非4位。已于 2026-05-10 修复。

### 17.5 各页面的精度应用

#### QDII 详情页 (`stock_detail.html`)

| 显示项 | 格式 | 示例 |
|--------|------|------|
| 估算净值 (official_net_value) | `%.3f` | 0.880 |
| 公允净值 (fair_net_value) | `%.3f` | 0.880 |
| 校准值 (factor) | `%.4f` | 1286.5329 |
| 仓位 (position) | `%.2f` | 0.95 |

对应 PHP 来源：
- 估算净值/公允净值: `fundestparagraph.php:19,25` → `$ref->GetPriceDisplay($fOfficialPrice)` → 内部调用 `GetNetValueDisplay()` → `NETVALUE_PRECISION=4` 但通过 `GetPrecision()` 走 FundA 分支得 3
- 校准值: `calibrationhistoryparagraph.php:8` → `number_format($fCalibration, NETVALUE_PRECISION)` = 4位
- 仓位: `fundestparagraph.php:135` → `number_format($fPosition, 2)`

#### 净值历史页 (`netvalue_history.html`)

精度由 `StockSymbol.get_precision()` 动态决定：

| symbol | 类型 | precision | 示例值 |
|--------|------|-----------|--------|
| XOP | 美股ETF | 2 | 165.16 |
| USCNY | 外汇(EastMoney) | 4 | 6.8502 |
| 162411 | A股基金(FundA) | 3 | 0.884 |

#### 校准记录页 (`calibration_history.html`)

| 列 | 格式 | 说明 |
|----|------|------|
| 日期 | `%Y-%m-%d` | 2026-05-07 |
| 校准值 | `%.4f` | 1286.5329 |
| 时间 | `HH:MM` | 15:30 |
| 次数 | 整数 | 1 |

### 17.6 Jinja2 模板注意事项

Jinja2 默认**不提供** `zip` 过滤器。当需要在模板中合并两个列表时，有两种解决方案：

1. **推荐**: 在 Python 路由函数中预构建 cells 结构（如 `_get_calibration_history()` 和 `netvalue_history()` 的做法），避免在模板中使用复杂操作
2. **备选**: 自定义 Jinja2 过滤器注册 `zip`，但不推荐增加不必要的复杂度

本次 netvalue_history.html 的教训：最初使用了 `data.records \| map(attribute='date') \| zip(data.records \| map(attribute='close'))` 导致 `TemplateRuntimeError: No filter named 'zip' found`，后改为在 routes.py 中预构建 `rows`（含 cells 结构）解决。

---

## 十八、数据明细超链接页面

> **建立日期**: 2026-05-10
> **来源**: 作者 PHP `externallink.php` (GetYahooNetValueLink / GetCnyRefLink / GetNetValueHistoryLink), `stocklink.php`

### 18.1 功能说明

在 QDII 基金详情页（如 162411）中，添加三个数据明细超链接，用户可点击查看各数据源的历史记录：

| 链接文本 | 路由 | 对应作者链接 | 数据来源 |
|----------|------|-------------|---------|
| XOP 收盘价 | `/stock/XOP/netvalue` | `GetYahooNetValueLink("XOP")` — 标注"估算标的" | netvaluehistory 表 (stock_id=XOP) |
| 美元人民币汇率中间价 | `/stock/USCNY/netvalue` | `GetCnyRefLink("USCNY")` — 标注"外汇参考" | netvaluehistory 表 (stock_id=USCNY) |
| 基金净值记录 | `/stock/{symbol}/netvalue` | `GetNetValueHistoryLink(symbol)` — 标注"净值记录" | netvaluehistory 表 (stock_id=基金) |

### 18.2 作者归类逻辑

作者在 PHP 中对这三个数据的归类方式：

- **XOP** → `YahooNetValueLink` 类别，标注为 **"估算标的"**（QDII 基金跟踪的海外 ETF）
- **USCNY** → `CnyRefLink` 类别，标注为 **"外汇参考"**（人民币汇率中间价）
- **基金净值** → `NetValueHistoryLink` 类别，标注为 **"净值记录"**（基金自身的历史净值）

### 18.3 实现细节

#### 路由定义 (`routes.py`)

```python
@bp.route('/stock/<symbol>/netvalue')
def netvalue_history(symbol):
    """Net value history page (通用: XOP/USCNY/基金净值)."""
    # 1. 通过 StockSymbol 查找 stock 记录
    # 2. 查询 NetValueHistory 表（按 date DESC，限制500条）
    # 3. 按 get_precision() 决定格式化精度
    # 4. 在 Python 端预构建 rows (cells 结构)，避免 Jinja2 zip 问题
    # 5. 渲染 netvalue_history.html 模板

@bp.route('/api/stock/<symbol>/netvalue')
def api_netvalue(symbol):
    """Get net value history as JSON."""
    # 同上逻辑，返回 JSON 格式（含 precision 字段）
```

#### 模板 (`netvalue_history.html`)

通用净值历史模板，适用于任何 stock symbol：
- 标题根据 symbol 自动映射（XOP→"XOP收盘价", USCNY→"汇率中间价", 其他→"{name}净值记录"）
- 使用 `_table.html` 的 `render_table` 宏渲染表格
- 显示两列：日期 + 数值（数值精度动态决定）
- 底部显示总记录数和返回链接

#### 详情页入口 (`stock_detail.html`)

在 QDII 信息区域底部、更新时间上方，插入"数据明细"区块：

```html
<div class="data-links">
    <h4>数据明细</h4>
    <div class="link-row">
        <a href="/stock/XOP/netvalue">XOP 收盘价</a> |
        <a href="/stock/USCNY/netvalue">美元人民币汇率中间价</a> |
        <a href="/stock/{{ data.symbol }}/netvalue">基金净值记录</a>
    </div>
</div>
```

### 18.4 已知数据量

| symbol | 记录数 | 数据来源 | 最近日期 |
|--------|--------|---------|---------|
| XOP | 237 | akshare `ak.stock_us_daily(symbol="XOP", adjust="")` | 2026-05-09 |
| USCNY | 206 | 中国货币网官方中间价 | 2026-05-08 |
| 162411 | 360 | Sina Finance 基金净值 | 2026-05-07 |
