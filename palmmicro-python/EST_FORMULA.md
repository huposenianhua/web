# 官方EST计算公式文档

> **基于PHP源码分析**: `fundpairref.php`, `qdiiref.php`, `fundhistoryparagraph.php`, `stock.php`
> **适用基金**: 162411（华宝油气，QDII-LOF基金，跟踪XOP）

---

## 一、校准因子（factor）计算

### 1.1 触发时机

`DailyCalibration()` — 每日净值发布后运行一次

**PHP源码位置**: `fundpairref.php:184-202`

### 1.2 中文公式

```
factor_T = XOP_收盘价_T × CNY汇率_T ÷ NAV_162411_T
```

### 1.3 代码公式

```php
// fundpairref.php:196 — DailyCalibration()
$fFactor = $this->CalcFactor($fPairNetValue, floatval($strNetValue), $strDate);

// fundpairref.php:209-218 — CalcFactor()
function CalcFactor($fPairNetValue, $fNetValue, $strDate)
{
    $fCny = $this->cny_ref->GetVal($strDate);
    if ($this->IsSymbolA())                              // A股QDII
        $fNetValue /= $fCny;                             // adjusted_NAV = NAV / CNY
    else
        $fNetValue *= $fCny;
    return $fPairNetValue / $fNetValue;                  // factor = XOP / adjusted_NV
}

// 等价于 (A股):
// qdiiref.php:3 — QdiiGetCalibration() 反推验证
// factor = XOP × CNY ÷ NAV
```

### 1.4 数据来源与时间

| 变量 | 数据源 | 时间 |
|------|--------|------|
| **XOP_收盘价** | `pair_ref->GetNetValue(date)` → **netvaluehistory表** (Yahoo) | **北京时间T日**<br>(= 美东T-1日收盘) |
| **CNY汇率** | `cny_ref->GetVal(date)` → **USCNY netvaluehistory表** | **北京时间T日** |
| **NAV_162411** | `net_sql->GetCloseNow(id)` → **netvaluehistory表** | **北京时间T日**<br>(当日发布的净值) |
| **写入目标** | `calibrationhistory.WriteDaily(id, T, factor)` | — |

### 1.5 写入条件

```php
// fundpairref.php:189-190
$strDate = $net_sql->GetDateNow($strStockId);           // 净值最新日期
if ($strDate == $cal_sql->GetDateNow($strStockId))      // 已校准过则跳过
    return;

// fundpairref.php:192-201 — 有净值且有XOP数据才校准
if ($strNetValue = $net_sql->GetCloseNow($strStockId))
{
    if ($fPairNetValue = $this->pair_ref->GetNetValue($strDate))
    {
        $fFactor = ...;                                  // 计算factor
        $cal_sql->WriteDaily($strStockId, $strDate, strval($fFactor));
        $this->LoadCalibration();                        // 重新加载到内存
    }
}
```

---

## 二、官方EST计算

### 2.1 触发时机

`GetOfficialNetValue()` — 每次请求页面时实时计算

**PHP源码位置**: `fundpairref.php:234-250`

**存库条件**: 美股时间 < 20:55 且净值尚未发布时写入fundest表

### 2.2 中文公式

```
raw_EST = XOP_收盘价_D × CNY汇率_D ÷ factor_最新

EST = position × raw_EST + (1 - position) × base_val
```

### 2.3 代码公式

```php
// fundpairref.php:234-250 — GetOfficialNetValue()
$strOfficialDate = $this->pair_ref->GetDate();            // D = XOP最新日期
$fCny = $this->cny_ref ? $this->cny_ref->GetVal($strOfficialDate) : false;
$fEst = $this->pair_ref->GetNetValue($strOfficialDate);   // XOP_D (netvaluehistory)

$fVal = $this->EstFromPair($fEst, $fCny);                 // 计算EST

if ($this->pair_ref->GetHourMinute() < 2055)              // 美股 < 20:55
    StockUpdateEstResult($this->GetStockId(), $fVal, $strOfficialDate); // 存入fundest
return $fVal;

// fundpairref.php:80-88 — EstFromPair()
function EstFromPair($fPairVal = false, $fCny = false)
{
    if ($fPairVal == false) $fPairVal = $this->pair_ref->GetPrice();
    if ($fCny == false)     $fCny     = $this->GetDefaultCny();

    if ($this->IsSymbolA())                                 // A股QDII (162411)
        $fVal = QdiiGetVal($fPairVal, $fCny, $this->fFactor);
    else
        $fVal = ($fPairVal / $fCny) / $this->fFactor;
    return FundAdjustPosition($this->GetPosition(), $fVal,
           $this->fLastCalibrationVal ?: $fVal);
}

// qdiiref.php:8-11 — QdiiGetVal (A股专用)
function QdiiGetVal($fEst, $fCny, $fFactor)
{
    return $fEst * $fCny / $fFactor;
}

// fundref.php — FundAdjustPosition (仓位调整)
function FundAdjustPosition($fRatio, $fVal, $fOldVal)
{
    return $fRatio * $fVal + (1 - $fRatio) * $fOldVal;
}
```

