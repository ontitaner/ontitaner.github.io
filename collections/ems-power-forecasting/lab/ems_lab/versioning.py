# @AI_GENERATED
"""第 12 章核心模块：预测模型版本治理与再训练。

约定（对齐 05/07/08 章手算、附录B/C）：
- 版本治理五步闭环：漂移检测 -> 训练/验证时间隔离 -> 再训练 -> 发布卡 -> 上线后回滚卡。
- 漂移检测：对比"近期窗口偏差 bias_recent"与"上线时训练基准 bias_train"，
  绝对值 >= 阈值判漂移（等号算触发）。
- 时间隔离：按时间先后切分训练集/验证集（禁止随机切，避免用未来数据泄漏）。
- 再训练：复用 05 章 fit_bin_bias 用近期训练集重估分箱偏差 -> 新版本 bias。
- 发布卡：新版本验证集 RMSE < 旧版本 且 准确率 >= 门槛，才允许发布。
- 回滚卡：新版本上线后线上 RMSE > 上一版本基线，则回滚到上一版本。

教学示例默认值（对齐 05/07/08 章，主线 30 MW 光伏）：
- 分箱边界 [5, 20]；v1 分箱偏差 = [+0.5, -0.9, -2.25]（05 章锚定）
- 漂移阈值 DRIFT_THRESHOLD = 1.0 MW、发布卡准确率门槛 80%（复用 08 章）
- 主案例：正午（箱3）偏差从 -2.25 漂到 -3.25（组件老化，物理高估加剧）
  -> 漂移 |-1.0| >= 1.0 触发 -> 再训练 v2 = [+0.5, -0.9, -3.25]
  -> 验证集 v1 RMSE=1.25、v2 RMSE=0.25 -> 发布卡通过。
"""
from __future__ import annotations

from ems_lab.error_metrics import root_mean_square_error
from ems_lab.shortterm import bias_correct, fit_bin_bias

DRIFT_THRESHOLD = 1.0       # 漂移告警阈值 MW [教学示例]
P_NOM = 30.0                # 装机容量（归一化基准）MW，复用 07 章
ACC_THRESHOLD = 80.0        # 发布卡准确率门槛 %，复用 08 章
BIN_EDGES = [5.0, 20.0]     # 分箱边界 MW，复用 05 章
BIAS_V1 = [0.5, -0.9, -2.25]  # v1 上线时分箱偏差，05 章锚定


def detect_drift(bias_recent: float, bias_train: float,
                 threshold: float = DRIFT_THRESHOLD) -> bool:
    """漂移检测：|bias_recent - bias_train| >= threshold 判漂移（等号算触发）。

    主案例：detect_drift(-3.25, -2.25) -> |-1.0| = 1.0 >= 1.0 -> True。
    边界语义：|漂移| 恰好等于阈值也触发（>= 不是 >）。
    """
    return abs(bias_recent - bias_train) >= threshold


def time_split(p_phys: list[float], p_meas: list[float],
               split_idx: int) -> tuple[tuple[list, list], tuple[list, list]]:
    """训练/验证时间隔离：前 split_idx 个样本为训练集，之后为验证集。

    按时间先后切分（禁止随机切），避免"用未来数据评估过去模型"的泄漏。
    返回 ((训练 P_phys, 训练 P_meas), (验证 P_phys, 验证 P_meas))。
    """
    if len(p_phys) != len(p_meas):
        raise ValueError(f"物理与实测样本数须一致，实际 {len(p_phys)} vs {len(p_meas)}")
    if split_idx <= 0 or split_idx >= len(p_phys):
        raise ValueError(f"切分点须在 1..{len(p_phys) - 1} 之间，实际 {split_idx}")
    return ((p_phys[:split_idx], p_meas[:split_idx]),
            (p_phys[split_idx:], p_meas[split_idx:]))


def retrain_bias(p_phys_train: list[float], p_meas_train: list[float],
                 bin_edges: list = BIN_EDGES) -> list[float]:
    """再训练：复用 05 章 fit_bin_bias，用近期训练集重估分箱偏差 -> 新版本 bias。

    主案例（近期训练集 7 点）：
      P_phys=[2,3, 10,15, 20,22,24]、P_meas=[2.5,3.5, 9.1,14.1, 16.75,18.75,20.75]
      -> 箱1=+0.5、箱2=-0.9、箱3=-3.25 -> v2 = [+0.5, -0.9, -3.25]。
    """
    return fit_bin_bias(p_phys_train, p_meas_train, bin_edges)


def rmse_of(p_phys: list[float], p_meas: list[float], bias: list[float],
            bin_edges: list = BIN_EDGES) -> float:
    """给定分箱偏差，在样本集上算预测 P_hat = P_phys + bias[箱]，返回 RMSE。

    复用 05 章 bias_correct + 07 章 RMSE；用于发布卡/回滚卡评估。
    主案例（验证集 4 点）：
      v1 bias=[0.5,-0.9,-2.25] -> RMSE=1.25；v2 bias=[0.5,-0.9,-3.25] -> RMSE=0.25。
    """
    p_hat = [bias_correct(p, bin_edges, bias) for p in p_phys]
    return root_mean_square_error(p_hat, p_meas)


def release_check(rmse_new: float, rmse_prev: float,
                  p_nom: float = P_NOM, acc_threshold: float = ACC_THRESHOLD) -> dict:
    """发布卡：新版本验证集 RMSE < 旧版本 且 新版本准确率 >= 门槛，才允许发布。

    返回 {"improved", "accuracy", "accuracy_ok", "release"}。
    主案例：release_check(0.25, 1.25)
      -> improved=True、accuracy=(1-0.25/30)x100=99.17%、release=True。
    """
    improved = rmse_new < rmse_prev
    acc = (1.0 - rmse_new / p_nom) * 100.0
    accuracy_ok = acc >= acc_threshold
    return {"improved": improved, "accuracy": acc,
            "accuracy_ok": accuracy_ok, "release": improved and accuracy_ok}


def should_rollback(rmse_online: float, rmse_baseline: float) -> bool:
    """回滚卡：新版本上线后线上 RMSE > 上一版本基线，则回滚到上一版本。

    主案例（高温季 v2 表现恶化）：should_rollback(1.5, 1.25) -> True（回滚）。
    """
    return rmse_online > rmse_baseline
# @AI_GENERATED: end