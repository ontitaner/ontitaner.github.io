<!-- @AI_GENERATED -->
# 附录 C EMS 数学函数、公式与实现速查

> [课程首页](README.md) · [完整章节概览](README.md#全部章节概览) · [附录 B 方向规范](附录B_符号与功率方向规范.md)

**一句话**：课程里用到的 22 个公式和小函数，每个给出定义、单位、用途、所在章节、lab 实现位置和最容易踩的坑；本附录还把公式连接到 example、test 和适用边界。

**公式卡片阅读顺序**：先看方向和单位，再看公式和手算，随后定位 `lab/ems_lab` 实现、章节 example 与测试；最后阅读“陷阱”和“不能证明什么”。公式中的 `[教学示例]` 参数不能直接作为现场整定值。

**约定**：

- 方向和符号以 [附录 B](附录B_符号与功率方向规范.md) 为准：储能放电为正，并网点送电为正，无功发出为正，可充/可放为非负幅值；
- 代码单位 kW、kvar、kVA、kWh、s；SOC 在代码中为 0～1；
- 函数签名以 `lab/ems_lab/` 中的代码为准，“lab 实现”一列给出模块和函数名，完整签名见对应章节和源码；
- 手算中的数字均为 `[教学示例]`，不能直接用于现场。

---

## C.0 总表

| # | 函数 | 核心公式 | 详解章节 | lab 实现 |
|---|---|---|---|---|
| C.1 | 限幅 clamp | `min(max(x, lo), hi)` | 第 11 章 | `control.clamp` |
| C.2 | 按方向限幅 | `clamp(P, −可充, +可放)` | 第 11、12 章 | `control.clamp_power` |
| C.3 | 截断型死区 | `abs(x) ≤ w → 0；否则 x` | 第 11、15 章 | `control.deadband_cut` |
| C.4 | 连续型死区 | `abs(x) ≤ w → 0；否则 x − w·sign(x)` | 第 11、15 章 | `control.deadband_shift` |
| C.5 | 滞回 | 低于开启阈值开，高于关闭阈值关 | 第 11 章 | `control.Hysteresis` |
| C.6 | Ramp 变化率限制 | `Δ = clamp(目标 − 上次, −r↓·dt, +r↑·dt)` | 第 11 章 | `control.RateLimiter`、`control.limit_then_ramp` |
| C.7 | 一阶低通 | `y ← y + α(x − y)`，`α = dt/(τ + dt)` | 第 11 章 | `control.LowPassFilter` |
| C.8 | 查表插值 | 分段线性，表外取端点 | 第 11 章 | `control.interp_table` |
| C.9 | PI + 抗饱和 | `u = 前馈 + Kp·e + Σ Ki·e·dt`，顶住限幅时停积分 | 第 11 章 | `control.PIController` |
| C.10 | 梯形积分电量 | `E = Σ (P[i] + P[i−1])/2 · Δt[i]` | 第 02 章 | `power.energy_kwh_trapezoid` |
| C.11 | 安时 / 能量积分 SOC | `SOC −= P·Δt/(E·η_dis)` 等 | 第 05a、05b 章 | `battery.update_soc`、`battery.CoulombCounter` |
| C.12 | P-Q-S 与 PF | `S = √(P² + Q²)`，`PF = abs(P)/S` | 第 02 章 | `power.apparent_power`、`power.power_factor` |
| C.13 | P-Q 圆 | `P_max = √(S² − Q²)` | 第 02、17 章 | `power.max_active_power`、`power.max_reactive_power` |
| C.14 | 下垂与调差率 | `K = Pn/(δ·fn)`，`ΔP = −K·死区(Δf)` | 第 15 章 | `frequency.droop_gain_kw_per_hz`、`frequency.primary_frequency_power` |
| C.15 | 摇摆方程 | `df/dt = fn·ΔP/(2H)` | 第 15 章 | `frequency.swing_rocof_hz_per_s`、`grid_sim.simulate_trip` |
| C.16 | 虚拟惯量 | `ΔP = −2·H_v·Sn/fn · RoCoF` | 第 15 章 | `frequency.virtual_inertia_power` |
| C.17 | RoCoF 窗口拟合 | 窗口内最小二乘直线斜率 | 第 15 章 | `frequency.RocofEstimator` |
| C.18 | 电压降近似 | `ΔU ≈ (P·R + Q·X)/U` | 第 17 章 | `reactive.voltage_rise_v`、`reactive.q_for_voltage_change_kvar` |
| C.19 | PF → Q | `Q = P·tan(arccos PF)` | 第 17 章 | `reactive.q_from_pf`、`reactive.pf_signed` |
| C.20 | 需量 | `D = E_窗口/T_窗口`，预测与剩余允许功率 | 第 14 章 | `demand.fixed_window_demands`、`sliding_window_demands`、`predict_demand_kw`、`allowed_import_kw` |
| C.21 | 按比例分配 | `P_i = P_总 · w_i / Σw` | 第 18 章 | `allocation.allocate_by_capability`、`allocate_soc_balance`、`water_fill` |
| C.22 | 套利收益与价差门槛 | `p_峰 大于 p_谷/η_RTE + c_退化` | 第 13 章 | `arbitrage.spread_threshold`、`cycle_net_profit`；`economics.breakeven_spread` |

---

## C.1 限幅 clamp

```text
                   ┌ lo    x 小于 lo
clamp(x, lo, hi) = ┤ x     lo ≤ x ≤ hi
                   └ hi    x 大于 hi
```

- **参数**：`x` 待限幅值；`lo`、`hi` 下限、上限，与 `x` 同单位。
- **用途**：一切“不能超出范围”的量：功率指令、SOC 目标、配置参数。
- **实现**：`control.clamp(value, lower, upper)`。
- **陷阱**：`lo > hi` 表示可行域为空（约束冲突），函数会报错而不是随便取一个边界；输入含 NaN 时 Python 的 `max/min` 结果取决于参数顺序，函数直接报错，NaN 应在数据校验层拦截。

## C.2 按方向限幅

```text
P_out = clamp(P_request, −available_charge_kw, +available_discharge_kw)
```

- **参数**：`P_request` 请求功率（kW，放电为正）；`available_charge_kw`、`available_discharge_kw` 可充、可放能力（kW，**非负幅值**）。
- **手算**：可放 800、可充 500，请求 +1000 → +800；请求 −700 → −500。
- **用途**：每条功率指令下发前的最后一道能力检查。
- **实现**：`control.clamp_power(p_request_kw, available_charge_kw, available_discharge_kw)`。
- **陷阱**：用对称区间 `±额定` 代替两个独立能力；BMS 上送的可充功率带负号，未在接入层换算就传入（函数会报错）。

## C.3 截断型死区

```text
deadband_cut(x, w) = 0    当 abs(x) ≤ w
                   = x    其他
```

- **参数**：`x` 偏差（如 `f − fn`，Hz）；`w` 死区半宽，非负。
- **用途**：一次调频、调压中“小偏差不动作”，死区外按完整偏差计算。
- **实现**：`control.deadband_cut(x, width)`。
- **陷阱**：边界处输出从 0 跳到 `±w`，频率在边界附近徘徊时出力来回跳；死区要作用在**偏差**上，不是作用在频率本身。

## C.4 连续型死区

```text
deadband_shift(x, w) = 0              当 abs(x) ≤ w
                     = x − w·sign(x)  其他
```

- **手算**：`w = 0.03 Hz`，`x = −0.10 Hz`：截断型 −0.10，连续型 −0.07。乘以同一个下垂系数后，出力相差 30%。
- **用途**：希望出力从死区边界起连续增长的场合。
- **实现**：`control.deadband_shift(x, width)`；一次调频中由 `PrimaryFrequencyConfig.deadband_mode` 选择 `"shift"` 或 `"cut"`。
- **陷阱**：选哪一种由项目适用的规程和考核方法决定，选错会被判“出力不足”或“过调”（第 15 章案例一）；“正好等于死区”的输入用 `<` 还是 `≤` 要全项目统一并有测试。

## C.5 滞回

```text
未激活 且 x 小于 on_below   → 激活
已激活 且 x 大于 off_above  → 取消激活
其他                        → 保持原状态
```

- **参数**：`on_below` 开启阈值，`off_above` 关闭阈值，要求 `on_below < off_above`；`initial` 初始状态。
- **手算**：15% / 25% 的 SOC 自充滞回，SOC 依次 16、14、20、24、26、20 → 关、开、开、开、关、关。
- **用途**：低 SOC 自充、告警产生与恢复、模式切换。
- **实现**：`control.Hysteresis(on_below, off_above, initial=False).update(x)`。
- **陷阱**：它有状态，控制器重启时 `initial` 要按实际运行状态初始化；滞回带宽小于测量噪声时等于没有滞回。

## C.6 Ramp 变化率限制

```text
Δ    = clamp(目标 − 上次输出, −down_rate·dt, +up_rate·dt)
输出 = 上次输出 + Δ
```

- **参数**：`up_rate`、`down_rate` 上升/下降速率（kW/s，非负）；`dt` 周期（s）。
- **单位换算**：规程常写 %Pn/min。`r[kW/s] = r[%Pn/min] / 100 × Pn[kW] / 60`。例：1000 kW、10%Pn/min → 1.67 kW/s。
- **手算**：0 → 1000 kW，100 kW/s，周期 1 s，第 10 秒到达。
- **用途**：所有主动功率变化的平滑。
- **实现**：`control.RateLimiter(up_rate, down_rate, initial=0.0)`，方法 `update(target, dt)`、`reset(value)`；推荐组合 `control.limit_then_ramp(p_request_kw, ramp, dt, available_charge_kw, available_discharge_kw)`：限幅 → Ramp → 再限幅兜底 → 同步 Ramp 状态。
- **陷阱**：能力突降时只靠 Ramp 慢慢降会在若干周期内越过安全能力，必须兜底限幅；“上升”指代数值增大（−500 → 0 也是上升）；%Pn/min 与 kW/s 换算差 60 倍；紧急功能是否绕过 Ramp 要按项目要求明确配置。

## C.7 一阶低通滤波（α 与 τ 换算）

```text
y ← y + α·(x − y)
α = dt / (τ + dt)          （后向欧拉，lab 实现采用）
α = 1 − e^(−dt/τ)          （精确离散化，dt 远小于 τ 时两者几乎相等）
τ = dt·(1 − α) / α         （已知 α 反求 τ）
```

- **参数**：`τ` 时间常数（s）：阶跃后输出走完 63.2% 的时间，约 3τ 走完 95%；`dt` 采样周期（s）。
- **手算**：`dt = 0.1 s`、`τ = 1 s` → `α ≈ 0.091`（精确式 0.095）。α 不变而 `dt` 改为 0.5 s 时，实际 `τ` 会随之改变，所以**配置写 τ，代码按实际 dt 算 α**。
- **用途**：频率、功率测量降噪；RoCoF 前处理。
- **实现**：`control.LowPassFilter(tau_s).update(x, dt)`；第一个样本直接作为初值，`tau_s = 0` 时不滤波。
- **陷阱**：滤波延迟会吃掉快速功能的响应时间预算；数据无效时应冻结滤波器，而不是把异常值也滤进去。

## C.8 查表插值

```text
y = y0 + (y1 − y0) · (x − x0) / (x1 − x0)     x 位于 [x0, x1]
x 小于等于 xs[0] → ys[0]；x 大于等于 xs[−1] → ys[−1]（不外推）
```

- **手算**：30℃ → 1.0，45℃ → 0.5，38℃ 时比例 ≈ 0.733，1000 kW 降额为约 733 kW。
- **用途**：温度/SOC 降额、效率曲线、厂家能力表。
- **实现**：`control.interp_table(x, xs, ys)`；要求至少 2 点、`xs` 严格递增。
- **陷阱**：外推可能得到负功率或大于 1 的比例；充电、放电降额是两张表；BMS 已经给出可充/可放功率时，EMS 不应再重复降额。

## C.9 PI 控制与抗积分饱和

```text
e       = 目标 − 测量
积分候选 = 积分 + Ki·e·dt
u_未限幅 = 前馈 + Kp·e + 积分候选
u       = clamp(u_未限幅, out_min, out_max)
若 u_未限幅 已越过上限且 e 大于 0，或越过下限且 e 小于 0 → 不更新积分（条件积分）
否则 积分 = 积分候选
```

- **参数**：`Kp` 比例系数，`Ki` 积分系数（1/s），`out_min/out_max` 输出限幅（每周期可更新），`feedforward` 前馈。
- **用途**：并网点功率闭环（防倒送、需量、计划跟踪）、定 Q 控制。
- **实现**：`control.PIController(kp, ki, out_min, out_max, anti_windup=True)`，方法 `update(error, dt, feedforward=0.0)`、`reset(integral=0.0)`，属性 `saturated`。
- **陷阱**：没有抗饱和时，限制解除后积分一次性释放造成超调；模式切换要 `reset`；测量数据无效时要冻结积分；闭环对象有数百毫秒到数秒延迟，增益过大会振荡。判断“往外推”的写法假设 `Kp`、`Ki` 为正。

## C.10 梯形积分电量

```text
E[kWh] = Σ ( P[i] + P[i−1] ) / 2 × ( t[i] − t[i−1] ) / 3600
```

- **参数**：`t` 时间戳（s，严格递增，可不等间隔）；`P` 功率（kW）。
- **手算**：0.5 h 从 0 线性升到 1000 kW，再保持 0.5 h：`250 + 500 = 750 kWh`。
- **用途**：充放电电量、效率统计、需量窗口能量。
- **实现**：`power.energy_kwh_trapezoid(times_s, powers_kw)`；时间戳不递增时报错。
- **陷阱**：`电量 += 功率 × 固定周期` 在通信变慢或丢包时系统性偏差；充电和放电电量要分开累计（先按符号拆分再积分），否则相互抵消。

## C.11 安时积分与能量积分 SOC

```text
能量形式（功率 P 在某一测量平面上，放电为正，Δt 单位 h）：
  放电：SOC_next = SOC − P·Δt / (E_usable · η_dis)
  充电：SOC_next = SOC + abs(P)·Δt · η_ch / E_usable

安时形式（电流 I 放电为正，单位 A；Δt 单位 s；Q_Ah 为容量）：
  SOC_next = SOC − I·Δt / (3600 · Q_Ah)
```

- **参数**：`E_usable` 可用能量（kWh）；`η_ch`、`η_dis` 从该测量平面到电池可用能量的单向效率；`Q_Ah` 安时容量。
- **手算**：`E_usable = 4000 kWh`，交流侧以 1000 kW 放电 0.5 h，`η_dis = 0.95`：SOC 下降 `1000 × 0.5 / (4000 × 0.95) ≈ 13.2%`。电芯 280 Ah、放电 140 A、1800 s：SOC 下降 25%。
- **用途**：EMS 侧的 SOC 预测、仿真中的电池模型、SOC 是否够完成下一段计划。
- **实现**：`battery.update_soc(soc, p_kw, dt_s, capacity_kwh, eta_charge, eta_discharge, soc_min, soc_max)` 返回 `SocUpdate`（含限幅前 `soc_raw` 与越界原因）；安时积分见 `battery.CoulombCounter`。
- **陷阱**：功率所在的测量平面和效率的定义必须配套（附录 B.4）；`Δt` 的 s/h 混用差 3600 倍；安时积分会累积误差，现场 SOC 以 BMS 为准并关注其校准跳变；更新时应保留“限幅前的原始结果 + 是否越界 + 原因”，不能静默 clamp 后丢掉越界事件。

## C.12 P-Q-S 与功率因数

```text
S  = √(P² + Q²)
PF = abs(P) / S          （S = 0 时按惯例取 1）
```

- **手算**：P = 80 kW、Q = 60 kvar → S = 100 kVA、PF = 0.8。
- **用途**：容量校核、点表合理性检查、功率因数考核统计。
- **实现**：`power.apparent_power(p_kw, q_kvar)`、`power.power_factor(p_kw, q_kvar)`。
- **陷阱**：PF 只有幅值，方向看 Q；这组公式假设平衡三相、基波正弦，含谐波时真实功率因数低于位移功率因数。

## C.13 P-Q 能力圆

```text
P_max = √(S_rated² − Q²)      给定 Q 时的最大有功幅值
Q_max = √(S_rated² − P²)      给定 P 时的最大无功幅值
```

- **手算**：100 kVA，Q = 60 kvar → P 最多 80 kW。
- **用途**：有功优先/无功优先决策、P 与 Q 联合约束。
- **实现**：`power.max_active_power(s_rated_kva, q_kvar)`、`power.max_reactive_power(s_rated_kva, p_kw)`；需求超过视在容量时报错，而不是返回 0。
- **陷阱**：P、Q 同时受限时不能对两个轴分别 clamp（第 17、18 章讲圆上的处理）；真实能力边界不是完美的圆，会随电压、温度、充放电方向变化，以厂家曲线为准。

## C.14 下垂与调差率

```text
K  = Pn / (δ · fn)                          下垂系数，kW/Hz
ΔP = clamp( −K · 死区(f − fn), −限幅, +限幅 )   一次调频增量，kW
P_总 = P_基点 + ΔP
```

- **参数**：`Pn` 额定功率（kW）；`δ` 调差率（如 0.02）；`fn` 额定频率（Hz）；死区类型和宽度；限幅（占 Pn 比例）。
- **手算**：100 MW、δ = 2% → K = 100 MW/Hz。49.90 Hz、连续型死区 0.03 Hz、限幅 10% Pn → ΔP = +7 MW（放电）。
- **用途**：一次调频；Q-U 下垂同理（第 17 章）。
- **实现**：`frequency.droop_gain_kw_per_hz(p_rated_kw, droop_ratio, f_nominal_hz=50.0)`；`frequency.primary_frequency_power(f_hz, cfg)`，`cfg` 为 `PrimaryFrequencyConfig(p_rated_kw, droop_ratio, deadband_hz, limit_ratio, deadband_mode, f_nominal_hz)`。
- **陷阱**：少了负号，频率低时储能反而充电；ΔP 是叠加在基点上的**增量**，不是总指令；δ、死区、限幅、响应时间以 GB/T 40595-2021 及所在电网调度规程为准。

## C.15 摇摆方程（扰动初瞬）

```text
df/dt = fn · ΔP / (2H)
```

- **参数**：`ΔP` 功率缺口占系统容量的比例（标幺值，发电不足为负）；`H` 系统惯性时间常数（s）。
- **手算**：ΔP = −0.04、H = 4 s → RoCoF = −0.25 Hz/s。
- **用途**：估算事故初期频率跌速、理解惯量的作用。
- **实现**：`frequency.swing_rocof_hz_per_s(delta_p_pu, inertia_h_s, f_nominal_hz=50.0)`；完整的时域教学模型见 `grid_sim.simulate_trip(trip_pu, grid, bess, t_end_s, dt, t_trip_s)`（参数 `GridParams`、`BessParams`，结果 `SimResult.nadir_hz`）。
- **陷阱**：公式忽略了负荷阻尼和各类调节器，只在扰动瞬间成立；`grid_sim` 是聚合低阶模型，参数均为 `[教学示例]`，不代表任何具体电网。

## C.16 虚拟惯量

```text
ΔP_惯量 = −2 · H_v · Sn / fn · RoCoF
```

- **参数**：`H_v` 设定的虚拟惯性时间常数（s）；`Sn` 储能额定容量（kW）；`RoCoF` 频率变化率（Hz/s）。
- **手算**：100 MW、H_v = 4 s、RoCoF = −0.15 Hz/s → ΔP = +2.4 MW。
- **用途**：事故初期按跌速提前支撑频率。
- **实现**：`frequency.virtual_inertia_power(rocof_hz_per_s, h_virtual_s, s_rated_kw, f_nominal_hz=50.0)`。
- **陷阱**：RoCoF 测量噪声会直接变成功率噪声；对时间极其敏感，通常放在 PCS 或快速控制装置中实现，EMS 负责参数、投退和记录。

## C.17 RoCoF 窗口拟合

```text
在最近 window_s 秒内的样本 (t_k, f_k) 上做最小二乘直线拟合：
RoCoF = Σ (t_k − t̄)(f_k − f̄) / Σ (t_k − t̄)²
```

- **参数**：`window_s` 窗口长度（s）；时间戳必须递增。
- **对比**：相邻两点相减时，4 mHz 的测量噪声、20 ms 的间隔就能产生 ±0.2 Hz/s 的假 RoCoF；窗口拟合平滑得多，代价是约半个窗口的延迟。
- **用途**：虚拟惯量、按 RoCoF 触发的快速频率响应。
- **实现**：`frequency.RocofEstimator(window_s).update(t_s, f_hz)`；样本少于 3 个时返回 `None`。
- **陷阱**：窗口长度在“抗噪”和“快速”之间取舍，需用实测数据确定；调用方必须处理 `None`，不能当作 0。

## C.18 电压降近似

```text
ΔU ≈ (P·R + Q·X) / U
```

- **参数**：`P`、`Q` 沿线路输送的三相有功（MW）、无功（Mvar），按注入方向取正；`R`、`X` 线路每相电阻、电抗（Ω）；`U` 线电压（kV）；`ΔU` 为线电压变化（kV）。
- **含义**：储能在并网点**注入** P、Q 时，并网点电压相对上游升高约 ΔU；吸收时降低。
- **手算**：10 kV 线路，R = 0.5 Ω、X = 1.0 Ω，注入 P = 2 MW、Q = 1 Mvar：`ΔU ≈ (2 × 0.5 + 1 × 1.0) / 10 = 0.2 kV`，约 2%。
- **用途**：理解“无功管电压”、估算调压效果、解释光伏午间抬高电压。
- **实现**：`reactive.voltage_rise_v(p_kw, q_kvar, r_ohm, x_ohm, u_kv)`（返回 V）；反算所需无功见 `reactive.q_for_voltage_change_kvar`。
- **陷阱**：高压电网 X 远大于 R，电压主要受 Q 影响；低压配电网 R 不小，有功对电压影响同样明显；这是忽略横向分量的近似，不能替代潮流计算。

## C.19 功率因数 → 无功

```text
Q = ± abs(P) · tan(arccos PF)        0 小于 PF ≤ 1
```

- **参数**：`P` 有功（kW）；`PF` 目标功率因数幅值；符号由项目要求（发出还是吸收）决定。
- **手算**：P = 800 kW、PF = 0.95 → `Q ≈ 800 × 0.329 ≈ 263 kvar`。
- **用途**：定功率因数控制、功率因数考核。
- **实现**：`reactive.q_from_pf(p_kw, pf, q_sign)`；由 P、Q 反求带方向的功率因数见 `reactive.pf_signed`。
- **陷阱**：`PF = 0` 或越界要拒绝；P 接近 0 时是否把 Q 置零要明确；算出的 Q 可能超出 P-Q 圆，需投影并记录未满足量；超前/滞后的叫法有惯例差异，以 Q 的符号为准（附录 B.8）。

## C.20 需量：窗口平均、滑差与预测

```text
窗口需量：    D = E_窗口 / T_窗口              E 为窗口内取电能量（由 P_import 梯形积分）
计费最大需量： MD = max(各窗口 D)              一个计费周期内
滑差：        窗口长度 T 不变，每隔滑差步长向前滑动一次，重新计算 D
窗口末预测：  D_预测 = (E_已用 + P_假设 · T_剩余) / T_窗口
剩余允许功率： P_允许 = (D_目标 · T_窗口 − E_已用) / T_剩余
```

- **参数**：`T_窗口` 需量窗口（国内常见 15 min `[行业典型值]`，以电表和供电合同为准）；滑差步长由电表设定；`P_import = −P_PCC`（取电为正）。
- **手算**：15 min 窗口、目标 1800 kW，已过 10 min、平均取电 1900 kW：`E_已用 ≈ 316.7 kWh`；若保持 1900 kW，`D_预测 = 1900 kW` 超标；剩余 5 min 平均取电必须压到 `(1800 × 0.25 − 316.7) / (5/60) ≈ 1600 kW`，即储能需要放电约 300 kW（或减少同样多的充电）。
- **用途**：需量控制、基本电费测算。
- **实现**：`demand.fixed_window_demands`、`sliding_window_demands`、`predict_demand_kw`、`allowed_import_kw`、`required_extra_discharge_kw`；基本电费见 `basic_charge_by_demand`。
- **陷阱**：窗口对齐要以计费电表的时钟为准；滑差方式下一次越限会影响之后多个窗口；倒送时段是否抵扣取电能量取决于计量规则，按项目配置；缺测、坏点要有明确处理规则；`P_import` 只在这里和接入层使用，控制层仍用 `P_PCC`。

## C.21 按比例分配

```text
P_总 大于 0（放电）：w_i = available_discharge_kw[i]
P_总 小于 0（充电）：w_i = available_charge_kw[i]
P_i = P_总 · w_i / Σ w_j，再对每台做按方向限幅
```

- **手算**：站级放电 600 kW，三台 PCS 可放 500、300、100 kW → 333.3、200、66.7 kW。
- **用途**：站级指令拆分到多台 PCS 或多个电池簇；也可按 SOC、SOH 加权。
- **实现**：`allocation.allocate_by_capability(p_total_kw, units)`、`allocate_soc_balance(...)`，余量迭代再分配见 `water_fill`，结果校验见 `check_allocation`。
- **陷阱**：权重要按**方向**取；离线或故障单元权重为 0；`Σw = 0` 时不能除零，应上报“无可用能力”；单台被限幅后剩余量要重新分配给未饱和的单元，仍分不完的记为未满足量；分配结果之和必须回写审计。

## C.22 套利收益与价差门槛

```text
每放出 1 kWh（交流侧）：
  充电成本 = p_谷 / η_RTE
  毛利     = p_峰 − p_谷 / η_RTE − c_退化
价差门槛：p_峰 大于 p_谷 / η_RTE + c_退化 才值得做一次循环
```

- **参数**：`p_峰`、`p_谷` 放电、充电时段电价（元/kWh）；`η_RTE` 交流侧往返效率；`c_退化` 折算到每 kWh 放电量的电池退化成本（元/kWh）。
- **手算**：`p_谷 = 0.30`、`η_RTE = 0.85`、`c_退化 = 0.10` → 门槛约 0.453 元/kWh；`p_峰 = 1.10` 时每 kWh 毛利约 0.647 元。
- **用途**：判断某个时段是否值得充放电、计划曲线编制、收益测算。
- **实现**：`arbitrage.spread_threshold(price_charge, round_trip_eff, degradation_cost_per_kwh)`、`arbitrage.cycle_net_profit(...)`；第 03 章的同类函数见 `economics.breakeven_spread`、`economics.arbitrage_cycle`。
- **陷阱**：效率要用与电量计量点一致的往返效率；辅助用电、需量电费的影响要另外计入；电价、时段会随政策调整，数值以当地最新政策为准；退化成本的折算方法项目之间差异很大。

---

## C.23 使用这些函数时的共同原则

1. **单位写在名字里**：`_kw`、`_kvar`、`_kwh`、`_s`、`_hz`；
2. **有状态的函数要管理状态**：滞回、Ramp、低通、PI、RoCoF 估计器在重启、模式切换、数据失效时要复位或冻结；
3. **限制动作要留痕**：任何 clamp、投影、分配截断，都要能回答“原本想要多少、被谁限制、限制后是多少”；
4. **先合成、后约束**：各功能分别算出请求 → 仲裁合成 → 一次性约束投影 → Ramp → 兜底限幅，不要各自限幅后再相加（第 12、18 章）。


## C.24 公式到实验与测试的索引

| 公式组 | 实现模块 | 最小示例 | 主要测试 |
|---|---|---|---|
| C.1～C.9 控制原语 | `ems_lab.control` | `ch11_control_examples.py`、`ch11_ramp_example.py` | `test_control.py` |
| C.10～C.11 电量与 SOC | `ems_lab.power`、`ems_lab.battery` | `ch04_battery_basics.py`、`ch05_*.py` | `test_power.py`、`test_battery.py` |
| C.12～C.13 P-Q-S 与能力圆 | `ems_lab.power`、`ems_lab.reactive` | `ch06_pcs_projection.py`、`ch17_avc_examples.py` | `test_pcs.py`、`test_reactive.py` |
| C.14～C.17 频率、调频、RoCoF | `ems_lab.frequency`、`ems_lab.grid_sim` | `ch15_primary_frequency_trace.py` | `test_frequency.py`、`test_grid_sim.py` |
| C.18～C.19 电压与功率因数 | `ems_lab.reactive` | `ch17_avc_trace.py`、`ch17_modes_examples.py` | `test_reactive.py` |
| C.20 需量 | `ems_lab.demand` | `ch14_demand_trace.py` | `test_demand.py` |
| C.21 分配 | `ems_lab.allocation` | `ch18_arbitration_allocation.py` | `test_allocation.py` |
| C.22 套利 | `ems_lab.arbitrage`、`ems_lab.economics` | `ch03_economics_trace.py`、`ch13_arbitrage_trace.py` | `test_economics.py`、`test_arbitrage.py` |

### 公式卡片的验收要求

每个公式至少应能回答：输入单位是什么、方向如何定义、边界输入怎样处理、哪个 example 可以重跑、哪个 test 验证手算、模型结果不能证明什么。若公式依赖项目合同、厂家曲线或当地规程，必须把它标为配置或工程边界，而不是写成普适定值。

<!-- @AI_GENERATED: end -->