### 2.4 数据来源与时间

| 变量 | 数据源 | 时间 | 说明 |
|------|--------|------|------|
| **XOP_收盘价** | `pair_ref->GetNetValue(D)` → netvaluehistory (Yahoo) | **北京时间D日** | 最新可用XOP日期 |
| **CNY汇率** | `cny_ref->GetVal(D)` → USCNY netvaluehistory | **北京时间D日** | 与XOP同日 |
| **factor_最新** | `LoadCalibration()` → calibrationhistory **最新一条** | **北京时间T日** | T ≤ D，通常为D或D-1 |
| **position** | `GetPosition()` → **fundposition表** | 常量 | LOF默认 **0.95**，其他默认1.0 |
| **base_val** | `fLastCalibrationVal` → **lastcalibration表** | **北京时间T日** | 校准时的162411净值/价格 |

### 2.5 核心要点：factor是「之前某次校准」的结果

```
Day T-1 晚间: DailyCalibration() 运行
  factor_{T-1} = XOP_{T-1} × CNY_{T-1} ÷ NAV_{T-1}
  → 写入 calibrationhistory → fFactor 更新为 factor_{T-1}

Day T 白天: 用户访问页面 → GetOfficialNetValue()
  D = XOP最新日期 (通常是T或T-1，取决于美股是否开盘)
  EST = XOP_D × CNY_D ÷ fFactor          ← fFactor仍是 factor_{T-1}！
       ≠ NAV_D                              ← 这是预测值，不是恒等式！

★ 关键：factor不是用当天数据算的，而是之前某次校准的结果
  所以 EST 是真正的跨日预测值，与实际NAV有合理偏差
```

### 2.6 存入fundest的条件

```php
// fundpairref.php:248
if ($this->pair_ref->GetHourMinute() < 2055)   // 美股时间 < 20:55
    StockUpdateEstResult(stock_id, EST, official_date);

// stock.php:148-156 — StockUpdateEstResult()
function StockUpdateEstResult($strStockId, $fNetValue, $strDate)
{
    $net_sql = GetNetValueHistorySql();
    // ★ 只有净值还没发布时才写入（净值为预估值的替代）
    if ($net_sql->GetRecord($strStockId, $strDate) == false)
    {
        $fund_est_sql = GetFundEstSql();
        $fund_est_sql->WriteDaily($strStockId, $strDate, strval($fNetValue));
    }
    // 净值已发布则不覆盖，保持之前的预估值用于误差对比
}
```

---

## 三、误差计算

### 3.1 触发时机

premium页面展示每行数据时

**PHP源码位置**: `fundhistoryparagraph.php:23`, `stock.php:121-124`

### 3.2 中文公式

```
误差 = ( 官方EST ÷ 官方NAV - 1 ) × 100%
```

### 3.3 代码公式

```php
// fundhistoryparagraph.php:23 — premium页面每行
$ar[] = $ref->GetPercentageDisplay($fNetValue, $fEstValue);

// stock.php:121-124 — StockGetPercentage()
function StockGetPercentage($fDivisor, $fDividend)
{
    if (abs($fDivisor) > MIN_FLOAT_VAL)
        return ($fDividend / $fDivisor - 1.0) * 100.0;
    // 调用: StockGetPercentage(NAV, EST) = (EST / NAV - 1) × 100
    return 0.0;
}
```

### 3.4 数据来源与时间

| 变量 | 数据源 | 时间 |
|------|--------|------|
| **官方NAV** | `netvaluehistory.close` | **北京时间nav_date** |
| **官方EST** | `fundest.close`（预存值） | **北京时间nav_date** |

### 3.5 QDII基金的日期映射（重要！）

```php
// fundhistoryparagraph.php:39-42 — _echoHistoryTableData()
$bSameDay = UseSameDayNetValue($ref);             // QDII → false
$strDate = $bSameDay ? $arHistory['date']          // 非QDII: 用当天 his_date
          : $his_sql->GetDatePrev(id, date);       // ★ QDII: 用前一日 nav_date!

// 然后:
$nav   = $net_sql->GetClose(id, strDate);          // NAV at nav_date (= T-1)
$est   = $fund_est_sql->GetRecord(id, strDate);     // EST at nav_date (= T-1)
$error = GetPercentageDisplay(NAV, EST);           // 用同一 nav_date 的两个值比
```

