<!-- @AI_GENERATED -->
# 附录A AVC术语、符号与参数速查

> [课程首页](README.md)

本附录列出 AVC（自动电压控制）领域的核心术语、符号、缩写和常用参数。每个术语标注中英文、首次详解章节及缩写对照。

---

## A.1 核心术语

| 术语 | 英文 | 缩写 | 一句话解释 | 详见章节 |
|---|---|---|---|---|
| 自动电压控制 | Automatic Voltage Control | AVC | 通过调节无功出力来控制电网节点电压的自动控制系统 | 00 |
| AVC 主站 | AVC Master Station | — | 调度端的区域电压优化系统，计算并下发各场站的电压目标 | 00 |
| AVC 子站 | AVC Substation / AVC Sub-station Controller | — | 场站端的电压控制装置/程序，接收主站指令并控制本地无功设备 | 00/06 |
| 并网点 | Point of Common Coupling | PCC | 场站与电网的电气分界点，AVC 最核心的电压受控测点 | 00 |
| 电压目标值 | Voltage Target / Voltage Setpoint | U_target | 调度 AVC 主站下发的并网点电压控制目标 | 01/06 |
| 无功功率 | Reactive Power | Q | 用于建立电磁场、影响电压但不传输净能量的功率，单位 kvar/Mvar | 01 |
| 有功功率 | Active Power | P | 真正传输能量、做功的功率，单位 kW/MW | 01/02 |
| 视在功率 | Apparent Power | S | P 和 Q 的矢量和，PCS 的总容量约束，单位 kVA/MVA | 02/03 |
| 功率因数 | Power Factor | PF | cos(φ) = P/S，衡量有功/无功比例，AVC 的控制模式之一 | 01 |
| Q-U 下垂 | Q-U Droop Control | — | 根据本地 PCC 电压按固定斜率生成无功响应的有差调节 | 01 |
| 定电压 PI | Constant Voltage PI Control | — | 以消除电压偏差为目标的闭环 PI 控制，AVC 子站的核心模式 | 01/02 |
| 死区 | Deadband | DB | 目标附近不产生控制动作的电压区间，防止噪声引发的频繁调节 | 02 |
| 连续死区 | Continuous Deadband | — | 在死区边界平滑过渡的死区类型，消除简单死区的功率跳变 | 02 |
| 滞回死区 | Hysteresis Deadband | — | 带进入/退出双阈值的死区，彻底消除边界高频切换 | 02 |
| 积分饱和 | Integral Windup | — | PI 控制器的积分项在输出被限幅时持续无意义累积的现象 | 02 |
| 抗积分饱和 | Anti-Windup | — | 在输出被限幅时冻结或限制积分累积的保护策略 | 02 |
| P-Q 能力圆 | P-Q Capability Curve / P-Q Circle | — | PCS 在 P-Q 平面上的运行边界：P²+Q² ≤ S² | 02/03 |
| P 优先模式 | P-Priority Mode | — | PCS 保证有功出力、剩余容量给无功的分配模式 | 03 |
| Q 优先模式 | Q-Priority Mode | — | PCS 保证无功出力、剩余容量给有功的分配模式 | 03 |
| SVG | Static Var Generator | SVG | 静止无功发生器，独立的连续无功调节设备 | 03 |
| OLTC | On-Load Tap Changer | OLTC | 有载调压分接头，能改变变压器变比来调节电压的慢设备 | 03 |
| 电压合格率 | Voltage Qualification Rate | VQR | AVC 核心考核指标：PCC 电压在合格范围内的统计时间占比 | 04 |
| 无功调节速率 | Reactive Power Regulation Rate | — | 无功出力变化的速度，kvar/s 或 %Qn/s | 04 |
| 电压响应时间 | Voltage Response Time | — | 从指令下达到 PCC 电压进入稳态的时间 | 04 |
| 无功反向调节 | Reverse Reactive Power Regulation | — | 电压偏差方向与无功出力方向不一致——如电压偏高时发出无功 | 04/09 |
| 软压板 | Soft Strap / Virtual Isolator | — | 调度通过 104 遥控实现的 AVC 远程投退，无物理刀闸 | 06 |
| IEC 60870-5-104 | IEC 60870-5-104 | IEC104 / 104 | 远动通信协议标准，调度与场站间 AVC 指令的传输协议 | 06 |
| 五级流水线 | Five-Stage Pipeline | — | AVC 子站的数据处理链路：接收→校验→控制→分配→执行 | 06 |
| 控制状态机 | Control State Machine | — | AVC 的运行状态管理：INIT→STANDBY→RUNNING/FREEZE/BLOCKED | 06 |
| 冻结（FREEZE） | FREEZE State | — | 通信或数据失效时，AVC 保持最后一拍 Q 值的保护状态 | 06 |
| 闭锁（BLOCKED） | BLOCKED State | — | 保护动作或人工操作时，AVC 立即将 Q 置零的安全状态 | 06 |
| 四时刻数据 | Four-Timestamp Data | — | 联调证据链：T_cmd / T_recv / T_Q90% / T_settle | 08 |
| 无功电能量补偿 | Reactive Energy Compensation | — | 按实际发/吸的无功电量（kvarh）结算的辅助服务模式 | 05/07 |
| 无功容量补偿 | Reactive Capacity Compensation | — | 按可用无功容量 × 投运时间（Mvar·h）结算的辅助服务模式 | 05/07 |
| 现行技术标准 | — | DL/T 1867 | 《电力系统自动电压控制技术规范》 | 00 |
| 现行技术导则 | — | DL/T 1707 | 《电力系统电压和无功电力技术导则》 | 00 |

