<!-- @AI_GENERATED -->
# 附录A AGC术语、符号与参数速查

> [课程首页](README.md) · 上一章：[09 AGC考核不合格的根因在哪](09_AGC典型误区与故障诊断.md)

> 📖 **怎么用这份速查**：不用通读。查公式跳"K1/K2/K3 评分公式速查"，查参数跳"三区域关键参数对照"，查状态跳"AGC 状态机四种状态"。需要和调度对账时看"104 轮询周期与 K2 安全预算"。现场调参数时翻"常用单位换算"。

---

## 🔢 常用单位换算【高频查阅】

现场最频繁的换算操作——Pn/min ↔ MW/s、元/月 ↔ 元/MW·次：

| 换算 | 公式 | 速记示例（100 MW 场站） |
|---|---|---|
| Pn/min → MW/s | MW/s = Pn × (Pn/min值) ÷ 60 | K1=1.0 Pn/min → 100×1.0÷60 = **1.67 MW/s** |
| MW/s → Pn/min | Pn/min = MW/s × 60 ÷ Pn | ramp=1.5 MW/s → 1.5×60÷100 = **0.90 Pn/min** |
| Pn/min → MW/min | MW/min = Pn × (Pn/min值) | K1=1.5 Pn/min → 100×1.5 = **150 MW/min** |
| MW → MW·次（里程） | 每次调节的 ΔP 绝对值累积 | 一次 +15 MW → 15 MW·次（里程单位） |
| MW·次 → MW·月 | MW·月 = Σ每日 MW·次 | 日均 1200 MW·次 → 月均 1200×30 = **36000 MW·月** |
| 元/MW（里程单价）→ 元/月 | 元/月 = MW·月 × 里程单价 × 评分系数 | 36000×0.5×0.80 = **14400 元/月** |
| 元/MW·月（容量单价）→ 元/月 | 元/月 = Pn × 单价 × 投运率 × 评分系数 | 100×10×0.98×0.80 = **784 元/月** |
| 秒 → 分钟（K2 换算） | — | K2=30 s = **0.5 min**（注意考核窗口是分钟级） |
| % Pn → MW | MW = Pn × % | K3=2% Pn → 100×0.02 = **2 MW** |
| MW → % Pn | % = MW ÷ Pn × 100 | 偏差 0.3 MW → 0.3÷100×100 = **0.3% Pn** |

> 💡 **最常见的换算错误**：把 Pn/min 当成 MW/s。K1=1.0 Pn/min 是 1.67 MW/s，不是 1.0 MW/s——这个错误导致华东 100 MW 场站的 ramp rate 配置偏低 40%，直接 K1 不合格。

---

## AGC 核心术语

| 术语 | 英文 | 定义 |
|---|---|---|
| AGC | Automatic Generation Control | 自动发电控制，调度主站计算 ACE 后向各场站下发指令，调整出力以消除频率和联络线偏差 |
| ACE | Area Control Error | 区域控制偏差，ACE = ΔP_tie + B × Δf |
| PFR | Primary Frequency Regulation | 一次调频，本地自主响应频率偏差 |
| FFC | Flat Frequency Control | 定频率控制，AGC 只控制频率、不控联络线 |
| FTC | Flat Tie-line Control | 定联络线控制，AGC 只控联络线、不控频率 |
| TBC | Tie-line Bias Control | 联络线偏差控制，AGC 同时控制频率和联络线 |
| 104 规约 | IEC 60870-5-104 | 调度主站与 EMS 的远动通信标准 |
| PCS | Power Conversion System | 储能变流器，接受 EMS 的控制指令 |
| SOC | State of Charge | 储能电池荷电状态（%），影响充放电能力 |
| ramp rate | | 爬坡速率，出力变化的速度上限（MW/s 或 Pn/min） |

## AGC 性能指标

| 符号 | 全称 | 定义 | 单位 |
|---|---|---|---|
| K1 | 调节速率 | ΔP_actual / Δt | Pn/min 或 MW/min |
| K2 | 响应时间 | T_start_move − T_cmd_issued | s |
| K3 | 调节精度 | \|P_actual_ss − P_target\| / Pn × 100% | % Pn |

## AGC 功率合成变量

| 符号 | 含义 | 单位 |
|---|---|---|
| Pn | 场站额定有功功率 | MW |
| P_target | 调度 AGC 目标出力 | MW |
| P_agc_base | EMS 存储的 AGC 基点 | MW |
| ΔP_primary | 一次调频增量 | MW |
| P_total | 合成总出力指令 | MW |
| P_min / P_max | 出力限幅 | MW |

## AGC 系统变量

| 符号 | 含义 | 说明 |
|---|---|---|
| ΔP_tie | 联络线交换功率偏差 | 实际与计划值的差值 |
| Δf | 频率偏差 | f_actual − 50.00 Hz |
| B | 频率偏差系数 | MW/Hz，区域的自然频率响应特性 |
| T_poll | 104 轮询周期 | 取决于调度侧配置，典型 4~8 s |

## AGC 考核与结算