| 页面显示日期 | 查询NAV/EST的日期 | 说明 |
|-------------|-----------------|------|
| **his_date (T)** | **nav_date (T-1)** | QDII基金：用前一交易日净值匹配当日价格 |

---

## 四、完整时序图（以2026-05-07为例）

```
美东时间          北京时间          事件                        数据变化
─────────       ──────────       ──────                      ────────

05-06 16:00  →   05-07 04:00     XOP收盘 169.3300             netvaluehistory(XOP, 05-06)=169.33
                                   SSGA发布NAV 169.2997         xop_nav_ssga(05-06)=169.30

05-07 09:30  →   05-07 09:30     162411开盘                  -

05-07 15:00  →   05-07 15:00     162411收盘 0.892             dailystock(162411, 05-07)=0.892

05-07 ????:??→   05-07 晚间      发布NAV 0.9021               netvaluehistory(162411, 05-07)=0.9021
                 ↓
                 DailyCalibration():
                   factor = 169.33 × 6.8487 ÷ 0.9021 = 1286.53
                   calibrationhistory(05-07, 1286.53)

05-08 04:00  →   05-08 04:00     XOP收盘 166.06               netvaluehistory(XOP, 05-07)=166.06
                 ↓
                 用户访问页面:
                   GetOfficialNetValue():
                     D = 05-07 (XOP最新日期)
                     XOP_D = 166.06, CNY_D = ???
                     fFactor = 1286.53 (最新=05-07那条!)
                     raw = 166.06 × CNY ÷ 1286.53 = 0.8837
                     EST  = 0.95 × 0.8837 + 0.05 × base = 0.8837
                     美股 < 20:55 → fundest(05-07, 0.8837)

premium页面 05-08行:
  显示日期=05-08, 价格=0.875
  nav_date = 05-07 (QDII前一日)
  NAV = 0.9021 (netvaluehistory at 05-07)
  EST = 0.8837 (fundest at 05-07)
  误差 = 0.8837 / 0.9021 - 1 = -2.04%

premium页面 05-07行:
  显示日期=05-07, 价格=0.892
  nav_date = 05-06 (前一日)
  NAV = 0.8840 (netvaluehistory at 05-06)
  EST = fundest at 05-06 (用05-06之前factor算出的预测值)
  误差 = EST / 0.8840 - 1
```

---

## 五、各数据表在EST流程中的角色

| 表名 | 在EST流程中的角色 | 写入时机 |
|------|-----------------|---------|
| **netvaluehistory** (162411) | 提供NAV（校准输入 + 误差分母） | 基金公司每日发布后导入 |
| **netvaluehistory** (XOP) | 提供XOP收盘价（校准输入 + EST分子） | Yahoo数据每日更新 |
| **netvaluehistory** (USCNY) | 提供CNY汇率（校准 + EST计算） | 汇率数据每日更新 |
| **calibrationhistory** | 存储每日校准因子 | DailyCalibration() 每日运行 |
| **fundest** | 存储预计算的EST值 | GetOfficialNetValue() 美股<20:55 |
| **fundposition** | 存储仓位比例（LOF=0.95） | 手动配置 |
| **lastcalibration** | 存储校准时的base_val | DailyCalibration() 时同步写入 |
| **xop_nav_ssga** | SSGA官方XOP NAV（仅展示用） | ssga_nav.py 定期抓取 |

---

## 六、Python实现对应关系

| PHP函数/方法 | Python实现 | 文件 |
|-------------|-----------|------|
| `DailyCalibration()` | 批量回填脚本（待实现定时任务） | scripts/ 或 services/ |
| `CalcFactor()` | 内联于回填脚本 | — |
| `QdiiGetVal()` | `qdii_get_val()` | `app/services/qdiiref.py` |
| `EstFromPair()` | 内联于 `routes.py:premium_history()` | `app/routes.py` |
| `FundAdjustPosition()` | `fund_adjust_position()` | `app/services/fundref.py` |
| `GetPosition()` | `_get_position()` | `app/services/fundref.py` |
| `StockUpdateEstResult()` | FundEst ORM write | `app/models/market_data.py` |
| `GetPercentageDisplay()` | `(est/nav-1)*100` | `app/routes.py:premium_history()` |
