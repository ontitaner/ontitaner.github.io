"""第 05 章 5.4 最小闭环：用 ems_lab 的 OCV 查表函数重跑三次静置的校准决策。

输入：静置电压、静置时长、积分估计 SOC
算法：静置判定 → soc_from_ocv 查表 → soc_error_from_voltage_error 求不确定度 → 门限判定
输出：校准后 SOC 与决策原因

运行（在 lab 目录下）：
    python examples/ch05_ocv_calibration.py
"""
import sys
from pathlib import Path

# 直接运行脚本时 Python 只把 examples/ 放进搜索路径，这里补上 lab/ 以便导入 ems_lab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import CoulombCounter, soc_error_from_voltage_error, soc_from_ocv  # noqa: E402

DV_METER = 0.005     # ΔV：电压测量误差（V）
MAX_UNCERT = 0.01    # 不确定度门限 [教学示例]
MIN_REST_MIN = 60    # 最短静置时长（min）[教学示例]

# (场景, 真实 SOC, 积分估计 SOC, 实测静置电压 V, 静置时长 min)
CASES = [("A 低端静置", 0.07, 0.035, 3.145, 120),
         ("B 平台区静置", 0.45, 0.43, 3.300, 120),
         ("C 静置不足", 0.07, 0.035, 3.160, 10)]


def try_ocv_calibration(counter, v_rest, rest_min):
    """可信才调用 calibrate() 覆盖积分值；返回决策原因。"""
    if rest_min < MIN_REST_MIN:
        return "放弃：静置不足"
    soc_ocv = soc_from_ocv(v_rest)                              # 查表 f⁻¹
    uncert = soc_error_from_voltage_error(DV_METER, soc_ocv)    # ΔSOC = ΔV / k
    if uncert > MAX_UNCERT:
        return f"放弃：不确定度 {uncert:.2%}"
    counter.calibrate(soc_ocv)                                  # 采用：覆盖积分值，吞吐量清零
    return f"采用：不确定度 {uncert:.2%}"


def main():
    results = []
    for name, soc_true, soc_est, v, rest in CASES:
        cc = CoulombCounter(314, soc_est)
        why = try_ocv_calibration(cc, v, rest)
        results.append(cc.soc)
        print(f"{name:<8}校准前 {soc_est - soc_true:+.2%}  校准后 {cc.soc:.2%}（{cc.soc - soc_true:+.2%}）  {why}")
    assert abs(results[0] - 0.0725) < 1e-9
    assert results[1] == 0.43 and results[2] == 0.035
    print("自检通过")

if __name__ == "__main__":
    main()

