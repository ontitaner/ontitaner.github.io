<!-- @AI_GENERATED -->
# 附录 A EMS 术语词典与缩写索引

> [课程首页](README.md) · [完整章节概览](README.md#全部章节概览) · [代码与测试入口](README.md#配套代码示例与测试)

**一句话**：全课程术语的中英文对照、缩写、首次详解章节和代码定位；正文讲业务与推导，本附录负责查词、定位和复习。

**使用约定**：

- 正文首次出现某个术语时写成“中文（English，缩写）”，之后可以只用缩写，但不能改变缩写的含义；
- “首次详解”指这个术语被系统讲解的章节，不一定是它第一次出现的章节；标“附录 B”的术语以附录 B 的定义为准；
- 功率方向、单位、测量点的约定以 [附录 B](附录B_符号与功率方向规范.md) 为准，本词典不重复定义正负号；
- 厂商自定义名称（如某品牌的“能量路由器”）不是行业通用术语，不收录；
- 带“[了解]”的条目只需知道含义，不要求会实现。

---

## A.1 电力系统基础

| 中文 | 英文全称 | 缩写 | 一句话解释（面向软件工程师） | 首次详解 |
|---|---|---|---|---|
| 电力系统 | Power System | — | 发电、输电、配电、用电组成的整体，最大特点是发电和用电必须每时每刻相等 | 第 01 章 |
| 发电 / 输电 / 配电 | Generation / Transmission / Distribution | — | 电能从电厂经高压电网、再经中低压电网送到用户的三个环节 | 第 01 章 |
| 电压等级 | Voltage Level | — | 电网按标称电压分层（如 0.4 kV、10 kV、35 kV、110 kV），储能站接入哪一级决定了它的调度关系和规范要求 | 第 01 章 |
| 同步电网 | Synchronous Grid | — | 所有同步发电机转速被电磁力锁在一起的电网，同一时刻各处频率几乎相同 | 第 15 章 |
| 同步发电机 | Synchronous Generator | SG | 火电、水电、核电的发电机，转子转速与电网频率严格同步，转子动能天然提供惯量 | 第 15 章 |
| 额定频率 | Nominal Frequency | fn | 电网的标称频率，中国为 50 Hz；代码中常写 `f_nominal_hz` | 第 02 章 |
| 额定电压 | Nominal Voltage | Un | 电网或设备的标称电压；标幺化电压时常用它做基准 | 第 02 章 |
| 标幺值 | Per Unit | p.u. | 实际值 ÷ 基准值得到的无量纲数，便于在不同容量、电压等级之间比较；类似“归一化” | 第 15 章 |
| 惯量 | Inertia | — | 系统抵抗频率变化的“质量”，来自同步机转子动能；新能源通过电力电子并网，基本不提供惯量 | 第 15 章 |
| 惯性时间常数 | Inertia Constant | H | 额定转速下的转子动能能以额定功率输出多少秒，H 越小频率跌得越快 | 第 15 章 |
| 负荷 | Load | — | 用电设备消耗的功率；在本课程符号中消耗为正 | 第 01 章 |
| 峰谷差 | Peak-Valley Difference | — | 一天中用电最高和最低时段的差距，是储能“挪电”的业务起点 | 第 01 章 |
| 弃风弃光 | Wind/PV Curtailment | — | 新能源发得出来但电网消纳不了、只能限发的电量 | 第 03 章 |
| 调度中心 | Dispatch Center / Control Center | — | 电网的上级指挥系统，下发计划曲线、AGC、AVC 指令并考核执行情况 | 第 01 章 |
| 变电站 | Substation | — | 进行电压变换、电能汇集和分配的场所；储能站的并网点常在其母线或出线上 | 第 01 章 |
| 短路比 / 弱电网 [了解] | Short-Circuit Ratio / Weak Grid | SCR | 接入点短路容量与设备容量之比，比值小说明电网“软”，电压对功率变化更敏感 | 第 06 章 |
| 低频减载 | Under-Frequency Load Shedding | UFLS | 频率跌到设定值时，电网自动切除一部分用户负荷来止跌，相当于“有损降级” | 第 15 章 |
| 稳控 / 安全稳定控制 | Stability Control / Emergency Control | — | 电网严重故障时由专用装置快速切机、切负荷或调节出力，独立于 EMS 的快速通道 | 第 08 章 |

## A.2 功率与电能

| 中文 | 英文全称 | 缩写 | 一句话解释（面向软件工程师） | 首次详解 |
|---|---|---|---|---|
| 有功功率 | Active Power | P | 真正被消耗、储存或送出的能量速度，单位 kW；电费、SOC、功率平衡都只看 P | 第 02 章 |
| 无功功率 | Reactive Power | Q | 在电源和电感/电容之间来回搬运、平均不做功的能量幅度，单位 kvar；它维持电压、占用设备容量 | 第 02 章 |
| 感性无功 / 容性无功 | Inductive / Capacitive Reactive Power | — | 电感（电流滞后电压）产生的无功记为正、电容（电流超前电压）产生的记为负；这是负荷惯例下的行业约定，本课程方向以 Q 的正负（发出为正）为准 | 第 02 章 |
| 发出 / 吸收无功 | Injecting / Absorbing Reactive Power | — | 无功能量来回吞吐的方向，不是消耗；`Q_BESS > 0` 为发出、< 0 为吸收。“发出感性无功 = 吸收容性无功”是同一现象的两种说法 | 第 02 章 |
| 无功补偿 | Reactive Power Compensation | — | 在负载（如电机）附近就地发出/吸收无功，减少无功长途输送、提高功率因数；电容补偿电机是典型例子，PCS 也能做 | 第 02 章 |
| 视在功率 | Apparent Power | S | 设备实际承受的“总量”，S² = P² + Q²，单位 kVA；PCS、变压器按 S 标定容量 | 第 02 章 |
| 功率因数 | Power Factor | PF | PF = \|P\| / S，只有幅值没有方向；方向要看 Q 的正负 | 第 02 章 |
| 超前 / 滞后 | Leading / Lagging | — | 电流相位领先或落后于电压；同一物理状态在发电机惯例和负荷惯例下叫法相反，课程用 Q 的正负代替 | 附录 B |
| 有效值 | Root Mean Square | RMS | “与多大直流电发热相同”的等效值；点表里的电压、电流默认是有效值 | 第 02 章 |
| 三相交流 | Three-Phase AC | — | 三根相线电压依次错开 120°，点表中的 P、Q、S 通常是三相总量 | 第 02 章 |
| 相电压 / 线电压 | Phase Voltage / Line Voltage | — | 相线对中性点 / 两相线之间的电压，平衡时线电压 = 相电压 × √3 | 第 02 章 |
| 电量 | Energy | — | 功率对时间的累加，单位 kWh（度）；离散采样用梯形积分 | 第 02 章 |
| 功率平衡 | Power Balance | — | 并网点功率 = 站内所有发出 − 所有消耗，是防倒送、需量等功能的第一步 | 附录 B |
| 取电 / 倒送 | Import / Export | — | 站点从电网吸收有功 / 向电网送出有功 | 附录 B |
| 四象限运行 | Four-Quadrant Operation | — | P 和 Q 各自可正可负，储能能在 P-Q 平面四个象限运行 | 第 02 章 |
| P-Q 能力圆 | P-Q Capability Curve | — | 理想模型下 P² + Q² ≤ S² 的圆形运行范围；真实设备以厂家能力曲线为准 | 第 02 章 |
| 电能质量 | Power Quality | PQ | 电压偏差、频率偏差、谐波、闪变、三相不平衡等指标的统称 | 第 06 章 |
| 谐波 | Harmonics | — | 频率为基波整数倍的电压/电流分量，电力电子设备会产生；EMS 一般只读监测值 | 第 06 章 |
| 三相不平衡 | Three-Phase Unbalance | — | 三相电压或电流不一致；最重的一相可能先过流，而三相总功率看不出来 | 第 02 章 |
| 电压偏差 | Voltage Deviation | — | 实际电压相对标称值偏离的百分比，是 AVC 的控制对象之一 | 第 17 章 |

## A.3 储能与电池

| 中文 | 英文全称 | 缩写 | 一句话解释（面向软件工程师） | 首次详解 |
|---|---|---|---|---|
| 电池储能系统 | Battery Energy Storage System | BESS | 电池、BMS、PCS、热管理、消防、通信组成的完整系统；本课程的核心对象 | 第 04 章 |
| 储能系统 | Energy Storage System | ESS | 更宽泛的储能概念，可含飞轮、超级电容等；外部资料中的 `P_ESS` 在本课程统一写 `P_BESS` | 附录 B |
| 电芯 | Battery Cell | Cell | 电池的最小电化学单元，BMS 监测到每一颗的电压和温度 | 第 04 章 |
| 电池模组 | Battery Module | Module | 若干电芯串并联组成的可更换单元 | 第 04 章 |
| 电池簇 | Battery Rack / Cluster | Rack | 若干模组串联、由一个簇级 BMS 管理、接入一路直流的单元 | 第 04 章 |
| 电池管理系统 | Battery Management System | BMS | 监测电芯、估算 SOC/SOH、计算可充/可放功率并在危险时自主切断；EMS 无权覆盖它的保护 | 第 04 章 |
| 木桶效应 | Weakest-Cell Effect | — | 串联电池组的可充/可放能力由最差的那颗电芯决定，一颗电芯到限整簇都要限 | 第 04 章 |
| 一致性 / 均衡 | Cell Consistency / Balancing | — | 电芯之间容量、内阻、SOC 的差异，以及 BMS 缩小这种差异的手段 | 第 04 章 |
| 开路电压 | Open-Circuit Voltage | OCV | 电池静置、无电流时的端电压，与 SOC 有对应关系，常用来校准 SOC | 第 04 章 |
| 充放电倍率 | C-rate | C | 充放电电流（或功率）相对容量的倍数，1C 约 1 小时充满或放完 | 第 04 章 |
| 荷电状态 | State of Charge | SOC | 当前可用电量占容量的比例；代码用 0～1，正文用 %，必须声明容量基准 | 第 05a 章 |
| 健康状态 | State of Health | SOH | 电池相对新电池的健康程度；必须说明是容量 SOH、内阻 SOH 还是综合值 | 第 05b 章 |
| 功率状态 | State of Power | SOP | 当前时间窗口内分方向的可充/可放功率能力，不是一个无方向的单值 | 第 05c 章 |
| 可充 / 可放功率 | Available Charge / Discharge Power | — | SOP 的具体数值，本课程一律用非负幅值（`available_charge_kw`、`available_discharge_kw`） | 附录 B |
| 放电深度 | Depth of Discharge | DoD | 一次运行用掉的电量占可用容量的比例 | 第 05 章 |
| 等效完整循环 | Equivalent Full Cycle | EFC | 累计充放电能量折算成的完整循环次数，用于寿命和质保统计 | 第 05 章 |
| 额定容量 / 可用容量 | Rated / Usable Capacity | — | 铭牌标称的能量 / 当前 SOC 窗口、温度、SOH 下实际允许使用的能量 | 第 05b 章 |
| 安时积分 | Coulomb Counting | — | 对电流按时间累加来推算 SOC，简单但会累积误差，需要 OCV 等方法校准 | 第 05a 章 |
| 充电效率 / 放电效率 | Charge / Discharge Efficiency | η_ch / η_dis | 某一测量平面到电池可用能量之间的单向效率；必须说明是电池侧、PCS 侧还是端到端 | 第 05b 章 |
| 往返效率 | Round-Trip Efficiency | RTE | 放出的电量 ÷ 充入的电量，决定峰谷套利的价差门槛 | 第 05b 章 |
| 降额 | Derating | — | 因温度、SOC、SOH 等原因把允许功率调低，常由厂家表格给出 | 第 05b 章 |
| 循环老化 / 日历老化 [了解] | Cycle / Calendar Aging | — | 因充放电次数 / 因时间和存放条件导致的容量衰减 | 第 05b 章 |
| 热失控 | Thermal Runaway | — | 电池内部放热反应失控、温度急升并可能起火的严重事故；由 BMS 和消防系统负责 | 第 04 章 |
| 热管理系统 | Thermal Management System | TMS | 控制电池和 PCS 温度的液冷或风冷系统，其耗电计入辅助用电 | 第 07 章 |
| 辅助系统 | Balance of Plant | BoP | 电池和 PCS 以外支撑电站运行的系统，如液冷、消防、照明、通信 | 第 07 章 |

## A.4 变流与并网

| 中文 | 英文全称 | 缩写 | 一句话解释（面向软件工程师） | 首次详解 |
|---|---|---|---|---|
| 储能变流器 | Power Conversion System | PCS | 在电池直流和电网交流之间双向变换能量、按指令输出 P 和 Q 的执行器 | 第 06 章 |
| 逆变器 | Inverter | — | 直流变交流的电力电子设备；PCS 是可双向工作、带储能接口的变流器 | 第 06 章 |
| 脉宽调制 [了解] | Pulse Width Modulation | PWM | PCS 内部用高速开关合成正弦电压的方法，属于微秒级控制，不在 EMS 范围内 | 第 06 章 |
| 跟网型 | Grid-Following | GFL | 先锁相测量电网电压和频率，再按指令注入电流；目前大多数储能 PCS 属于此类 | 第 06 章 |
| 构网型 | Grid-Forming | GFM | 像同步机一样自己建立电压和频率，功率随电网变化自然响应，可提供惯量支撑 | 第 06 章 |
| 虚拟同步机 [了解] | Virtual Synchronous Generator | VSG | 构网型控制的一种实现，用控制算法模拟同步机的转子方程 | 第 06 章 |
| 低电压穿越 / 高电压穿越 | Low / High Voltage Ride-Through | LVRT / HVRT | 电网电压短时跌落或升高时设备不脱网、按规范继续运行并支撑电压的能力；由 PCS 本地实现 | 第 06 章 |
| 故障穿越 | Fault Ride-Through | FRT | 高低电压穿越、频率穿越等“扰动期间不脱网”能力的统称 | 第 06 章 |
| 防孤岛保护 | Anti-Islanding Protection | — | 电网失电后，并网设备检测到“孤岛”并停止向局部网络送电，防止检修人员触电 | 第 06 章 |
| 并网点 | Point of Common Coupling / Point of Interconnection | PCC / POI | 站点与外部电网交换功率、计量和考核的边界点；项目要写明用 PCC 还是 POI | 第 07 章 |
| 升压变压器 | Step-up Transformer | — | 把 PCS 输出的低压交流升到并网电压等级，其损耗计入 `P_loss` | 第 07 章 |
| 电压互感器 / 电流互感器 | Voltage / Current Transformer | PT(VT) / CT | 把高电压、大电流按变比转换成仪表可测的小信号；变比或极性配错会让读数整体错位或反向 | 第 07 章 |
| 功率变化率 | Ramp Rate | — | 功率随时间变化的速度，规程常用 %Pn/min，代码常用 kW/s | 第 11 章 |
| 响应时间 | Response Time | — | 从指令或扰动发生到出力开始/达到目标的时间，需按端到端链路拆分 | 第 09 章 |
| 黑启动 [了解] | Black Start | — | 电网全停后不依赖外部电源自行启动并逐步恢复供电的能力，一般需要构网型设备 | 第 06 章 |

## A.5 EMS 与控制

| 中文 | 英文全称 | 缩写 | 一句话解释（面向软件工程师） | 首次详解 |
|---|---|---|---|---|
| 能量管理系统 | Energy Management System | EMS | 站级“控制平面”：汇总全站数据，按调度、电价、电网状态计算并下发功率指令 | 第 08 章 |
| 站级控制器 | Power Plant Controller / Site Controller | PPC | 协调多台 PCS 跟踪并网点目标的控制装置；有的项目与 EMS 合一，有的独立部署 | 第 08 章 |
| 控制周期 | Control Cycle | — | 控制循环执行一次的间隔；不等于端到端响应时间 | 第 09 章 |
| 控制流水线 | Control Pipeline | — | 采集 → 校验 → 状态估计 → 策略 → 仲裁合成 → 约束 → Ramp → 下发 → 反馈的固定处理顺序 | 第 09 章 |
| 参考值 / 指令 / 测量值 | Reference / Command / Measurement | ref / cmd / meas | 策略想要的值 / 最终下发的值 / 设备实际反馈的值，三者必须分开存储 | 附录 B |
| 闭环 / 开环控制 | Closed-Loop / Open-Loop Control | — | 按实测偏差持续修正 / 按公式算一次就下发 | 第 11 章 |
| 前馈 | Feedforward | FF | 按模型直接算出“大致应该给多少”，闭环只修正剩余误差 | 第 11 章 |
| 限幅 | Clamping / Saturation | — | 把数值压回允许区间；储能区间是 [−可充, +可放]，两边不对称 | 第 11 章 |
| 死区 | Deadband | DB | 偏差小于阈值时输出 0，分截断型和连续型，二者出力不同 | 第 11 章 |
| 滞回 | Hysteresis | — | 开和关用不同阈值，防止在边界附近来回抖动 | 第 11 章 |
| 变化率限制器 | Rate Limiter / Ramp Limiter | — | 限制每个周期输出最多变化多少；类似令牌桶限流 | 第 11 章 |
| 一阶低通滤波 | First-Order Low-Pass Filter | LPF | 每次只朝新测量值走一部分，等价于 EWMA；配置写时间常数 τ，而不是写 α | 第 11 章 |
| 查表插值 | Look-up Table Interpolation | LUT | 厂家给的表格点之间按直线估算，表外取端点值 | 第 11 章 |
| 比例积分控制器 | Proportional-Integral Controller | PI | 按“现在差多少”和“一直差了多久”持续修正输出 | 第 11 章 |
| 比例积分微分控制器 [了解] | Proportional-Integral-Derivative Controller | PID | 在 PI 上加变化趋势项；D 对噪声敏感，EMS 功率闭环很少用 | 第 11 章 |
| 抗积分饱和 | Anti-Windup | — | 输出被限幅时停止或回拉积分，防止限制解除后超调 | 第 11 章 |
| 状态机 | Finite State Machine | FSM | 用有限状态和切换条件描述运行模式，让每个动作可解释 | 第 11 章 |
| 下垂控制 | Droop Control | — | 频率（或电压）每偏离一点，有功（或无功）按固定比例变化一点 | 第 15 章 |
| 可行域 | Feasible Region | — | 同时满足所有硬约束的功率取值范围；为空时说明约束冲突，必须上报 | 第 12 章 |
| 约束投影 | Constraint Projection | — | 把合成后的总请求压回可行域的那一步，一次性对总量执行 | 第 12 章 |
| 防超容 | Transformer / Capacity Overload Protection | — | 限制并网点或变压器不超过容量上限 | 第 12 章 |
| 防倒送 | Export Limitation / Anti-Backflow | — | 限制站点向电网送电 `P_PCC ≤ P_export_limit`，零倒送时上限为 0 | 第 12 章 |
| 防非计划充电 | Unplanned Charging Prevention | — | 限制不该发生的充电（`P_BESS < 0`），与防倒送是两个独立功能 | 第 12 章 |
| 缺电自充 / 低 SOC 自充 | Low-SOC Self-Charging | — | SOC 过低时自动小功率充电恢复备用能力，通常配合滞回 | 第 05 章 |
| 命令仲裁 | Command Arbitration | — | 按优先级把多个功能的请求合成为一个总请求，并记录谁被限制、原因是什么 | 第 18 章 |
| 功率分配 | Power Dispatch / Allocation | — | 把站级总指令按各 PCS/各簇的实时能力拆分下发 | 第 18 章 |
| 未满足量 | Unserved Amount | — | 请求值与最终执行值之差，必须记录和上报，不能静默丢弃 | 第 18 章 |
| 故障安全 | Fail-Safe | — | 出错时进入预先定义的安全状态，而不是继续执行不确定的动作 | 第 09 章 |
| 降级运行 | Degraded Operation | — | 部分数据或设备不可用时以受限能力继续运行 | 第 09 章 |
| 看门狗 | Watchdog | WDT | 监视任务或通信是否按时“喂狗”，超时即触发安全动作 | 第 09 章 |
| 模型预测控制 [了解] | Model Predictive Control | MPC | 用预测模型滚动优化未来一段时间的控制序列；主线只介绍思路 | 第 13 章 |
| 经济调度 [了解] | Economic Dispatch | ED | 满足约束前提下优化成本、收益和寿命的调度 | 第 13 章 |

## A.6 调度与市场

| 中文 | 英文全称 | 缩写 | 一句话解释（面向软件工程师） | 首次详解 |
|---|---|---|---|---|
| 一次调频 | Primary Frequency Control | PFC | 电源或储能按本地频率偏差自动增减有功，秒级止住频率下跌，但不能回到 50 Hz | 第 15 章 |
| 调差率 | Droop Ratio / Speed Regulation | δ | 频率变化（占 fn 比例）与出力变化（占 Pn 比例）之比；换算为下垂系数 K = Pn / (δ·fn) | 第 15 章 |
| 调频死区 | Frequency Deadband | — | 频率偏差小于该值时一次调频不动作；类型和数值以规程为准 | 第 15 章 |
| 频率变化率 | Rate of Change of Frequency | RoCoF | 频率对时间的变化率，单位 Hz/s；由功率缺口和系统惯量决定 | 第 15 章 |
| 频率最低点 | Frequency Nadir | Nadir | 扰动后频率跌到的最低值，过低会触发低频减载 | 第 15 章 |
| 准稳态频率偏差 | Quasi-Steady-State Frequency Deviation | — | 一次调频后频率停住但仍低于额定值的那部分偏差，需要二次调频消除 | 第 15 章 |
| 虚拟惯量 | Virtual Inertia / Synthetic Inertia | — | 储能按 RoCoF 输出功率，模拟同步机转子释放动能 | 第 15 章 |
| 快速频率响应 | Fast Frequency Response | FFR | 比常规一次调频更快的有功支撑服务，定义和验收方法各电网不同 | 第 15 章 |
| 二次调频 | Secondary Frequency Control | — | 调度主站统一计算、分钟级把频率和联络线功率拉回计划值，即 AGC | 第 16 章 |
| 自动发电控制 | Automatic Generation Control | AGC | 调度每隔几秒下发出力指令，电站跟踪并被考核调节速率、精度和响应时间 | 第 16 章 |
| 区域控制偏差 | Area Control Error | ACE | 调度用来计算 AGC 指令的偏差量，综合了频率偏差和联络线功率偏差 | 第 16 章 |
| AGC 性能指标 [了解] | AGC Performance Indices | K1 / K2 / K3 | 国内常见的调节速率、调节精度、响应时间三项考核指标，定义以所在区域细则为准 | 第 16 章 |
| 三次调频 [了解] | Tertiary Frequency Control | — | 分钟到小时级重新安排发电计划，恢复前两层消耗的备用 | 第 15 章 |
| 计划曲线 | Schedule / Dispatch Curve | — | 调度或交易下达的分时段功率目标，常见每 15 分钟一个点 | 第 13 章 |
| 基点功率 | Base Point | — | 一次调频等增量叠加之前的功率基准，通常是计划值或 AGC 指令 | 第 15 章 |
| 自动电压控制 | Automatic Voltage Control | AVC | 调度主站下发电压或无功目标，电站调节无功把并网点电压维持在目标附近 | 第 17 章 |
| 无功-电压下垂 | Reactive Power–Voltage Droop | Q-U 下垂 | 电压低就多发无功、电压高就吸收无功，按固定斜率计算 | 第 17 章 |
| 静止无功发生器 | Static Var Generator | SVG | 基于电力电子的动态无功补偿装置，常与储能 PCS 一起参与站内无功调节 | 第 17 章 |
| 静止无功补偿器 [了解] | Static Var Compensator | SVC | 基于晶闸管投切电抗/电容的无功补偿装置，响应比 SVG 慢 | 第 17 章 |
| 有载调压分接头 [了解] | On-Load Tap Changer | OLTC | 变压器带负荷改变变比来调电压，动作慢且次数受限，需与 AVC 协调 | 第 17 章 |
| 辅助服务 | Ancillary Services | — | 调频、调峰、备用、调压、黑启动等维持电网安全的服务，按规则补偿或考核 | 第 03 章 |
| 调峰 | Peak Regulation / Load Following | — | 按电网要求在负荷高峰多发、低谷少发（储能为低谷充电） | 第 03 章 |
| 两个细则 [了解] | Grid Operation and Ancillary Service Implementation Rules | — | 各区域能源监管机构制定的并网运行管理和辅助服务管理实施细则，是考核和补偿的直接依据 | 第 16 章 |
| 电力现货市场 [了解] | Electricity Spot Market | — | 按日前、实时时段出清电价的市场，储能可按价格信号充放电 | 第 03 章 |
| 容量租赁 [了解] | Capacity Leasing | — | 独立储能把容量租给新能源电站以满足配储要求，获取固定收入 | 第 03 章 |
| 虚拟电厂 [了解] | Virtual Power Plant | VPP | 把分散的储能、负荷、分布式电源聚合成一个可调度资源参与电网 | 第 03 章 |
| 分时电价 | Time-of-Use Tariff | TOU | 按尖峰、高峰、平段、低谷时段执行不同电度电价；具体时段和价格以当地最新政策为准 | 第 13 章 |
| 峰谷套利 | Peak-Valley Arbitrage | — | 低价时充电、高价时放电赚取价差，价差需超过效率损耗和退化成本 | 第 13 章 |
| 两部制电价 | Two-Part Tariff | — | 电费 = 按用电量计的电度电费 + 按容量或最大需量计的基本电费 | 第 14 章 |
| 基本电费 / 电度电费 | Capacity (Demand) Charge / Energy Charge | — | 按变压器容量或最大需量收取的部分 / 按 kWh 收取的部分 | 第 14 章 |
| 需量 | Demand | — | 规定时间窗口内的平均取电功率，单位 kW | 第 14 章 |
| 最大需量 | Maximum Demand | MD | 一个计费周期（通常为一个月）内各需量窗口的最大值，决定基本电费 | 第 14 章 |
| 需量窗口 | Demand Interval | — | 计算需量的时间窗，国内常见 15 分钟 [行业典型值]，以电表和供电合同为准 | 第 14 章 |
| 滑差 | Sliding Window Step | — | 需量窗口每次向前滑动的步长；滑差计算时一次越限会影响之后多个窗口 | 第 14 章 |
| 需量预测 | Demand Forecast | — | 根据窗口内已用电量和剩余时间的假设功率，预估本窗口结束时的需量 | 第 14 章 |

## A.7 通信与数据

| 中文 | 英文全称 | 缩写 | 一句话解释（面向软件工程师） | 首次详解 |
|---|---|---|---|---|
| 监控与数据采集系统 | Supervisory Control and Data Acquisition | SCADA | 负责设备监视、数据采集、告警、历史记录和遥控操作的系统；EMS 常与其同平台部署 | 第 08 章 |
| 人机界面 | Human-Machine Interface | HMI | 运行人员看状态、确认告警、下发操作的界面 | 第 08 章 |
| 四遥 | Telemetry / Teleindication / Telecontrol / Teleadjusting | YC / YX / YK / YT | 遥测（模拟量）、遥信（开关量）、遥控（开关命令）、遥调（设定值）四类数据的统称 | 第 10 章 |
| 遥测 | Telemetry | YC | 功率、电压、温度等模拟量；带缩放系数、单位和质量位 | 第 10 章 |
| 遥信 | Teleindication / Telesignal | YX | 断路器位置、故障信号等状态量 | 第 10 章 |
| 遥控 | Telecontrol | YK | 分合闸、启停等开关命令，通常要“选择—执行”两步确认 | 第 10 章 |
| 遥调 | Teleadjusting / Setpoint Command | YT | 功率设定值等连续调节命令 | 第 10 章 |
| 点表 | Point List / Data Point Table | — | 每个数据点的地址、类型、缩放、单位、方向、质量要求的配置清单；相当于接口契约 | 第 10 章 |
| Modbus | Modbus（RTU / TCP） | — | 常见的寄存器式主从协议，设备侧最常用；要核对寄存器地址、字节序、符号位和缩放系数 | 第 10 章 |
| 字节序 / 字序 | Byte Order / Word Order | — | 多字节数值在寄存器中的排列顺序，配错会得到离谱的数值 | 第 10 章 |
| 控制器局域网 [了解] | Controller Area Network | CAN | 常用于 BMS 内部及 BMS 与 PCS 之间的实时总线 | 第 10 章 |
| IEC 104 规约 | IEC 60870-5-104 | 104 | 基于 TCP/IP 的电力远动协议，场站与调度主站之间最常用；国内对应 DL/T 634.5104 | 第 10 章 |
| 总召唤 | General Interrogation | GI | 104 等规约中主站一次性召唤全部数据的过程，常用于连接建立和断线恢复 | 第 10 章 |
| IEC 61850 | IEC 61850（Communication Networks and Systems for Power Utility Automation） | — | 以面向对象数据模型（逻辑设备、逻辑节点）描述电力设备的通信标准体系 | 第 10 章 |
| 制造报文规范 | Manufacturing Message Specification | MMS | IEC 61850 中客户端/服务器方式的站控层通信服务 | 第 10 章 |
| 面向通用对象的变电站事件 | Generic Object Oriented Substation Event | GOOSE | IEC 61850 中用于快速事件发布/订阅的机制，常用于保护和联锁 | 第 10 章 |
| 顺序事件记录 | Sequence of Events | SOE | 按毫秒级时标记录状态变化的先后顺序，事故分析的主要依据 | 第 10 章 |
| 质量位 | Quality Code / Quality Flags | — | 标明数据是否有效、过期、被替代、越限或通信中断的附加属性 | 第 10 章 |
| 时间戳 | Timestamp | — | 数据采集或事件发生的时刻；要区分设备采样时间和网关接收时间 | 第 10 章 |
| 数据新鲜度 | Data Freshness | — | 数据从采集到被使用经过了多久，超过阈值就不能参与控制 | 第 10 章 |
| 数据冻结 | Frozen / Stale Value | — | 通信异常时数值长时间不变但质量位仍“正常”的现象，需要专门检测 | 第 10 章 |
| 对时 | Time Synchronization（NTP / PTP / IRIG-B） | — | 让全站设备时钟一致；没有统一时钟，SOE 和调频考核数据无法对齐 | 第 10 章 |
| 远动装置 / 远动机 | Remote Terminal Unit / Telecontrol Gateway | RTU | 场站与调度主站之间转发四遥数据的专用装置，调度侧通过它看到电站 | 第 08 章 |
| 通信管理机 | Communication Management Unit / Protocol Gateway | — | 站内把多种设备协议汇集、转换后统一上送的装置，负载过高会拖慢采集周期 | 第 08 章 |
| 数据网关 | Device Gateway | — | EMS 软件中把各种设备协议转换成统一数据模型、并完成方向和单位换算的接入层 | 第 10 章 |

## A.8 安全与运维

| 中文 | 英文全称 | 缩写 | 一句话解释（面向软件工程师） | 首次详解 |
|---|---|---|---|---|
| 电力监控系统安全防护 | Cyber Security Protection of Power Monitoring and Control Systems | — | 国内对调度、厂站监控系统的强制性网络安全要求，核心是分区、专网、隔离、认证 | 第 08 章 |
| 生产控制大区 / 管理信息大区 | Production Control Zone / Management Information Zone | — | 按业务重要性划分的两大网络区域，前者承载实时监控，后者承载办公和管理信息 | 第 08 章 |
| 安全Ⅰ区（控制区） | Security Zone I (Control Zone) | — | 生产控制大区中直接实时控制的区域，EMS 实时控制、SCADA、远动一般在此 | 第 08 章 |
| 安全Ⅱ区（非控制区） | Security Zone II (Non-Control Zone) | — | 生产控制大区中不直接控制、但与生产密切相关的区域，如电能量计量、部分功率预测系统 | 第 08 章 |
| 横向隔离 | Horizontal Isolation | — | 同一厂站内不同安全区之间的隔离措施；跨大区必须用专用隔离装置 | 第 08 章 |
| 正向隔离装置 | Forward Isolation Device | — | 只允许数据从生产控制大区单向流向管理信息大区的专用装置 | 第 08 章 |
| 反向隔离装置 | Reverse Isolation Device | — | 只允许管理信息大区的数据（通常是文件）经严格校验后单向进入生产控制大区 | 第 08 章 |
| 纵向加密认证 | Vertical Encryption and Authentication | — | 厂站与调度之间经调度数据网通信时，在边界部署专用装置做加密和身份认证 | 第 08 章 |
| 网络安全等级保护 [了解] | Classified Protection of Cybersecurity | 等保 | 国内信息系统按等级落实安全要求的制度，电力监控系统同样适用 | 第 20 章 |
| 双机热备 | Hot Standby / Active-Standby Redundancy | — | 主备两套 EMS 实时同步，主机故障时备机接管；切换期间指令不能跳变 | 第 08 章 |
| 可观测性 | Observability | — | 通过日志、指标、事件推断系统内部状态的能力 | 第 20 章 |
| 告警 / 事件 | Alarm / Event | — | 需要人处理的异常 / 已发生的状态变化记录；告警要有生命周期和滞回 | 第 20 章 |
| 控制决策审计 | Control Decision Audit | — | 记录每条最终指令的来源、被哪些约束限制、原因和执行结果 | 第 20 章 |
| 幂等 | Idempotency | — | 同一命令重复下发不会产生额外副作用；重试和断线重连的前提 | 第 09 章 |
| 故障注入 | Fault Injection | — | 在测试中人为制造通信中断、数据冻结、设备跳闸等故障，验证降级行为 | 第 19 章 |
| 软件在环 | Software-in-the-Loop | SIL | 控制软件与仿真模型闭环运行的测试；注意与功能安全中的“安全完整性等级（SIL）”同缩写不同义 | 第 19 章 |
| 硬件在环 | Hardware-in-the-Loop | HIL | 真实控制器接入实时仿真器运行的测试，能验证真实通信和时序 | 第 19 章 |
| 实时数字仿真器 [了解] | Real-Time Digital Simulator | RTDS | 常用于 HIL 的电力系统实时仿真设备（也是某厂商产品名） | 第 19 章 |
| 工厂验收测试 | Factory Acceptance Test | FAT | 交付前在厂家或实验室进行的验收测试 | 第 19 章 |
| 现场验收测试 | Site Acceptance Test | SAT | 部署到现场后进行的联调和验收测试，包括方向核对、点表核对 | 第 19 章 |
| 并网试验 | Grid Connection Test / Commissioning Test | — | 按并网规范和调度要求对一次调频、AGC、AVC、电能质量等做的现场试验 | 第 19 章 |
| 安全完整性等级 [了解] | Safety Integrity Level | SIL | 功能安全标准（IEC 61508 系列）中安全功能可靠程度的分级；与“软件在环”同缩写 | 第 12 章 |

---

## A.9 缩写速查

```text
ACE   区域控制偏差          AGC   自动发电控制          AVC   自动电压控制
BESS  电池储能系统          BMS   电池管理系统          BoP   辅助系统
CAN   控制器局域网          C-rate 充放电倍率          CT/PT 电流/电压互感器
DoD   放电深度              EFC   等效完整循环          EMS   能量管理系统
FAT   工厂验收测试          FFR   快速频率响应          FSM   状态机
GFL   跟网型                GFM   构网型                GOOSE 面向通用对象的变电站事件
HIL   硬件在环              HMI   人机界面              HVRT  高电压穿越
LPF   低通滤波              LUT   查表                  LVRT  低电压穿越
MD    最大需量              MMS   制造报文规范          MPC   模型预测控制
OCV   开路电压              OLTC  有载调压分接头        PCC   并网点
PCS   储能变流器            PF    功率因数              PFC   一次调频
PI    比例积分              POI   并网点（互联点）      PPC   站级控制器
RoCoF 频率变化率            RTE   往返效率              RTU   远动装置
SAT   现场验收测试          SCADA 监控与数据采集        SCR   短路比
SIL   软件在环 / 安全完整性等级（看上下文）            SOC   荷电状态
SOE   顺序事件记录          SOH   健康状态              SOP   功率状态
SVC   静止无功补偿器        SVG   静止无功发生器        TMS   热管理系统
TOU   分时电价              UFLS  低频减载              VPP   虚拟电厂
VSG   虚拟同步机            YC/YX/YK/YT 遥测/遥信/遥控/遥调
```

## A.10 自测

用一句话（中文或英文）解释下列术语，并说出它在 EMS 代码里对应什么：

```text
BESS、BMS、PCS、PCC、SOC、SOP、P/Q/S、PF、调差率、死区、RoCoF、Nadir、
AGC、ACE、AVC、SVG、两部制电价、最大需量、滑差、四遥、SOE、
安全Ⅰ区、正向隔离、纵向加密认证、构网型、LVRT、防孤岛、SIL、HIL、FAT、SAT
```


## A.11 术语到代码与测试的快速索引

| 术语组 | 首要章节 | 实现/示例 | 测试 |
|---|---|---|---|
| 功率、PCC、取电/倒送 | [02](02_交流电与功率.md)、[07](07_电站拓扑与功率平衡.md) | `ems_lab.power`、`ch07_site_balance.py` | `test_power.py`、`test_site.py` |
| SOC、SOH、SOP、能力 | [05a](05a_SOC估计与校准.md)、[05b](05b_从SOC到可用电量.md)、[05c](05c_功率能力与能力模型.md) | `ems_lab.battery`、`ch05_*.py` | `test_battery.py` |
| 控制、约束、可行域 | [11](11_控制基础函数.md)、[12](12_安全约束与可行域.md) | `ems_lab.control`、`ems_lab.constraints` | `test_control.py`、`test_constraints.py` |
| AGC、AVC、SOE、FAT/SAT | [16](16_AGC与调度考核.md)、[17](17_无功电压与AVC.md)、[19](19_仿真与测试.md) | `ems_lab.agc`、`ems_lab.reactive`、`ch16_agc_trace.py` | `test_agc.py`、`test_reactive.py`、`test_sim_scenarios.py` |
| 点表、质量、审计 | [10](10_通信点表与数据质量.md)、[20](20_运维可观测性与安全.md) | `ems_lab.datapoint`、`ems_lab.observability` | `test_datapoint.py`、`test_observability.py` |
| 仲裁、分配、综合验收 | [18](18_命令仲裁与功率分配.md)、[21](21_综合项目.md) | `ems_lab.arbitration`、`ems_lab.allocation`、`ems_lab.mini_ems` | `test_arbitration.py`、`test_allocation.py`、`test_mini_ems.py` |

## A.12 自测参考标准

A.10 的答案不要求逐字一致，但至少应包含三部分：**术语含义、在 EMS 中的职责或方向、对应代码/测试入口**。例如：

- `SOC`：荷电状态，代码通常是 0～1；对应 `battery.update_soc` 和 `test_battery.py`；必须说明容量基准。
- `PCC`：并网点功率测量/考核边界；本课程送电为正；对应 `power.pcc_injection_kw` 和 `test_site.py`。
- `AGC`：调度侧二次调频设点；对应 `ems_lab.agc`、`ch16_agc_trace.py` 和 `test_agc.py`。
- `SOE`：按设备时标排序的事件记录；对应第 20 章的事故分析规则，而不是简单按 EMS 收到顺序排序。
- `SIL/HIL/FAT/SAT`：依次是软件在环、硬件在环、工厂验收和现场验收；对应第 19 章的验证阶梯，不能把 SIL 结果当作现场并网证明。

<!-- @AI_GENERATED: end -->
