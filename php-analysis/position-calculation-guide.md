# QDII基金仓位计算方法详解

> **以162411华宝油气为例**
> **创建日期**: 2026-05-08

---

## 一、仓位数据来源

### 1.1 数据库表结构

**表名**: `fundposition`（基金仓位表）

```php
// PHP: php/sql/sqlval.php
class FundPositionSql extends ValSql {
    function ReadPos($strStockId) {
        if ($fPos = $this->ReadVal($strStockId)) return $fPos;
        return 1.0;  // 默认100%仓位
    }
}
```

**Python复刻** (`app/models/market_data.py`):

```python
class FundPosition(Base):
    """基金仓位比例表"""
    __tablename__ = 'fundposition'
    id = Column(Integer, primary_key=True)  # stock_id
    close = Column(Float)  # 仓位比例，如0.95表示95%
```

### 1.2 默认仓位规则

```php
// PHP: php/stock/stocksymbol.php
function GetDefaultPosition() {
    return $this->IsLofA() ? 0.95 : 1.0;  
    // LOF基金默认95%仓位，其他100%
}
```

**162411是LOF基金，默认仓位为95%**

---

## 二、核心公式详解

### 2.1 公式定义

```
(est * cny / estPrev * cnyPrev - 1) * position = (nv / nvPrev - 1)
```

### 2.2 变量说明

| 变量 | 含义 | 示例 |
|------|------|------|
| `est` | 当前标的（XOP）价格 | XOP当天收盘价 |
| `estPrev` | 昨日标的（XOP）价格 | XOP昨日收盘价 |
| `cny` | 当前美元兑人民币汇率 | 7.20 |
| `cnyPrev` | 昨日美元兑人民币汇率 | 7.18 |
| `nv` | 基金当前净值 | 0.387 |
| `nvPrev` | 基金昨日净值 | 0.375 |
| `position` | **仓位比例**（待求解）| 0.95 = 95% |

### 2.3 公式拆解

**左边：标的涨跌幅（以人民币计）**

```
est * cny = XOP当天人民币价值
estPrev * cnyPrev = XOP昨日人民币价值

(est * cny) / (estPrev * cnyPrev) - 1 = XOP的人民币涨跌幅
```

**右边：基金净值涨跌幅**

```
nv / nvPrev - 1 = 基金净值涨跌幅
```

**核心逻辑**：

> 基金净值涨跌幅 = 标的涨跌幅 × 仓位比例

如果基金满仓（100%仓位），则基金涨跌幅应该等于标的涨跌幅。如果基金只有80%仓位，则基金涨跌幅只有标的的80%。

### 2.4 计算示例

**假设数据**：
- XOP昨日：$100，今日：$104（涨4%）
- 汇率昨日：7.20，今日：7.22
- 162411净值昨日：0.375，今日：0.387

**计算过程**：

```
XOP人民币昨日 = 100 * 7.20 = 720
XOP人民币今日 = 104 * 7.22 = 750.88
XOP人民币涨跌幅 = (750.88 - 720) / 720 = 4.29%

基金净值涨跌幅 = (0.387 - 0.375) / 0.375 = 3.20%

仓位 = 3.20% / 4.29% = 0.7458 ≈ 0.75 = 75%
```

**结论**：该基金当前仓位约75%，说明有25%的现金未投资。

---

## 三、PHP代码逐行解析

### 3.1 完整代码

```php
// PHP: php/ui/netvaluehistoryparagraph.php
function _QdiiGetStockPosition($fEstPrev, $fEst, $fPrev, $fNetValue, $fCnyPrev, $fCny, $fInput)
{
    // 第1步：计算基金净值涨跌幅百分比
    $fPercent = StockGetPercentage($fPrev, $fNetValue);
    
    // 第2步：判断基金涨跌幅是否超过阈值（默认4%）
    if (abs($fPercent) > $fInput)
    {
        // 第3步：计算标的（XOP）的人民币涨跌幅
        $fEstPercent = StockGetPercentage($fEstPrev * $fCnyPrev, $fEst * $fCny);
        
        // 第4步：确保标的涨跌幅有效（不为0）
        if (abs($fEstPercent) > MIN_FLOAT_VAL)
        {
            // 第5步：计算仓位比例
            $fVal = $fPercent / $fEstPercent;
            
            if ($fVal > MIN_FLOAT_VAL)
            {
                return number_format($fVal, 2);
            }
        }
    }
    return false;
}
```

### 3.2 步骤详解

