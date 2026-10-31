<!-- @AI_GENERATED -->
# 储能 SOC/SOE/SOP 进阶课程（优化版）：从数据到履约

本课程面向储能转行入门者、在校学生，以及希望深入 SOC/SOE/SOP 工程实践的专业人士。它从软件与业务协同视角解释储能状态估计、可信度传播、一致性运维和履约验证；不设计采样电路、均衡器件或 BMS 固件算法。目标是让读者逐步回答三个问题：输入数据能不能用，状态估计为什么可信，业务承诺为什么能或不能履约。

全课程围绕同一个晚峰案例：**17:30 观测到 SOC，18:00 要求以 2 MW 放电 30 分钟**。26 章逐步消除其中的每一类未知，最后在第 25 章形成可复现的履约证据。

## 读者与学习路径

| 读者 | 目标 | 建议路径 |
|---|---|---|
| 转行入门者 | 看懂业务与状态关系 | 主线通读，公式可略 |
| 学生 / 算法入门 | 能手算、跑最小代码、复现结论 | 主线 + 两步手算 + lab |
| EMS/BMS/运维工程师 | 掌握数据质量、参数版本、风险能力与验收 | 全读，侧重边界与深入 |

## 学习约定

- **先读主线，再按需深入**：正文先用晚峰任务、图表和直白结论建立直觉；公式推导与算法变体放入"深入"折叠。首次术语给中文、英文/缩写、一句话解释，统一定义见[附录 A](附录A_术语与符号词典.md)。
- **算法可复算、代码可运行**：算法章先给符号公式块（含变量、单位与适用条件），再给至少两步连续手算；手算数值须与所在章公式小节和附录 A.8 常量一致。完整标准库实现在 `lab/`，每个实验含 `main()` 与 `test_*` 自检。
- **合成数据先于现场结论**：真值器生成已知状态再注入噪声/偏置/丢包/延迟/失配；隐藏真值只用于评分，禁止回填估计器。
- **算法与业务口径分开**：教学参数均为 `[教学示例]`；未核验的标准或合同条款不得用于宣称合规或验收通过。
- **图表可重复生成**：`lab/` 只依赖标准库；`figures/scripts/` 是可选制图工具（需 matplotlib），固定种子、输出到 `img/`，不进入教程运行期依赖。

## 统一对象与口径

| 项目 | 统一值 | 用途 |
|---|---:|---|
| 单体额定容量 | 314 Ah | 状态模型与容量辨识 |
| 每簇串联数 | 416 | 单体换算到簇 |
| 并联簇数 | 12 | 站级容量与聚合 |
| 单体标称电压 | 3.2 V | 名义能量换算 |
| 名义能量 | `314×3.2×416×12/1000 = 5015.96 kWh` | 约 5.016 MWh |
| PCS 额定有功 | 2500 kW | 履约与 SOP 场景 |
| 方向 | 放电为正、充电为负 | 电流与功率统一 |
| 时间 | 秒，用本地单调时间算 `dt` | 设备时间只作来源与诊断 |
| SOC | 代码 0～1，正文可写百分比 | 禁止 50 与 0.50 混用 |

## 26 章课程目录