---

## A.2 符号约定

| 符号 | 含义 | 单位 | 说明 |
|---|---|---|---|
| P | 有功功率 | kW / MW | 放电/送电为正 |
| Q | 无功功率 | kvar / Mvar | 发出无功为正（Q>0，容性），吸收无功为负（Q<0，感性） |
| S | 视在功率 | kVA / MVA | PCS 容量上限：P²+Q²≤S² |
| U | 电压 | kV | 线电压有效值 |
| U_pu | 电压标幺值 | pu | U / U_base，1.000 pu 为额定 |
| U_target | 电压目标值 | pu / kV | 调度下发的控制目标 |
| U_ref | 参考电压 | pu | Q-U 下垂的参考点 |
| ΔU | 电压偏差 | pu | U_pcc − U_target |
| ΔU_db | 经死区处理后的电压偏差 | pu | 用于 Q-U 下垂和 PI 控制的有效偏差 |
| PF | 功率因数 | — | = P/S = cos(φ) |
| K | Q-U 下垂斜率 | kvar/pu | 负斜率：电压越高→吸收越多→Q 越负 |
| Kp | PI 比例增益 | kvar/pu | 每 1 pu 电压偏差对应的 Q 输出 |
| Ki | PI 积分增益 | kvar/(pu·s) | 每秒每 1 pu 电压偏差累积的 Q 积分量 |
| Ts | 控制周期 | s | EMS 控制循环的执行间隔 |
| I | PI 积分项 | kvar | 累积的电压偏差积分量 |
| I_max | 积分限幅 | kvar | 抗积分饱和的积分上限 |
| Q_max | 无功出力上限 | kvar | Q 指令的硬限幅 |
| S_nominal | PCS 额定视在功率 | kVA/MVA | PCS 单机铭牌容量 |
| T_cmd | 指令下发时刻 | 时间戳 | 调度主站下发 AVC 指令的时刻 |
| T_recv | 指令接收时刻 | 时间戳 | EMS 子站接收并校验通过的时刻 |
| T_Q90% | 达到目标 90% 时刻 | 时间戳 | 无功出力达到指令目标 90% 的时刻 |
| T_settle | 稳态收敛时刻 | 时间戳 | 电压进入合格范围并稳定的时刻 |
| VQR | 电压合格率 | % | 电压在合格范围内的统计时间占比 |
| Ts | 采样间隔 | s | 统计电压合格率的采样粒度 |

---

## A.3 常见缩写对照

| 缩写 | 全称 | 中文 |
|---|---|---|
| AVC | Automatic Voltage Control | 自动电压控制 |
| AGC | Automatic Generation Control | 自动发电控制 |
| PFR | Primary Frequency Regulation | 一次调频 |
| PCC | Point of Common Coupling | 并网点（公共连接点） |
| PCS | Power Conversion System | 储能变流器 |
| BMS | Battery Management System | 电池管理系统 |
| SVG | Static Var Generator | 静止无功发生器 |
| OLTC | On-Load Tap Changer | 有载调压分接头 |
| PT | Potential Transformer | 电压互感器 |
| EMS | Energy Management System | 能量管理系统 |
| RTU | Remote Terminal Unit | 远动终端单元 |
| IEC104 | IEC 60870-5-104 | 远动通信协议标准 |
| PI | Proportional-Integral | 比例积分控制 |
| VQR | Voltage Qualification Rate | 电压合格率 |
| SOC | State of Charge | 荷电状态 |
| Kp | Proportional Gain | 比例增益 |
| Ki | Integral Gain | 积分增益 |

