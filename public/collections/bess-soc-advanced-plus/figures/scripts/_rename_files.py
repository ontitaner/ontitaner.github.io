import os, sys

base = r"d:\ontitaner\ai-practice\sub_module\ontitaner.github.io\public\collections\bess-soc-advanced-plus"
renames = [
    ("21_业务回放与履约验证.md", "25_业务回放与履约验证.md"),
    ("20_均衡评估与运维闭环.md", "24_均衡评估与运维闭环.md"),
    ("19_成组一致性与异常检测.md", "23_成组一致性与异常检测.md"),
    ("18_风险化能力与调度决策.md", "22_风险化能力与调度决策.md"),
    ("17_持续功率SOP评估.md", "21_持续功率SOP评估.md"),
    ("16_可用能量SOE估计.md", "20_SOE能量状态估计.md"),
    ("15_在线诊断与可信度降级.md", "19_在线诊断与可信度降级.md"),
    ("14_协方差与噪声整定.md", "18_协方差与噪声整定.md"),
    ("13_扩展卡尔曼滤波.md", "17_扩展卡尔曼滤波.md"),
    ("12_开环漂移机理.md", "14_开环漂移机理.md"),
    ("11_安时积分与SOC递推.md", "13_安时积分与SOC递推.md"),
    ("10_参数验证与版本治理.md", "11_参数验证与版本治理.md"),
    ("09_有效容量与SOH标定.md", "10_SOH与可用容量分析.md"),
    ("08_模型参数辨识.md", "09_模型参数辨识.md"),
    ("07_等效电路与状态空间建模.md", "08_等效电路与状态空间建模.md"),
    ("06_OCV特性与可观测性.md", "07_OCV特性与可观测性.md"),
]

log_path = os.path.join(base, "img", "_rename_log.txt")
with open(log_path, "w") as f:
    for old, new in renames:
        oldpath = os.path.join(base, old)
        newpath = os.path.join(base, new)
        f.write(f"Check: {oldpath}\n")
        if os.path.exists(oldpath):
            os.rename(oldpath, newpath)
            f.write(f"OK: {old} -> {new}\n")
        else:
            f.write(f"SKIP: {old} not found\n")
    f.write("DONE\n")