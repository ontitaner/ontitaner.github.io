<!-- @AI_GENERATED -->
# 附录A 术语与参数速查

> [课程首页](README.md)

本附录按章节收录本课程首次出现的术语、缩写与关键参数，给出中英文、一句话解释与首次详解章节。

## A.1 基础与调度（第 00 章）

| 术语 | 英文/缩写 | 解释 | 首次详解 |
|---|---|---|---|
| 能量管理系统 | Energy Management System, EMS | 对储能进行充放电决策、状态监控与协同控制的系统 | 00 |
| 能量调度 | Energy Scheduling | 决定储能"何时充、何时放、放多少"的决策过程 | 00 |
| 日前调度 | Day-ahead Scheduling | 提前一天制定次日每小时的充放电计划 | 05 |
| 日内调度 | Intra-day Scheduling | 运行当日根据实时信息修正计划 | 06 |
| 实时调度 | Real-time Dispatch | 分钟级响应的即时功率指令 | 06 |
| 决策闭环 | Decision Loop | 感知→决策→执行→评估的循环 | 00 |

## A.2 峰谷套利与需量（第 01、02 章）

| 术语 | 英文/缩写 | 解释 | 首次详解 |
|---|---|---|---|
| 分时电价 | Time-of-Use, TOU | 不同时段执行不同电价 | 01 |
| 峰谷套利 | Peak-valley Arbitrage | 谷段充电、峰段放电赚取价差 | 01 |
| 峰/平/谷时段 | Peak/Flat/Valley | 电价高/中/低时段 | 01 |
| 往返效率 | Round-trip Efficiency, η_rt | 充放一圈后放出的能量/充入的能量 | 01 |
| 需量 | Demand | 用户在某计费周期内的最大平均功率 | 02 |
| 最大需量 | Maximum Demand | 计费周期内需量峰值 | 02 |
| 需量电价 | Demand Charge | 按最大需量收取的电费 | 02 |
| 削峰填谷 | Peak Shaving | 用储能在尖峰放电、低谷充电 | 02 |

## A.3 光储协同（第 03 章）

| 术语 | 英文/缩写 | 解释 | 首次详解 |
|---|---|---|---|
| 光伏 | Photovoltaic, PV | 太阳能直接转化为电能的系统 | 03 |
| 计划出力 | Scheduled Output | 向电网申报的发电计划曲线 | 03 |
| 跟踪计划出力 | Schedule Tracking | 储能补偿光伏预测误差，使并网功率贴近计划 | 03 |
| 功率平滑 | Power Smoothing | 用储能滤波掉光伏出力的高频波动 | 03 |
| 弃光 | Curtailment | 因无法消纳而主动降低光伏出力 | 03 |

## A.4 可行域与优化（第 04、05 章）

| 术语 | 英文/缩写 | 解释 | 首次详解 |
|---|---|---|---|
| 荷电状态 | State of Charge, SOC | 当前剩余电量占额定的比例（0~1） | 04 |
| 能量状态 | State of Energy, SOE | 当前可用能量（含效率折算） | 04 |
| 功率状态 | State of Power, SOP | 当前可持续充/放的最大功率 | 04 |
| 可行调度域 | Feasible Region | 满足 SOC/SOP/功率约束的充放电功率集合 | 04 |
| 线性规划 | Linear Programming, LP | 目标函数与约束均为线性的优化问题 | 05 |
| 目标函数 | Objective Function | 待最大化/最小化的量（如日收益） | 05 |
| 约束条件 | Constraint | 必须满足的等式/不等式 | 05 |
| 贪心算法 | Greedy Algorithm | 每步取局部最优，分段电价下即为全局最优 | 05 |

## A.5 滚动、现货与辅助服务（第 06-08 章）

| 术语 | 英文/缩写 | 解释 | 首次详解 |
|---|---|---|---|
| 滚动时域 | Rolling/Receding Horizon | 每步向前看固定长度、滚动推进的优化方式 | 06 |
| 预测误差 | Forecast Error | 预测值与实际值的偏差 | 06 |
| 现货市场 | Spot Market | 按实时/日前价格交易电能量的市场 | 07 |
| 节点电价 | Locational Marginal Price, LMP | 某节点增加单位负荷的边际成本 | 07 |
| 报价 | Bidding | 向市场申报电量与价格 | 07 |
| 辅助服务 | Ancillary Services | 保障电网安全的调频、调压、备用等服务 | 08 |
| 一次调频 | Primary Frequency Regulation, PFR | 秒级响应频差的有功调节 | 08 |
| 容量叠加 | Capacity Stacking | 同一储能同时参与多种服务的容量分配 | 08 |

## A.6 经济性（第 09 章）

| 术语 | 英文/缩写 | 解释 | 首次详解 |
|---|---|---|---|
| 全寿命成本 | Lifecycle Cost | 设备购置、运维、更换的累计成本 | 09 |
| 平准化储能成本 | Levelized Cost of Storage, LCOS | 全寿命成本摊到每 kWh 放电量 | 09 |
| 循环寿命 | Cycle Life | 电池容量衰减到阈值前的循环次数 | 09 |
| 收益归因 | Revenue Attribution | 把实际收益拆到各影响因素的偏差 | 09 |

---

> 各术语的公式与代码实现见 [附录C](附录C_函数速查.md) 与对应章节。