| 步骤 | 代码 | 说明 |
|------|------|------|
| 1 | `StockGetPercentage($fPrev, $fNetValue)` | 计算基金净值涨跌幅 = (净值今 - 净值昨) / 净值昨 |
| 2 | `abs($fPercent) > $fInput` | 判断涨跌幅是否超过阈值（默认4%） |
| 3 | `StockGetPercentage($fEstPrev * $fCnyPrev, $fEst * $fCny)` | 计算XOP的人民币涨跌幅 |
| 4 | `abs($fEstPercent) > MIN_FLOAT_VAL` | 确保分母不为0 |
| 5 | `$fVal = $fPercent / $fEstPercent` | **仓位 = 基金涨跌幅 / 标的涨跌幅** |

### 3.3 为什么筛选>4%的波动？

**原因**：
- 小波动时，管理费、托管费、现金利息等因素干扰大
- 大波动时，股票仓位的影响占主导地位
- 4%是一个经验阈值，可以根据实际情况调整

---

## 四、线性回归方法

### 4.1 什么是线性回归？

**线性回归**是统计学中寻找两个变量之间线性关系的方法。

**简单理解**：找到一条直线，让这条直线尽可能拟合所有数据点。

```
y = kx + b

其中：
- y = 基金净值涨跌幅
- x = 标的（XOP）涨跌幅  
- k = 斜率 = 仓位比例
- b = 截距 ≈ 0（理论上应该为0）
```

### 4.2 最小二乘法公式

```
k = Σ[(xi - x̄)(yi - ȳ)] / Σ[(xi - x̄)²]
b = ȳ - k * x̄

其中：
- xi, yi = 第i个数据点
- x̄, ȳ = x和y的平均值
```

### 4.3 与单点计算的区别

| 方法 | 公式 | 特点 |
|------|------|------|
| **单点计算** | position = 基金涨跌幅 / 标的涨跌幅 | 使用单个交易日数据 |
| **线性回归** | y = kx + b，k为仓位 | 使用多个交易日数据拟合 |

**PHP代码使用的是单点计算**，但通过筛选大波动日来提高准确性。

### 4.4 为什么不用线性回归？

**PHP选择单点计算的原因**：
1. **实时性**：单点计算可以每天实时计算
2. **简单性**：不需要存储历史数据，当天数据即可
3. **筛选条件**：只在大波动（>4%）时计算，减少误差

**线性回归的优势**：
- 使用多个数据点，结果更稳定
- 可以计算R²评估拟合质量
- 可以检测异常值

---

## 五、Python实现

### 5.1 单点计算（与PHP等效）

```python
def calculate_position_single(fund_return: float, benchmark_return: float) -> float:
    """
    单点计算仓位（PHP代码的实现方式）
    
    Args:
        fund_return: 基金净值涨跌幅，如 0.032 表示涨3.2%
        benchmark_return: 标的涨跌幅，如 0.0429 表示涨4.29%
    
    Returns:
        仓位比例，如 0.75
    """
    if abs(benchmark_return) < 0.0001:
        return None
    
    position = fund_return / benchmark_return
    return round(position, 2)


# 使用示例
fund_ret = 0.032   # 基金涨3.2%
xop_ret = 0.0429   # XOP涨4.29%
pos = calculate_position_single(fund_ret, xop_ret)
print(f"仓位: {pos * 100:.0f}%")  # 输出: 仓位: 75%
```

### 5.2 线性回归计算

```python
import numpy as np
from sklearn.linear_model import LinearRegression

def calculate_position_by_regression(
    fund_returns: list, 
    benchmark_returns: list
) -> dict:
    """
    使用线性回归计算基金仓位
    
    Args:
        fund_returns: 基金净值涨跌幅列表
        benchmark_returns: 标的涨跌幅列表
    
    Returns:
        包含仓位、截距、R²的字典
    """
    X = np.array(benchmark_returns).reshape(-1, 1)
    y = np.array(fund_returns)
    
    model = LinearRegression()
    model.fit(X, y)
    
    return {
        'position': round(model.coef_[0], 4),
        'intercept': round(model.intercept_, 6),
        'r_squared': round(model.score(X, y), 4)
    }


# 使用示例：10个交易日数据
data = [
    (0.0429, 0.0320),   # (XOP涨跌幅, 基金涨跌幅)
    (-0.0350, -0.0280),
    (0.0520, 0.0410),
    (-0.0480, -0.0380),
    (0.0380, 0.0300),
    (-0.0420, -0.0330),
    (0.0550, 0.0440),
    (-0.0380, -0.0300),
    (0.0450, 0.0360),
    (-0.0500, -0.0400),
]

xop_returns = [d[0] for d in data]
fund_returns = [d[1] for d in data]

result = calculate_position_by_regression(fund_returns, xop_returns)
print(f"仓位: {result['position'] * 100:.1f}%")
print(f"截距: {result['intercept']}")  # 应该接近0
print(f"R²: {result['r_squared']}")    # 越接近1越好
```

