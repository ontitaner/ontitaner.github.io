# @AI_GENERATED
"""第 08 章核心模块：预测考核口径与统计窗口（两个细则条款的可计算化）。

约定（对齐 08.x 手算、附录B）：
- 考核以自然月为统计窗口：月准确率 = 整月有效点一起算 RMSE -> (1 − RMSE/P_nom)×100。
  关键口径：先聚合误差（整月 RMSE）再算指标，不是"分日准确率再平均"。
- 剔除规则：限电 / 检修 / 数据异常 / 零出力时段的点不参与考核统计（误差不代表预测能力），
  剔除依据必须可溯源（调度限电指令、检修票、异常日志）。
- 四道考核项 [教学示例]：短期准确率 >= 80%、合格率 >= 90%、上报率 >= 99%
  （超短期准确率 >= 85% 见正文）。任何一道不达标都要扣分，不是"平均达标"。

教学示例默认值（对齐 08.x 手算，主线 30 MW 光伏）：
- P_nom = 30 MW、单点合格门槛 2 MW（复用 07 章）
- 主案例 6 点：p_hat=[20,25,22,18,24,26]、p_meas=[18,24,21,18,12,14]
  误差 e=[+2,+1,+1,0,+12,+12]（后两点为限电/检修，exclude=[F,F,F,F,T,T]）
  整月一起算 RMSE=7.0 -> 76.67%（不合格）；分日平均=84.12%（口径不同结论相反）
  剔除后 RMSE=sqrt(1.5)≈1.2247 -> 95.92%（合格）；合格率 4/4=100%
"""
from __future__ import annotations

from ems_lab.error_metrics import accuracy_rmse, pass_rate

P_NOM = 30.0                 # 装机容量（归一化基准）MW
ACC_THRESHOLD = 80.0         # 短期预测准确率门槛 % [教学示例]
PASS_RATE_THRESHOLD = 90.0   # 预测合格率门槛 % [教学示例]
REPORT_RATE_THRESHOLD = 99.0  # 上报率门槛 % [教学示例]
POINT_THRESHOLD = 2.0        # 单点合格门槛 MW（复用 07 章）


def monthly_accuracy(p_hat: list[float], p_meas: list[float],
                     p_nom: float = P_NOM) -> float:
    """月准确率 = 整月有效点一起算 RMSE -> (1 − RMSE/p_nom)×100。

    主案例 6 点：monthly_accuracy([20,25,22,18,24,26], [18,24,21,18,12,14])
    -> 整月 RMSE=7.0 -> 76.666...%。
    """
    return accuracy_rmse(p_hat, p_meas, p_nom)


def filter_valid(p_hat: list[float], p_meas: list[float],
                 exclude: list[bool]) -> tuple[list[float], list[float]]:
    """按剔除掩码过滤无效点（exclude[i]=True 表示剔除）。

    返回 (有效预测, 有效实测)；三者长度须一致。全剔除返回空序列（无有效样本）。
    """
    if len(p_hat) != len(p_meas) or len(p_hat) != len(exclude):
        raise ValueError(
            f"预测/实测/剔除掩码长度须一致，实际 {len(p_hat)} vs {len(p_meas)} vs {len(exclude)}"
        )
    return ([p for p, x in zip(p_hat, exclude) if not x],
            [p for p, x in zip(p_meas, exclude) if not x])


def monthly_accuracy_excluding(p_hat: list[float], p_meas: list[float],
                               exclude: list[bool], p_nom: float = P_NOM) -> float:
    """剔除后月准确率：先过滤限电/检修/异常点，再整月一起算 RMSE。

    主案例剔除后 4 点：-> (1 − sqrt(1.5)/30)×100 ≈ 95.9175%。
    """
    p_hat_v, p_meas_v = filter_valid(p_hat, p_meas, exclude)
    return accuracy_rmse(p_hat_v, p_meas_v, p_nom)


def monthly_pass_rate(p_hat: list[float], p_meas: list[float],
                      exclude: list[bool], threshold: float = POINT_THRESHOLD) -> float:
    """有效点合格率 = (|e_i| <= threshold 的样本占比)×100。

    主案例剔除后 4 点（|e|=[2,1,1,0]）-> 4/4×100 = 100.0%。
    """
    p_hat_v, p_meas_v = filter_valid(p_hat, p_meas, exclude)
    return pass_rate(p_hat_v, p_meas_v, threshold)


def report_rate(reported: int, expected: int) -> float:
    """上报率 = 实报点数 / 应报点数 × 100（百分数）。

    主案例：应报 2880 点、实报 2784 点 -> 96.666...%。
    """
    if expected <= 0:
        raise ValueError(f"应报点数须为正，实际 {expected}")
    return reported / expected * 100.0


def assess(accuracy: float, pass_rate_val: float, report_rate_val: float) -> dict:
    """考核判定：返回各考核项是否达标（bool）。

    主案例：assess(95.92, 100.0, 96.67)
    -> {'accuracy_ok': True, 'pass_rate_ok': True, 'report_rate_ok': False}
    """
    return {
        "accuracy_ok": accuracy >= ACC_THRESHOLD,
        "pass_rate_ok": pass_rate_val >= PASS_RATE_THRESHOLD,
        "report_rate_ok": report_rate_val >= REPORT_RATE_THRESHOLD,
    }
# @AI_GENERATED: end