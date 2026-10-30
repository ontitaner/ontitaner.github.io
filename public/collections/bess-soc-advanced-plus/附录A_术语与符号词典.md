<!-- @AI_GENERATED -->
# 附录 A：术语与符号词典


**一句话**：本附录统一全课程的数据、状态、模型、辨识、可信度和业务术语；正文负责因果和推导，这里负责查词、方向和单位。

## 使用边界

- 术语首次出现时写中文、英文和缩写，之后使用缩写；
- “教学示例”只帮助手算，不代表标准或厂家定值；
- 本课程从软件视角描述模型和均衡结果，不展开电路、器件或固件控制；
- 若项目接口与本附录方向不同，只允许在适配层转换一次，内部仍使用本附录口径。

---

## A.1 状态与业务量

| 中文 | 英文/缩写 | 软件定义 | 单位/口径 | 首次详解 |
|---|---|---|---|---|
| 荷电状态 | State of Charge, SOC | 当前可放电荷相对当前有效满充容量的比例 | 0～1 | 00/02 |
| 能量状态 | State of Energy, SOE | 当前可用能量相对参考能量的比例，或直接给出可用能量 | 0～1 或 kWh | 02/16 |
| 健康状态 | State of Health, SOH | 容量和动态性能相对参考状态的分项指标 | 0～1，不应只给无口径单值 | 02/09 |
| 功率状态 | State of Power, SOP | 当前方向在指定持续时间内可承诺的功率 | kW，充/放分别给出 | 02/17 |
| 有效容量 | Effective Capacity, `C_eff` | 单体口径下，在明确温度、倍率和端点时辨识的当前容量 | Ah | 07/09 |
| 站级有效能量 | Effective Site Energy, `E_eff` | `C_site × SOH_capacity`，站级 SOE 换算的分母 | kWh | 02/16 |
| 额定容量 | Rated Capacity, `C_rated` | 铭牌或合同参考容量 | Ah 或 kWh，必须标口径 | 00 |
| 可用能量 | Available Energy | 在 SOC 窗口、SOH、簇差和效率约束后可交付的能量 | kWh，并标测量平面 | 02/16 |
| 履约 | Delivery/Performance | 在约定时段、功率和边界下实际完成计划 | kW、kWh、时长和偏差 | 00/21 |

## A.2 数据契约与时间

| 中文 | 英文/缩写 | 软件定义 | 首次详解 |
|---|---|---|---|
| 设备时间 | Device Time | 数据源记录的采样时间，用于来源追溯；可能因对时跳变 | 04 |
| 接收时间 | Receive Time | 平台墙上时钟记录的到达时间，用于延迟和审计 | 04 |
| 单调时间 | Monotonic Time | 只递增的本地会话时钟，用于排序、超时和 `dt` | 04 |
| 采样窗口 | Sample Window | 允许把不同通道视为同一时刻的时间范围 | 04 |
| 错拍 | Tick Misalignment | `y[k]` 错配到 `u[k+1]` 或其他窗口 | 04 |
| 重复样本 | Duplicate | 序号或设备时间与已处理样本重复 | 04 |
| 迟到样本 | Late Arrival | 样本在后续窗口已处理后到达，或传输延迟超限 | 04 |
| 缺失样本 | Missing Sample | 序号跳号或相邻有效时间间隔超期 | 04 |
| 数据冻结 | Frozen Payload | 多个独立通道连续多拍逐值不变，疑似采集停滞 | 04 |
| 非有限值 | Non-finite | NaN 或正负无穷，不能进入计算 | 04 |
| 质量门控 | Quality Gate | 在模型前对来源、范围、顺序、完整性、时效和冻结做状态化判定 | 04 |
| `good` | Good | 满足当前数据契约，可正常使用 | 04 |
| `suspect` | Suspect | 有缺失、延迟或冻结证据，需降级使用并保留原因 | 04 |
| `invalid` | Invalid | 非有限、越界、回退或跨窗，禁止用于本拍状态修正 | 04 |
| 测量平面 | Measurement Plane | 数值对应单体、簇直流侧、PCS 交流侧或并网点的位置口径 | 03 |

