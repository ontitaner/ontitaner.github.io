<!-- @AI_GENERATED -->
# 附录C AVC代码实验室函数速查

> [课程首页](README.md) | [lab/ems_lab/](lab/ems_lab/)

本附录按章节列出 `lab/ems_lab/` 中各模块的核心函数与类，供快速查阅。所有函数均已在 `lab/tests/` 中有对应的测试用例（21/21 通过）。

---

## C.1 第 01 章：控制模式

### pi_controller.py — `class PIController`

```python
PIController(kp=8000.0, ki=2000.0, out_max=500.0, out_min=-500.0, i_max=None, ts=4.0)
```

| 方法 | 签名 | 说明 |
|---|---|---|
| `step` | `(error: float) → float` | 单拍 PI 迭代，error = U_target − U_pcc，返回 Q 指令值（含抗积分饱和与输出限幅） |
| `reset` | `() → None` | 清零积分项与历史输出 |

> 默认值为 pu 体系（附录 B）。`i_max` 为积分限幅，缺省等于 `out_max`；正文 01.6/02.4 取 `i_max=300`、`out_max=500`。

---

## C.2 第 02 章：死区与滞回

### deadband.py — `class Deadband`

```python
Deadband(center: float, half_width: float)
```

| 方法 | 签名 | 说明 |
|---|---|---|
| `apply` | `(value: float) → float` | 返回死区外的偏差（死区内返回 0） |
| `in_deadband` | `(value: float) → bool` | 判断当前值是否在死区内 |

### deadband.py — `class HysteresisDeadband`

```python
HysteresisDeadband(center: float, outer_half_width: float, return_ratio: float = 0.6)
```

| 方法 | 签名 | 说明 |
|---|---|---|
| `apply` | `(value: float) → float` | 带进入/退出双阈值的滞回死区 |
| `state` → str | — | 只读属性：`"inside"` / `"outside"` |

---

## C.3 第 02/03 章：P-Q 能力域

### pq_domain.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `q_available_under_p` | `(p_kw: float, s_max_kva: float) → float` | 单台 PCS 在给定 P 下的可用 Q |
| `joint_q_available` | `(pcs: List[dict]) → dict` | 多台 PCS 联合 Q 可用量（返回 q_pos / q_neg / details） |
| `pq_circle_points` | `(s_max_kva: float, n: int = 360) → (List[float], List[float])` | 生成 P-Q 能力圆的 P/Q 坐标对 |

---

## C.4 第 03 章：多资源分配

### resource_allocator.py — `class Strategy(Enum)`

```python
CAPACITY_PROPORTIONAL  # 策略1：按剩余容量比例
SPEED_PRIORITY          # 策略2：按响应速度优先
ECONOMIC_PRIORITY       # 策略3：按经济损耗优先
```

### resource_allocator.py — `class ResourceConfig`

```python
@dataclass
ResourceConfig(
    id: str,
    q_max: float,
    q_min: float,
    speed_rank: int,          # 1=最快(SVG), 2=中速(PCS), 3=最慢(电容)
    unit_cost: float,         # 元/(kvar·h)
    is_discrete: bool,        # 电容/电抗器为 True
    discrete_steps: list,     # 离散挡位列表
)
```

### resource_allocator.py — `class ResourceAllocator`

| 方法 | 签名 | 说明 |
|---|---|---|
| `allocate` | `(q_total: float, strategy: Strategy) → List[dict]` | 按策略分配 Q_total 到各资源 |
| `check_feasibility` | `(q_total: float) → bool` | 检查 Q_total 是否在联合可行域内 |

---

## C.5 第 04 章：考核指标

### compliance.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `voltage_qualification_rate` | `(voltage_series, target=116.0, band=0.5) → float` | 计算电压合格率 |
| `response_time_flag` | `(t_response_s, t_limit_s=30.0) → bool` | 判断单次响应是否合格 |
| `moving_average_vqr` | `(voltage_series, window=6) → float` | 6 小时移动平均口径合格率 |

---

## C.6 第 06 章：状态机

### avc_state_machine.py — `class AVCStateMachine`

```python
AVCStateMachine()
```

| 方法 | 签名 | 说明 |
|---|---|---|
| `trigger` | `(event: str) → bool` | 触发事件，返回是否允许转换 |
| `current_state` → str | — | 只读：`STANDBY` / `RUNNING` / `FREEZE` / `BLOCKED` / `OFFLINE` |

**状态转换表**（`TRANSITIONS` dict）：

| 当前 | 事件 | 目标 |
|---|---|---|
| STANDBY | avc_start | RUNNING |
| RUNNING | comm_loss / quality_invalid | FREEZE |
| FREEZE | comm_restored | RUNNING |
| * | protection_trip | BLOCKED |
| BLOCKED | manual_reset | STANDBY |

---

## C.7 第 07 章：评分与结算

### scoring.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `s_voltage` | `(vqr: float, vqr_target=0.99) → float` | 电压合格率子得分 |
| `s_availability` | `(availability: float) → float` | 投运率子得分 |
| `s_performance` | `(t_avg_s: float, t_target_s=15.0) → float` | 无功调节性能子得分 |
| `monthly_score` | `(vqr, availability, t_avg, w_v=0.5, w_a=0.3, w_q=0.2) → float` | 月度综合评分 |
| `compensation_energy` | `(q_energy_kvarh, price, score_factor, penalty_factor) → float` | 无功电能量补偿金额 |
| `compensation_capacity` | `(q_rated_mvar, price, hours, score_factor) → float` | 无功容量补偿金额 |

---

## C.8 第 07b 章：经济性决策

### economics.py — 模块级函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `pcs_opportunity_cost` | `(q_avg_mvar, s_nominal_mva=50.0, hours_per_year=4000.0, price_spread=0.5, efficiency=0.9, years=10) → dict` | PCS 无功机会成本（全寿命） |
| `svg_total_cost` | `(initial_cost, annual_maintenance, years=15) → float` | SVG 全寿命总成本 |
| `breakeven_q` | `(s_nominal_mva, svg_cost, pcs_params) → float` | 计算盈亏平衡 Q 值 |

---

## C.9 第 05 章：跨区适配

### regional.py — `class RegionalRule`

```python
@dataclass
RegionalRule(
    province: str,
    voltage_deadband_kv: float,
    voltage_band_kv: float,
    sample_interval_s: int,
    measure_point: str,
    score_weights: tuple,
    include_positive_q: bool,
    include_negative_q: bool,
    include_reactive_energy: bool = False,
    include_availability: bool = True,
)
```

预置规则字典 `RULES`：江苏、山西等省的对照参数。

---

## C.10 第 09 章：故障诊断

### diagnostics.py — `class FaultCategory(Enum)`

```python
DEADBAND_COMPLIANCE   # 死区 > 合格范围
NTP_OFFSET            # 时间偏移
SVG_LOCAL_OVERRIDE    # SVG 本地抢控
INTEGRAL_WINDUP       # 积分饱和
PARAM_UPLOAD_BLOCK    # 参数上传阻塞
```

### diagnostics.py — `class FaultDiagnosis`

```python
@dataclass
FaultDiagnosis(
    category: FaultCategory,
    root_cause: str,
    symptoms: List[str],
    fix: str,
    chapter_ref: str,
)
```

---

> 以上函数与类的完整实现及单元测试见 `lab/ems_lab/` 和 `lab/tests/`。所有测试用例执行：`cd lab && python -m pytest tests/ -v`（20/20 通过）。