### 5.3 滑动窗口线性回归

```python
def calculate_position_sliding_window(
    fund_returns: list,
    benchmark_returns: list,
    window_size: int = 20,
    min_volatility: float = 0.04
) -> list:
    """
    使用滑动窗口线性回归计算仓位序列
    
    Args:
        fund_returns: 基金涨跌幅序列
        benchmark_returns: 标的涨跌幅序列
        window_size: 窗口大小（交易日）
        min_volatility: 最小波动阈值
    
    Returns:
        仓位序列
    """
    positions = []
    
    for i in range(window_size, len(fund_returns)):
        # 取最近window_size个数据点
        y = np.array(fund_returns[i-window_size:i])
        X = np.array(benchmark_returns[i-window_size:i])
        
        # 只在大波动日计算
        valid_idx = np.where(np.abs(X) > min_volatility)[0]
        
        if len(valid_idx) >= 5:  # 至少5个大波动日
            X_filtered = X[valid_idx].reshape(-1, 1)
            y_filtered = y[valid_idx]
            
            model = LinearRegression()
            model.fit(X_filtered, y_filtered)
            
            # 限制仓位在0-1之间
            position = max(0, min(1, model.coef_[0]))
            positions.append(round(position, 2))
        else:
            positions.append(None)
    
    return positions
```

---

## 六、仓位在净值估算中的应用

### 6.1 仓位调整公式

```php
// PHP: php/stock/fundref.php
function FundAdjustPosition($fRatio, $fVal, $fOldVal)
{
    return $fRatio * $fVal + (1.0 - $fRatio) * $fOldVal;
}
```

**公式推导**：

```
设：
- r = 仓位比例
- x = 估算净值
- x0 = 校准基准净值

则：
(x - x0) / x0 = r * (y - y0) / y0

推导：
x / x0 - 1 = r * y / y0 - r
x = x0 * (r * y / y0 + 1 - r)
x = r * (x0 * y / y0) + (1 - r) * x0
```

### 6.2 实际应用示例

```python
def adjust_position(estimated_value: float, position: float, base_value: float) -> float:
    """
    根据仓位调整估算净值
    
    Args:
        estimated_value: 基于标的计算的原始估算值
        position: 仓位比例，如 0.75
        base_value: 校准基准净值
    
    Returns:
        调整后的估算净值
    """
    return position * estimated_value + (1 - position) * base_value


# 示例
raw_estimate = 0.40    # 基于XOP计算的原始估算值
position = 0.75        # 仓位75%
base_value = 0.38      # 校准基准净值

adjusted = adjust_position(raw_estimate, position, base_value)
print(f"调整后估算: {adjusted:.4f}")  # 0.395
```

---

## 七、历史仓位变化记录

根据博客记录，162411华宝油气的历史仓位变化：

| 时间 | 仓位 | 原因 |
|------|------|------|
| 2015-2020.8 | ~95% | 正常LOF仓位 |
| 2020.8 | 85%-90% | 主动降仓位保申购 |
| 2020.9 | 恢复95% | 赎回后仓位回升 |
| 2020.3 | ~75% | 外汇额度不足被动降仓 |

---

## 八、方法对比总结

| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **单点计算** | 简单、实时 | 波动大时误差大 | 日常监控 |
| **线性回归** | 稳定、可评估 | 需要历史数据 | 精确分析 |
| **滑动窗口** | 兼顾实时和稳定 | 计算复杂 | 趋势跟踪 |

---

## 九、Python复刻改进建议

当前Python实现的问题：

```python
# 当前实现（有问题）
elif symbol == 'SZ162411':
    xle_price = get_price('XLE')  # ❌ 应该用XOP
    return xle_price * cny_usd * 0.8  # ❌ 固定仓位
```

建议改进：

```python
# 改进实现
def estimate_sz162411(self):
    # 1. 使用正确的标的
    xop_price = get_price('XOP')  # ✅ XOP是正确的跟踪标的
    
    # 2. 从数据库读取实际仓位
    position = self.get_position('SZ162411', default=0.95)
    
    # 3. 获取汇率
    cny_usd = get_cny_usd()
    
    # 4. 计算原始估算值
    raw_value = xop_price * cny_usd
    
    # 5. 应用仓位调整
    base_value = self.get_calibration_base('SZ162411')
    return self.adjust_position(raw_value, position, base_value)
```

---

## 十、参考资料

- PHP源码: `php/ui/netvaluehistoryparagraph.php`
- PHP源码: `php/stock/fundref.php`
- PHP源码: `php/stock/qdiiref.php`
- 博客文章: `woody/blog/entertainment/20150818cn.php`
- 数据库表: `fundposition`