## A.3 状态空间与合成数据

| 中文 | 英文/缩写 | 软件定义 | 单位 | 首次详解 |
|---|---|---|---|---|
| 状态向量 | State Vector, `x[k]` | 时刻 `t[k]` 的隐藏状态，本课程基础模型含 SOC、动态偏移和滞回 | 混合单位 | 04/07 |
| 输入向量 | Input, `u[k]` | 与 `y[k]` 同窗、用于 `[t[k],t[k+1])` 推进的电流和温度 | A、°C | 04/07 |
| 量测 | Measurement, `y[k]` | 时刻 `t[k]` 的代表性单体端电压 | V | 04/07 |
| 状态函数 | Transition Function, `f` | 从 `x[k],u[k],dt[k]` 计算 `x[k+1]` | — | 07 |
| 输出函数 | Observation Function, `h` | 从 `x[k],u[k]` 计算同拍预测量测 | — | 07 |
| 动态电压偏移 | Dynamic Voltage Offset, `p` | 对输入历史指数响应的模型状态 | V | 07 |
| 滞回状态 | Hysteresis State, `h` | 表达充放方向历史和松弛的慢状态 | V | 06/07 |
| 时间常数 | Time Constant, `τ` | 指数动态的恢复时间尺度 | s | 07/08 |
| 恢复指数 | Recovery Factor, `a` | `exp(−dt/τ)`；`dt` 改变时必须重算 | 0～1 | 07/08 |
| 库仑效率 | Coulombic Efficiency, `η_c` | 外部充入电荷转为可恢复电荷的比例 | 0～1 | 07 |
| 电流偏置 | Current Bias, `b_I` | 测得电流相对真实输入的近似常偏差 | A | 07 |
| 合成真值 | Synthetic Ground Truth | 由可控模型产生、只供评分使用的隐藏状态和参数 | — | 07 |
| 故障注入 | Fault Injection | 向遥测注入噪声、偏置、丢包、延迟或参数失配 | — | 07 |
| 参数失配 | Parameter Mismatch | 真值器与估计器参数有意不同，用于验证模型不完美 | — | 07 |
| 真值泄漏 | Ground-truth Leakage | 把隐藏状态或参数回填给被测估计器，使测试虚假通过 | — | 07/08 |

“等效模型（Equivalent Model）”在本课程指能解释输入、状态和输出关系的低阶软件模型。它可与工程中的 ECM 参数对应，但本课程不要求读者实现电路或器件算法。

## A.4 OCV 与可观测性

| 中文 | 英文/缩写 | 软件定义 | 单位 | 首次详解 |
|---|---|---|---|---|
| 开路参考电压 | Open-Circuit Voltage, OCV | 指定 SOC、温度、方向历史和静置条件下的参考电压 | V | 06 |
| 温度分层表 | Temperature-layered Table | 多个温度节点的 OCV-SOC 表，层间再插值 | V | 06 |
| 分段线性插值 | Piecewise Linear Interpolation | 在相邻标定节点间按比例计算 | — | 06 |
| 表外输入 | Out-of-bounds, OOB | 超出 SOC、温度或电压标定范围的查询 | — | 06 |
| 充放电滞回 | Charge/Discharge Hysteresis | 同一 SOC 下，方向历史造成参考电压不同 | V | 06 |
| 静置松弛 | Rest Relaxation | 方向历史偏移随静置时间逐步衰减 | s、V | 06 |
| 局部导数 | Observation Slope, `H` | `dOCV/dSOC`，局部 SOC 变化映射成电压变化 | V/SOC | 06 |
| 量测噪声方差 | Measurement Variance, `R` | 电压量测误差的方差 | V² | 06/14 |
| 局部信息量 | Local Information, `H²/R` | 在其他状态已知的局部近似下，电压对 SOC 的信息强度 | 1/SOC² | 06 |
| 卡尔曼增益 | Kalman Gain, `K` | 把电压残差映射成 SOC 修正的权重 | SOC/V | 06/13 |
| 修正比例 | `K·H` | 局部先验 SOC 误差被量测修正的无量纲比例 | 0～1 | 06 |
| 可观测性 | Observability | 隐藏状态能否由输入输出历史区分；不等同于单点斜率 | — | 06/13 |