---

## A.4 典型参数速查

> 以下为 `[教学示例]` 和 `[汇报口径]` 值，仅供参考建立量级概念，不能直接用于现场整定。现场以项目适用的调度规程、并网协议、PCS 手册和点表为准。

| 参数 | 典型值（参考） | 单位 | 说明 |
|---|---|---|---|
| 电压合格范围 | ±0.005 ~ ±0.010 | pu | 江苏 ±0.007、山西 ±0.005、辽宁 ±0.010 [汇报口径] |
| AVC 控制周期 Ts | 2 ~ 4 | s | 常见 EMS 控制循环周期 |
| 104 轮询周期 | 4 ~ 16 | s | 调度主站轮询场站子站的间隔 |
| Q-U 下垂斜率 K | 5000 ~ 20000 | kvar/pu | 根据可用 Q 范围和预期电压偏差设定 |
| Q-U 下垂死区 | ±0.005 ~ ±0.015 | pu | 需与合格范围协调 |
| PI Kp | 2000 ~ 20000 | kvar/pu | 取决于可用 Q 范围和期望响应幅度 |
| PI Ki | 500 ~ 5000 | kvar/(pu·s) | 取决于期望积分累积速度 |
| PI 积分限幅 I_max | 30%~60% Q_max | kvar | 建议为 Q_max 的 50% |
| Q 限幅 Q_max | 根据 PCS/SVG 铭牌 | kvar | 不超过设备铭牌值 |
| PCS 响应时间 | 50 ~ 200 | ms | 从收到指令到开始改变出力 |
| SVG 响应时间 | 10 ~ 50 | ms | 通常比 PCS 更快 |
| OLTC 单档时间 | 3 ~ 10 | s | 机械档位切换时间 |
| 电容投切响应时间 | 5 ~ 30 | s | 包含放电时间和机械开关动作 |
| AVC 无功响应时间要求 | ≤30 ~ ≤60 | s | 各省不同 [汇报口径] |
| 电压合格率考核要求 | ≥99% | — | 各省典型值 [汇报口径] |
| AVC 投运率要求 | ≥98% | — | 各省典型值 [汇报口径] |

---

## A.5 统一符号约定

> **规则**：全书各章统一使用以下符号。同一物理量不得在不同章节使用不同符号（如 V_target / V_ref / V_set / U₀ 混用）。

| 统一符号 | 含义 | 单位 | 优先级 | 废弃别名 |
|---|---|---|---|---|
| U_target | 电压目标值 | pu / kV | 全书唯一 | ~~V_target, V_ref, V_set, U₀~~ |
| U_pcc | PCC 电压实测值 | pu / kV | 全书唯一 | ~~V_pcc, U_meas~~ |
| ΔU | 电压偏差 = U_pcc − U_target | pu | 全书唯一 | ~~e, err~~ |
| ΔU_db | 经死区处理后的电压偏差 | pu | 全书唯一 | — |
| Q | 无功功率 | kvar / Mvar | 全书唯一 | — |
| Q_max | Q 输出硬限幅 | kvar | 全书唯一 | ~~Q_limit~~ |
| I | PI 积分项 | kvar | 全书唯一 | ~~I_sum, I_acc~~ |
| I_max | 积分限幅 | kvar | 全书唯一 | — |
| K | Q-U 下垂斜率 | kvar/pu | 全书唯一 | ~~K_droop~~ |
| Kp | PI 比例增益 | kvar/pu | 全书唯一 | — |
| Ki | PI 积分增益 | kvar/(pu·s) | 全书唯一 | — |
| Ts | 控制周期 | s | 全书唯一 | — |
| S | 视在功率 | kVA / MVA | 全书唯一 | ~~S_max~~ |
| P | 有功功率 | kW / MW | 全书唯一 | — |
| PF | 功率因数 | — | 全书唯一 | — |
| db | 死区半宽 | pu | 全书唯一 | ~~deadband, DB~~ |
| VQR | 电压合格率 | % | 全书唯一 | — |