| 章 | 主题 | 对应 lab | 主图 |
|---|---|---|---|
| [00](00_课程导读与履约主线.md) | 课程导读：从荷电状态到履约能力 | — | — |
| [01](01_系统架构与职责边界.md) | 储能系统构成与 BMS/PCS/EMS/电网职责边界 | — | 架构图(Mermaid) |
| [02](02_SOC_SOE_SOH_SOP状态体系.md) | 核心状态量辨析：SOC、SOE、SOH 与 SOP | — | 能力漏斗(Mermaid) |
| [03](03_遥测来源与测量平面.md) | 遥测来源与单体/簇/直流/交流/并网测量平面 | ch01 | — |
| [04](04_时序对齐与质量门控.md) | 采样时序对齐与数据质量门控 | ch01 | 时序图(Mermaid) |
| [05](05_容量电量与能量换算.md) | 容量、电量、电压与能量的工程换算 | ch02 | 换算链(Mermaid) |
| [06](06_OCV-SOC曲线构建.md) | OCV-SOC 曲线构建、温度与滞回标定 | ch03 | ocv_calibration |
| [07](07_OCV特性与可观测性.md) | OCV 特性：斜率、可观测性与信息量瓶颈 | ch03 | ocv_curve_slope |
| [08](08_等效电路与状态空间建模.md) | 一阶 RC 等效电路与状态空间建模 | ch02 | ecm_pulse |
| [09](09_模型参数辨识.md) | 模型参数辨识：R0、R1 与恢复时间常数 τ | ch04 | identify_pulse |
| [10](10_SOH与可用容量分析.md) | 有效容量 C_eff 与容量型 SOH 标定 | ch04 | soh_capacity |
| [11](11_参数验证与版本治理.md) | 参数验证、版本发布与适用域治理 | ch04 | 发布卡(表格) |
| [12](12_初始SOC获取.md) | 初始 SOC 获取：静置 OCV 查表 | ch05 | initial_soc |
| [13](13_安时积分与SOC递推.md) | 安时积分法与 SOC 递推 | ch05 | — |
| [14](14_开环漂移机理.md) | 开环漂移机理：初值误差与电流零漂 | ch05 | coulomb_drift |
| [15](15_自放电.md) | 自放电机理与静置 SOC 修正 | ch05 | self_discharge |
| [16](16_SOC校准与重置.md) | SOC 校准：满充/满放事件检测与重置 | ch05 | soc_calibration |
| [17](17_扩展卡尔曼滤波.md) | 扩展卡尔曼滤波：预测与量测修正 | ch05 | ekf_convergence |
| [18](18_协方差与噪声整定.md) | 协方差传播与过程/量测噪声整定 | ch06 | uncertainty_band |
| [19](19_在线诊断与可信度降级.md) | 在线诊断：残差、NIS 与可信度降级 | ch06 | uncertainty_band |
| [20](20_SOE能量状态估计.md) | 从 SOC 到可用能量 SOE | ch07 | — |
| [21](21_持续功率SOP评估.md) | 从 SOE 到指定时长持续功率 SOP | ch07 | soe_sop_limits |
| [22](22_风险化能力与调度决策.md) | 风险化能力评估与 EMS 调度决策 | ch07 | — |
| [23](23_成组一致性与异常检测.md) | 成组一致性、最低簇与异常检测 | ch08 | cell_divergence |
| [24](24_均衡评估与运维闭环.md) | 均衡效果评估与运维闭环 | ch09 | balancing_convergence |
| [25](25_业务回放与履约验证.md) | 业务回放、履约验证与验收证据 | ch10 | ch10_business_replay_evidence |
| [附录 A](附录A_术语与符号词典.md) | 术语与符号词典 | — | — |

说明：lab 实验以第 03–25 章解决的核心算法为单位组织，多个章节可共享同一实验（如 13–17 章共享 `ch05`）；正文均注明对应实验。

## 共享代码结构

```text
lab/soc_core.py                      统一常量、质量门控、OCV、状态模型、统计与辨识
lab/ch01_data_contract.py            数据异常、同窗对齐和错拍（第03–04章）
lab/ch02_state_space.py              不规则 dt 与真值故障注入（第05、08章）
lab/ch03_ocv_observability.py        温度/滞回/松弛和 H²/R（第06–07章）
lab/ch04_identification.py           带噪拟合、训练验证、有效容量（第09–11章）
lab/ch05_production_ekf.py           安时积分基线与三状态 EKF（第12–17章）
lab/ch06_uncertainty_diagnostics.py  不确定度传播、残差和降级诊断（第18–19章）
lab/ch07_soe_sop.py                  交流侧 SOE、指定时长 SOP 与风险化（第20–22章）
lab/ch08_group_anomaly.py            最低簇能力、MAD 评分和异常事件（第23章）
lab/ch09_balancing_effect.py         同工况均衡效果与运维关闭链（第24章）
lab/ch10_business_replay.py          冻结输入的计划、能力和实际回放（第25章）
```

