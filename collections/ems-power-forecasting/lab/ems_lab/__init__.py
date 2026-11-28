# @AI_GENERATED
"""ems_lab -- 新能源功率预测课程三层代码体系的第二层和第三层

ems_lab/   : 真实模块，可 from ems_lab import ...
examples/  : 逐章端到端可运行脚本
tests/     : 一致性测试，确保正文手算 == 模块输出

各章模块规划（随章节逐步落地，函数签名与数值以正文手算为准）：

- irradiance   : 辐照->光伏出力转换（第 03 章）
- power_curve  : 风速->风机出力转换（第 03 章）
- nwp_quality  : NWP 气象数据质量门控（第 04 章）
- shortterm    : 短期功率预测建模（第 05 章）
- ultrashort   : 超短期功率预测与滚动外推（第 06 章）
- error_metrics: 预测误差指标（第 07 章）
- assessment   : 预测考核口径与统计窗口（第 08 章）
- loss_forward : 误差->排程/报价收益损失传导（第 09/10 章）
- pipeline     : 预测 EMS 流水线与数据契约（第 11 章）
- versioning   : 预测模型版本治理与再训练（第 12 章）
- acceptance   : 预测并网验收与证据链（第 13 章）
- diagnosis    : 预测偏差根因诊断（第 14 章）
"""