## A.5 参数与容量辨识

| 中文 | 英文/缩写 | 软件定义 | 首次详解 |
|---|---|---|---|
| 参数辨识 | Parameter Identification | 从输入输出数据估计模型参数并给出适用范围和残差 | 08 |
| 激励 | Excitation | 输入在幅值和时间尺度上提供足够变化，使参数可区分 | 08 |
| 可辨识性 | Identifiability | 给定数据是否能唯一或稳定地区分待估参数 | 08 |
| 动态特征 | `q[k]` | 由电流历史按候选恢复指数递推得到的回归特征 | 08 |
| 即时系数 | `r0` | 同拍电流对电压降的局部系数 | 08 |
| 动态系数 | `r_d` | 动态特征 `q` 对电压降的系数 | 08 |
| 电压截距 | `b_v` | 吸收近似常值 OCV/量测偏差的回归截距，不直接等同故障根因 | 08 |
| 最小二乘 | Least Squares, LS | 最小化残差平方和估计线性参数 | 08 |
| 网格搜索 | Grid Search | 在有界候选 `τ` 中逐一拟合并用验证误差选择 | 08 |
| 训练集 | Training Set | 用于拟合线性参数的数据 | 08 |
| 验证集 | Validation Set | 不参与拟合，用于选择和评价泛化的数据 | 08/10 |
| 残差 | Residual | `observed−predicted` | 08/13 |
| 均方根误差 | Root Mean Square Error, RMSE | `sqrt(mean(residual²))` | 08/21 |
| 残差均值 | Residual Mean | `mean(residual)`，用于检查系统偏差 | 08 |
| 递推最小二乘 | Recursive Least Squares, RLS | 每个样本更新一次参数及其不确定度的在线方法 | 10 深入 |
| 遗忘因子 | Forgetting Factor, `λ` | RLS 对历史数据降权的系数 | 10 深入 |
| 完整循环 | Full/Qualified Cycle | 起止端点和工况明确、SOC 跨度达到配置要求的容量证据 | 09 |

## A.6 状态估计、成组与运维

| 中文 | 英文/缩写 | 软件定义 | 首次详解 |
|---|---|---|---|
| 安时积分 | Coulomb Counting | 按电流和时间推进 SOC 的预测方法 | 前置 05a/本课 11 |
| 扩展卡尔曼滤波 | Extended Kalman Filter, EKF | 对非线性状态模型局部线性化后执行预测和量测修正 | 13 |
| 过程噪声 | Process Noise, `Q` | 模型和输入不确定度在状态预测中的表示 | 14 |
| 协方差 | Covariance, `P` | 状态估计器对误差相关性和方差的内部表示 | 13/14 |
| 标准差 | Standard Deviation, `σ` | 方差平方根，与对应状态同单位 | 14 |
| 在线诊断 | Online Diagnosis | 用质量、残差、边界和持续时间判断估计器状态 | 15 |
| 降级 | Degradation/Fallback | 输入或模型证据不足时减少量测修正、扩大余量或停用输出 | 15 |
| 簇 | Cluster | 站内可独立监视和退出的电池分组，本教程统一 416 串 | 19 |
| 堆 | Stack | 多簇聚合后的储能对象，本教程统一 12 簇 | 19 |
| 一致性 | Consistency | 单体或簇在 SOC、电压、温度、容量和能力上的差异 | 19 |
| 木桶效应 | Weakest-unit Effect | 放电受最低状态单元、充电受最高状态单元先到边界约束 | 19 |
| 极值频率 | Extreme Frequency | 某位置在可比较样本中反复成为最大/最小值的比例 | 19/20 |
| 均衡状态 | Balancing Status | BMS 上送的空闲、执行、完成或故障等软件状态 | 20 |
| 均衡效果 | Balancing Effect | 在可比较工况下，均衡前后差异指标的变化 | 20 |
| 运维闭环 | Maintenance Loop | 事件、证据、建议、处理、复测和关闭的全过程 | 20 |
| 回放 | Replay | 用固定数据、配置和版本重现算法输出 | 21 |
| 验收证据 | Acceptance Evidence | 输入版本、配置、指标、断言和业务结果的可审计集合 | 21 |