| 术语 | 含义 |
|---|---|
| 投运率 | AGC 投入时间 / 总考核时间，通常月度计算 |
| 容量补偿 | 按可用可调容量付费（华东/山西） |
| 里程补偿 | 按累计调节里程付费（东北） |
| 调节里程 | Σ\|ΔP_target\|，所有 AGC 指令变化量的绝对值累加 |
| 评分系数 | AGC 月度综合评分 / 100，用于折扣补偿金额 |
| 指令死区 | P_target 变化小于此值时不跟踪 |
| 考核窗口 | 计算 K1/K2/K3 的时间窗口，通常 5 min 或 15 min |

## AGC 通信定时器

| 符号 | 含义 | 推荐值 |
|---|---|---|
| t1 | IEC 104 发送方确认超时 | 15~30 s |
| t2 | IEC 104 接收方确认间隔 | 10~15 s |
| t3 | IEC 104 空闲链路测试间隔 | 20~30 s |

## AGC 常用缩写

| 缩写 | 全称 |
|---|---|
| AGC | Automatic Generation Control |
| EMS | Energy Management System |
| PCS | Power Conversion System |
| SOC | State of Charge |
| ACE | Area Control Error |
| TBC | Tie-line Bias Control |
| FFC | Flat Frequency Control |
| FTC | Flat Tie-line Control |
| DL/T | 电力行业标准（中国） |
| IEC | International Electrotechnical Commission |
| IOA | Information Object Address（IEC 104 信息对象地址） |

## K1/K2/K3 评分公式速查

| 指标 | 评分公式 | 上限 | 说明 |
|---|---|---|---|
| K1（调节速率） | K1_score = min(100, 100 × K1_actual / K1_required) | 100（capped） | K1_required 参考：华东/山西 1.0、东北 1.5 Pn/min |
| K2（响应时间） | K2_score = 100 × (1 − K2_actual / K2_limit) | 100 | K2_limit 参考：华东/山西 60s、东北 30s |
| K3（调节精度） | K3_score = 100 × (1 − K3_actual / K3_limit) | 100 | K3_limit 参考：华东/东北 ±3% Pn、山西 ±2% Pn |

**月度综合评分**：

```text
AGC_score = w1 × K1_score + w2 × K2_score + w3 × K3_score
典型权重：w1=30%, w2=20%, w3=50%
```

**手算验证公式**：

```text
K1_score = min(100, 100 × 0.85/1.0) = 85
K2_score = 100 × (1 − 5/30)    = 83.3
K3_score = 100 × (1 − 2/3)     = 33.3
综合     = 85×0.3 + 83.3×0.2 + 33.3×0.5 = 58.9
```

## 三区域关键参数对照

| 参数 | 华东 | 东北 | 山西 |
|---|---|---|---|
| K1 要求 | ≥1.0 Pn/min | ≥1.5 Pn/min | ≥1.0 Pn/min |
| K2 限值 | ≤60 s | ≤30 s | ≤60 s |
| K3 限值 | ≤±3% Pn | ≤±3% Pn | ≤±2% Pn |
| 指令周期 | 8 s（典型） | 4 s（典型） | 8 s（典型） |
| 补偿模式 | 容量补偿 | 里程补偿 | 容量补偿 |
| 投运率 | ≥98% | ≥95% | ≥98% |
| 考核窗口 | 5 min | 5~15 min | 5 min |

## AGC 状态机四种状态

| 状态 | 含义 | 行为 |
|---|---|---|
| 退出 | 未投入 AGC | 不接收 AGC 指令，不上送 AGC 考核数据 |
| 投入 | 正常投入 | 正常接收、执行、跟踪 AGC 指令 |
| 暂停 | 因异常暂停 | 保持当前出力，不上调/下调，上送告警 |
| 闭锁 | 保护闭锁 | 设备/通信异常或 SOC 越限，AGC 强制退出 |

> 投运率 = (投入时长 + 暂停时长) / 总考核时长。闭锁时长通常不计入投运率，暂停时长部分区域计入。

## AGC 指令死区推荐取值

| 指令周期 | 推荐死区（MW） | 推荐死区（% Pn） | 适用场景 |
|---|---|---|---|
| 4 s（东北） | 0.1~0.2 MW | 0.1%~0.2% Pn | 高频小步长，需减少"不跟踪"判定 |
| 8 s（华东/山西） | 0.3~0.5 MW | 0.3%~0.5% Pn | 标准周期，死区偏大→K2 伪不合格风险 |
| 15 s 以上 | 0.5~1.0 MW | 0.5%~1.0% Pn | 低频更新，死区可适当放大以降低设备磨损 |

> 死区上限公式：死区 ≤ 调度最小指令步长 ÷ 2（保证每次步长变化都至少有一半被跟踪）。

## AGC 104 轮询周期与 K2 安全预算

| 参数 | 典型值 | 对 K2 的影响 |
|---|---|---|
| 调度轮询周期 T_poll | 4~8 s | 指令更新间隔 = K2 起跑线间隔 |
| EMS 响应延迟 | 0.1~0.5 s（电力电子） | K2 总时长中执行环节占比小 |
| 通信往返延迟 | 0.5~2 s | 在 K2 总预算中不可忽略 |
| 安全裕量 | K2_limit − T_poll − 通信延迟 | 东北 30s−4s−2s=24s（充裕）/ 华东 60s−8s−2s=50s |

<!-- @AI_GENERATED: end -->