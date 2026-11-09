<!-- @AI_GENERATED -->
# 附录C 能量管理与经济调度代码实验室函数速查

> [课程首页](README.md) | [lab/ems_lab/](lab/ems_lab/)

本附录按章节列出 `lab/ems_lab/` 中各模块的核心函数与类，供快速查阅。所有函数均已在 `lab/tests/` 中有对应的测试用例（27/27 通过）。

---

## C.1 第 01 章：峰谷套利

### tariff.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `price_at` | `(hour: float) → float` | 返回某时刻（0~24h）电价（元/kWh） |
| `period_at` | `(hour: float) → str` | 返回所属时段名 `"valley"/"flat"/"peak"` |
| `valley_hours` | `() → list` | 谷段小时列表 `[0..7, 23]` |
| `peak_hours` | `() → list` | 峰段小时列表 `[10,11,17,18,19,20]` |

### energy_flow.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `stored_from_grid` | `(e_grid_mwh: float, eta_chg=0.95) → float` | 充电：电网吸收 → 电池存入（MWh） |
| `out_from_stored` | `(e_stored_mwh: float, eta_dis=0.95) → float` | 放电：电池放出 → 并网输出（MWh） |
| `step_soc` | `(soc, p_mw, dt_h, e_nom=100, eta_chg=0.95, eta_dis=0.95) → float` | 单步 SOC 递推，clamp 到 [0,1] |

### schedule.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `one_cycle` | `(e_avail_mwh=80, price_valley=350, price_peak=1200, ...) → dict` | 一充一放收益明细（元），字段 e_grid/e_out/cost/revenue/profit |
| `two_cycle` | `(e_avail_mwh=80, price_valley=350, price_flat=700, price_peak=1200, ...) → dict` | 两充两放合计，字段 first/second/profit/revenue/cost |

---

## C.2 第 02 章：需量管理

### demand.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `peak_demand` | `(load_mw: list) → float` | 需量 = 15min 平均功率最大值（MW） |
| `demand_charge` | `(peak_mw, price_per_kw_month=40) → float` | 需量电费（元/月） |
| `shave` | `(load_mw, p_bess_max, target_demand) → list` | 各时点削峰放电功率（MW，非负） |
| `shaved_peak` | `(load_mw, bess_discharge) → float` | 削峰后的最大需量（MW） |

---

## C.3 第 03 章：光储协同

### solar.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `pv_curve` | `(t_hour, peak_mw=30) → float` | 简化日光伏曲线（6~18 点半正弦，MW） |
| `moving_average` | `(series: list, window: int) → list` | 滑动平均（等长输出） |
| `bess_for_smoothing` | `(pv_series, window) → list` | 储能补偿功率 = 平滑 − 原始（+放/−充，MW） |
| `track_error` | `(planned, actual) → list` | 计划跟踪误差 = actual − planned（MW） |

---

## C.4 第 04 章：可行调度域

### feasibility.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `available_energy` | `(soc, e_nom=100, soc_min=0.10, soc_max=0.90) → tuple` | 返回 (可放能量, 可充能量) MWh |
| `feasible_p` | `(soc, dt_h, p_max=50, ...) → tuple` | 返回 (p_dis_max, p_chg_max) MW |

---

## C.5 第 05 章：日前优化排程

### schedule.py — `one_cycle` / `two_cycle`（见 C.1）

分段电价下贪心（谷充峰放）即为全局最优，`two_cycle` 复现两充两放。

---

## C.6 第 06 章：日内滚动修正

### rolling.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `arbitrage_profit` | `(prices: list, e_avail=80, ...) → float` | 理想排程（预知价格）收益（元） |
| `fixed_plan_profit` | `(forecast, actual, e_avail=80, ...) → float` | 固定计划（forecast 选时段、actual 结算）收益（元） |
| `mape` | `(forecast: list, actual: list) → float` | 平均绝对百分比误差（%） |

---

## C.7 第 07 章：现货市场

### spot.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `should_discharge` | `(forecast_lmp, cost_per_mwh) → bool` | 预测价 > 放电成本才放电 |
| `bid_price` | `(cost_per_mwh, forecast_lmp, margin=0.1) → float` | 报价 = max(成本, 预测价×(1+margin)) |

---

## C.8 第 08 章：辅助服务叠加

### stack.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `capacity_split` | `(p_nom=50, pfr_reserve=10, volt_reserve=0) → dict` | 返回 {pfr, volt, arbitrage, total}（MW） |

---

## C.9 第 09 章：经济性后评估

### backtest.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `net_profit` | `(revenue, cost, degradation) → float` | 净收益 = 收入 − 成本 − 退化成本 |
| `attribution` | `(planned_profit, actual_profit, factors: dict) → dict` | 偏差归因，返回 gap/explained/residual/check |

---

> 以上函数的完整实现见 `lab/ems_lab/`，单元测试见 `lab/tests/`。执行：`cd lab && python -m pytest tests/ -v`（27/27 通过）。
<!-- @AI_GENERATED: end -->