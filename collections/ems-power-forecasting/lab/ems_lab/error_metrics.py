# @AI_GENERATED
"""第 07 章核心模块：预测误差指标（bias / MAE / RMSE / MAPE / 准确率 / 合格率）。

约定（对齐 07.x 手算、附录B）：
- 输入一组成对的并网点预测 P_hat 与实测 P_meas（时间对齐、已过第 04 章门控的好点）。
- 误差 e_i = P_hat_i − P_meas_i（预测 − 实测；正 = 高估、负 = 低估），单位 MW。
- bias = mean(e_i)（带符号，看方向）；MAE = mean(|e_i|)（看典型大小）；
  RMSE = sqrt(mean(e_i²))（看极端程度，大误差被平方放大）。
- MAPE = mean(|e_i| / P_meas_i) × 100（百分数，看相对占比）；零实测点按 drop_zero 剔除，
  剔除后无有效样本返回 0.0（全零边界）。
- 准确率 = (1 − RMSE / P_nom) × 100（百分数，RMSE 归一化到装机容量）；
  合格率 = (|e_i| ≤ 门槛的样本占比) × 100（百分数，离散计数）。

教学示例默认值（对齐 07.x 手算，主线 30 MW 光伏）：
- 主案例 6 点：P_hat = [9, 9, 15, 9, 6, 2]，P_meas = [6, 10, 16, 10, 6, 2]
  -> e = [+3, −1, −1, −1, 0, 0] -> bias=0.0、MAE=1.0、RMSE=sqrt(2)≈1.414、MAPE≈12.71%
- 准确率 = (1 − 1.414/30)×100 ≈ 95.29%；合格率（门槛 2 MW）= 5/6×100 ≈ 83.33%
"""
from __future__ import annotations

import math

P_NOM = 30.0           # 装机容量（归一化基准）MW，对齐主线 30 MW 光伏
PASS_THRESHOLD = 2.0   # 合格率门槛（教学示例）MW


def _check_paired(p_hat: list[float], p_meas: list[float]) -> None:
    """校验预测与实测成对且非空。"""
    if len(p_hat) != len(p_meas):
        raise ValueError(f"预测与实测样本数须一致，实际 {len(p_hat)} vs {len(p_meas)}")
    if len(p_hat) == 0:
        raise ValueError("预测/实测序列不能为空")


def error_list(p_hat: list[float], p_meas: list[float]) -> list[float]:
    """逐点误差 e_i = P_hat_i − P_meas_i（正 = 高估、负 = 低估）。

    主案例：error_list([9,9,15,9,6,2], [6,10,16,10,6,2]) -> [3, -1, -1, -1, 0, 0]。
    """
    _check_paired(p_hat, p_meas)
    return [h - m for h, m in zip(p_hat, p_meas)]


def mean_error(p_hat: list[float], p_meas: list[float]) -> float:
    """偏差 bias = mean(e_i)，保留符号（正 = 系统性高估、负 = 系统性低估）。

    主案例：mean_error([9,9,15,9,6,2], [6,10,16,10,6,2]) -> 0.0。
    """
    errs = error_list(p_hat, p_meas)
    return sum(errs) / len(errs)


def mean_absolute_error(p_hat: list[float], p_meas: list[float]) -> float:
    """MAE = mean(|e_i|)，平均绝对误差（典型大小，每个误差等权）。

    主案例：mean_absolute_error(...) -> 1.0。
    """
    errs = error_list(p_hat, p_meas)
    return sum(abs(e) for e in errs) / len(errs)


def root_mean_square_error(p_hat: list[float], p_meas: list[float]) -> float:
    """RMSE = sqrt(mean(e_i²))，均方根误差（大误差被平方放大）。

    主案例：root_mean_square_error(...) -> sqrt(2) ≈ 1.41421356。
    """
    errs = error_list(p_hat, p_meas)
    return math.sqrt(sum(e * e for e in errs) / len(errs))


def mean_absolute_percentage_error(p_hat: list[float], p_meas: list[float],
                                   drop_zero: bool = True) -> float:
    """MAPE = mean(|e_i| / P_meas_i) × 100（百分数，看相对占比）。

    drop_zero=True 时剔除 P_meas==0 的点（零分母边界）；剔除后无有效样本返回 0.0（全零边界）。
    主案例：mean_absolute_percentage_error(...) -> 12.7083...%。
    """
    _check_paired(p_hat, p_meas)
    pairs = [(h, m) for h, m in zip(p_hat, p_meas) if not (drop_zero and m == 0.0)]
    if not pairs:
        return 0.0
    return sum(abs(h - m) / m for h, m in pairs) / len(pairs) * 100.0


def accuracy_rmse(p_hat: list[float], p_meas: list[float],
                  p_nom: float = P_NOM) -> float:
    """准确率 = (1 − RMSE / p_nom) × 100（百分数，RMSE 归一化到装机容量）。

    主案例：accuracy_rmse(...) -> (1 − 1.41421356/30)×100 ≈ 95.2859%。
    """
    if p_nom <= 0.0:
        raise ValueError(f"装机容量必须为正，实际 {p_nom}")
    return (1.0 - root_mean_square_error(p_hat, p_meas) / p_nom) * 100.0


def pass_rate(p_hat: list[float], p_meas: list[float],
              threshold: float = PASS_THRESHOLD) -> float:
    """合格率 = (|e_i| ≤ threshold 的样本占比) × 100（百分数，离散计数）。

    主案例：pass_rate(..., threshold=2.0) -> 5/6×100 ≈ 83.3333%。
    """
    if threshold < 0.0:
        raise ValueError(f"合格率门槛不能为负，实际 {threshold}")
    errs = error_list(p_hat, p_meas)
    ok = sum(1 for e in errs if abs(e) <= threshold)
    return ok / len(errs) * 100.0
# @AI_GENERATED: end