## 运行课程实验

从本目录执行全部标准库实验和自检：

```powershell
python lab/ch01_data_contract.py
python lab/ch02_state_space.py
python lab/ch03_ocv_observability.py
python lab/ch04_identification.py
python lab/ch05_production_ekf.py
python lab/ch06_uncertainty_diagnostics.py
python lab/ch07_soe_sop.py
python lab/ch08_group_anomaly.py
python lab/ch09_balancing_effect.py
python lab/ch10_business_replay.py

python -m pytest -q -p no:cacheprovider lab
```

每个实验都能直接运行并提供 `test_*` 自检。`pytest` 只用于执行测试，课程实现仍只使用 Python 标准库。

## 生成课程图表（可选）

结构/流程类图（架构、能力漏斗、换算链、发布卡）直接用章节内的 Mermaid 或表格呈现，无需脚本。下列数据图由脚本生成，不是 lab 的运行期依赖；仅在重新生成 `img/` 图片时安装并执行：

```powershell
python -m pip install ".[figures]"
python figures/scripts/fig_arch_decision.py            # 01 架构决策
python figures/scripts/fig_measurement_planes.py      # 03 测量平面
python figures/scripts/fig_data_misalignment_impact.py  # 04 错拍与能力误判
python figures/scripts/fig_ocv_calibration.py         # 06 OCV 标定
python figures/scripts/fig_ocv_slope.py               # 07 OCV 斜率
python figures/scripts/fig_ocv_decision_map.py        # 07 OCV 校准决策
python figures/scripts/fig_ecm_pulse.py               # 08 ECM 脉冲响应
python figures/scripts/fig_identify.py                # 09 参数辨识
python figures/scripts/fig_soh_capacity.py            # 10 容量标定
python figures/scripts/fig_initial_soc.py             # 12 初始 SOC
python figures/scripts/fig_coulomb_drift.py           # 14 开环漂移
python figures/scripts/fig_open_loop_error_components.py  # 14 开环误差分解
python figures/scripts/fig_self_discharge.py          # 15 自放电
python figures/scripts/fig_soc_calibration.py         # 16 SOC 校准
python figures/scripts/fig_ekf_convergence.py         # 17 EKF 收敛
python figures/scripts/fig_ekf_update_explained.py    # 17 单次更新分解
python figures/scripts/fig_uncertainty_band.py        # 18–19 协方差/能量带
python figures/scripts/fig_soe_sop_limits.py          # 21 SOP 约束取最小
python figures/scripts/fig_sop_duration_curve.py      # 21 时长—功率曲线
python figures/scripts/fig_cell_divergence.py         # 23 木桶与异常评分
python figures/scripts/fig_cluster_capacity_compare.py  # 23 最低簇能量对比
python figures/scripts/fig_balancing.py               # 24 均衡与运维
python figures/scripts/fig_validation.py              # 25 业务回放证据
```

数据图统一使用白底主题（`figures/scripts/_figstyle.py`）：固定随机种子、中文字体自动探测、结论式标题。

## 全教程验收原则

1. 先证明输入样本同单位、同方向、同测量平面、同采样窗口。
2. 再证明状态转移和量测使用同一时序约定。
3. 合成真值与估计配置必须隔离，不能用真值参数帮助估计器过关。
4. 查表范围、质量状态和参数边界必须显式处理，不允许静默夹值或静默丢弃错误。
5. 训练集用于选参数，验证集用于评价泛化；报告 RMSE 也报告残差均值。
6. 最终输出必须回到晚峰履约：能承诺多少功率、持续多久、余量来自哪里、限制原因是什么。

<!-- @AI_GENERATED: end -->