---

## A.6 常见公式速查

| 编号 | 公式 | 含义 | 单位 | 详见章节 |
|---|---|---|---|---|
| Eq.A-1 | Q = −K × ΔU_db | Q-U 下垂 | kvar | 01 |
| Eq.A-2 | Q = P × tan(arccos(PF)) | 定 PF 的 Q 计算 | kvar | 01 |
| Eq.A-3 | ΔU ≈ (P×R + Q×X) / U | 线路电压降（近似） | kV | 01/09 |
| Eq.A-4 | P² + Q² ≤ S² | P-Q 能力约束 | — | 02/03 |
| Eq.A-5 | Q[n] = Kp×ΔU[n] + I[n] | PI 控制器输出 | kvar | 01/02 |
| Eq.A-6 | I[n] = I[n−1] + Ki×ΔU[n]×Ts | PI 积分更新 | kvar | 02 |
| Eq.A-7 | Q_available = √(S² − P²) | P 优先下的 Q 可用量 | kvar | 02 |
| Eq.A-8 | VQR = (N_total − N_violated) / N_total | 电压合格率 | % | 04 |
| Eq.A-9 | S_month = W_v×S_voltage + W_a×S_availability + W_q×S_performance | 月度综合评分 | 分 | 07 |

---

## A.7 状态机状态速查

| 状态 | 含义 | Q 行为 | 可转移至 |
|---|---|---|---|
| INIT | 初始化 | Q=0 | STANDBY |
| STANDBY | 待命 | Q=0 或保持 | RUNNING |
| RUNNING | 正常运行 | 每拍计算下发 Q | FREEZE, BLOCKED, STANDBY |
| FREEZE | 冻结 | 保持最后一拍 Q | RUNNING, BLOCKED |
| BLOCKED | 闭锁 | Q=0（立即停调） | STANDBY |

---

## A.8 四种控制模式速查

| 模式 | 输入 | 输出公式 | 有状态？ | 电压闭环？ | 适用场景 |
|---|---|---|---|---|---|
| 定 Q | Q_setpoint | Q = Q_setpoint | 否 | 否 | 调度直接下发无功设点 |
| 定 PF | P, PF, dir | Q = dir×\|P\|×tan(acos(PF)) | 否 | 否 | 并网 PF 考核窗口 |
| Q-U 下垂 | U_pcc, U_ref, K, DB | Q = −K×ΔU_db | 否 | 是（有差） | 本地快速响应/通信中断 |
| 定电压 PI | U_pcc, U_target, Kp, Ki | Q = Kp×ΔU + I | 是 | 是（无差） | 调度下发电压目标 |

---

## A.9 响应时间三义对照表

> 04 章详细讨论了"响应时间"在不同角色嘴里的三个含义。此处提供速查对照。

| 名称 | 公式 | 谁用 | 典型值 | 关键差异 |
|---|---|---|---|---|
| **EMS 侧响应时间** | T_Q90% − T_recv | EMS 自统计 | 4~8 秒 | 从子站接收指令开始计时，不含 104 通信延迟 |
| **调度侧响应时间** | T_Q90% − T_cmd | 调度考核 | 12~24 秒 | 从主站下发指令开始计时，含 104 轮询周期（约 8 秒） |
| **电压全程响应时间** | T_settle − T_cmd | 调度/联调验收 | 20~40 秒 | 要求电压也进入合格范围并连续稳定，最严格的口径 |

> **核心矛盾**：EMS 侧看起来合格（4 秒 ≤ 10 秒限值），调度侧却多了 8 秒通信延迟（12 秒 > 10 秒限值 → 不合格）。联调阶段必须对齐计时起点，避免"自认为满分、实际已扣分"。

| 计时节点 | 定义 | 记录者 | 详见 |
|---|---|---|---|
| T_cmd | 调度主站将 AVC 指令写入 104 下行报文 | 调度主站 | 04、06、08 |
| T_recv | EMS 子站接收并通过 104 校验 | EMS 子站 | 04、06 |
| T_Q90% | 全场无功合计 Q_actual 首次达到 Q_target 的 90% | EMS 子站 | 04 |
| T_settle | PCC 电压进入合格范围且连续 3 拍稳定 | EMS/调度 | 04、08 |

<!-- @AI_GENERATED: end -->