## A.7 统一符号和单位

| 符号 | 定义 | 单位/约定 |
|---|---|---|
| `k` | 离散采样索引 | 整数 |
| `t[k]` | 第 `k` 拍单调时间 | s |
| `dt[k]` | `t[k+1]−t[k]` | s，必须为正 |
| `x[k]` | 第 `k` 拍状态 | 混合单位 |
| `u[k]` | 第 `k` 拍输入 | 电流 A、温度 °C |
| `y[k]` | 第 `k` 拍单体电压量测 | V |
| `z[k]` | SOC 状态 | 0～1 |
| `I[k]` | 电流 | A，放电正、充电负 |
| `I_m[k]` | 测得电流 | A |
| `I*[k]` | 偏置修正电流 `I_m−b_I` | A |
| `b_I` | 电流偏置 | A |
| `T[k]` | 单体温度 | °C |
| `C_rated` | 额定容量 | Ah 或 kWh，字段必须区分 |
| `C_eff` | 单体有效容量 | Ah |
| `E_eff` | 站级有效能量 `C_site·SOH_capacity` | kWh |
| `E_internal` | 运行窗口内直流侧能量 `max(0,SOC_low−SOC_min)·E_eff` | kWh |
| `E_cell` | 单体名义能量 `C_cell·V_cell/1000` | kWh |
| `E_site` | 站级名义能量 `E_cell·N_s·N_p` | kWh |
| `E_dc` | 直流侧可交付能量 | kWh |
| `E_ac` | 交流侧可交付能量 `E_dc·η_DC→AC` | kWh |
| `C_cell` | 单体额定容量（正文简写 `C` 时同此） | Ah |
| `V_cell` | 单体标称电压（正文简写 `V` 时同此） | V |
| `η_c` | 充电库仑效率 | 0～1 |
| `η_DC→AC` | 直流到交流路径效率，只在跨平面时乘一次 | 0～1 |
| `η_bal` | 主动均衡转换效率 | 0～1 |
| `I_bal` | 均衡电流 | A |
| `Δt` | 均衡或回放区间时长 | s |
| `SOH_capacity` | 容量型健康度 `C_eff/C_rated` | 0～1 |
| `p[k]` | 动态电压偏移 | V |
| `h[k]` | 滞回电压偏移 | V |
| `r0` | 即时电流系数 | Ω |
| `r_d` | 动态电流系数 | Ω |
| `τ` | 恢复时间常数 | s |
| `a[k]` | `exp(−dt[k]/τ)` | 0～1 |
| `OCV(z,T,d,t_rest)` | 条件化参考电压 | V |
| `H` | `dOCV/dSOC` | V/SOC |
| `R` | 电压量测噪声方差 | V² |
| `P` | 状态或参数协方差 | 按元素单位组合 |
| `w[k]` | 过程噪声 | 按状态单位 |
| `v[k]` | 量测噪声 | V |
| `φ[k]` | 回归特征向量（第 08/10 章） | 混合单位 |
| `θ[k]` | 待估参数向量（第 10 章 RLS） | 混合单位 |
| `β` | 最小二乘闭式解参数向量（第 08 章） | 混合单位 |
| `K` | 状态修正增益 | SOC/V（标量示例） |
| `K[k]` | RLS 参数增益（第 10 章，与状态增益 `K` 区分） | 按参数单位组合 |
| `e[k]` / `e` | 残差序列及单拍残差（电压残差 `y−H·x⁻`；第 10 章 RLS 同符号） | V |
| `S` | 创新方差 `H·P⁻·Hᵀ+R` | V²（标量示例 `H²P+R`） |
| `ν` | 标准化残差 `e/√S` | 无量纲 |
| `NIS` | 标准化创新平方 `ν²` | 无量纲 |
| `k_risk` | 风险覆盖系数（如 1.96），不与采样索引 `k` 混用 | 无量纲 |
| `σ_SOC` | SOC 标准差 | SOC |
| `RMSE` | 均方根误差 | mV（电压）/ 无量纲（SOC） |
| `gap` | 泛化差距 `val_RMSE−train_RMSE` | mV |
| `bias` | 残差均值 `mean(y−ŷ)` | mV |
| `Q_net` | 循环积分净电量 | Ah |
| `N_s` | 每簇串联单体数 | 416 |
| `N_p` | 并联簇数 | 12 |
| `N` | 参与统计的簇数（本教程等于 `N_p`） | 簇 |
| `SOC_min` | 放电运行下限 | SOC，0～1 |
| `C_site` | 站级名义能量 `C_rated` | kWh |
| `E_cl` | 每簇名义能量 `C_cell·V_cell·N_s/1000` | kWh |
| `E_loss` | 均衡损耗能量 | kWh |
| `E_min` | 最低簇决定的可用能量 | kWh |
| `E_avg` | 平均 SOC 口径的可用能量 | kWh |
| `r` | 组内极差 `max−min` | SOC |
| `μ` | 组内均值 | SOC |
| `m` | 组内中位数基线 | SOC |
| `d` | 组内中位数绝对偏差 MAD（第 19 章）；第 06 章 `OCV(z,T,d,t_rest)` 中 `d` 表示充放方向历史 | SOC |
| `δ` | MAD 下限，防除零 | SOC |
| `score_i` | 鲁棒异常评分 `|SOC_i−m|/max(d,δ)` | 无量纲 |
| `m_est` | 估计风险余量（`k_risk·σ_SOC` 口径） | SOC |
| `m_est'` | 风险化后余量 `k_state·m_est` | SOC |
| `k_state` | 诊断状态系数（normal 1.0 / degraded 1.5） | 无量纲 |
| `ΔSOC_cluster` | 最低簇相对站级的保守差 | SOC |
| `SOE_AC` | 交流侧可用能量 | kWh |
| `σ_E` | 能量不确定度（1σ） | kWh |
| `P_energy(T)` | 指定时长的能量约束功率 | kW |
| `SOP(T)` | 指定方向与时长可交付功率 | kW |

## A.8 统一站点常量

| 常量 | 值 | 说明 |
|---|---:|---|
| `CELL_CAPACITY_AH` | 314 Ah | 代表性 LFP 单体额定容量 |
| `SERIES_CELLS` | 416 | 每簇串联单体数 |
| `PARALLEL_CLUSTERS` | 12 | 并联簇数 |
| `NOMINAL_CELL_V` | 3.2 V | 名义能量换算值 |
| `CLUSTER_NOMINAL_ENERGY_KWH` | 417.9968 kWh | `314×3.2×416/1000`，一簇的名义能量 |
| `SITE_NOMINAL_ENERGY_KWH` | 5015.9616 kWh | `314×3.2×416×12/1000` |
| `PCS_RATED_KW` | 2500 kW | PCS 额定有功教学值 |

这些常量统一存放在 [`lab/soc_core.py`](lab/soc_core.py)。正文按业务需要四舍五入写作“约 5.016 MWh”，代码保留精确乘积。修改统一对象时，应先改共享核心和测试，再检查全部章节的手算结果。

<!-- @AI_GENERATED: end -->