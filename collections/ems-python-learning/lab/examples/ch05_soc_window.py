"""第 05 章 5.7 最小闭环：用 ems_lab 的 SOC 窗口函数重跑降额 + 滞回追踪表。

输入：SOC 在 10% 附近波动的序列
算法：soc_window_factors（降额）+ SocPermissionGate（滞回）= soc_window_limits_kw
输出：每拍放电限值

运行（在 lab 目录下）：
    python examples/ch05_soc_window.py
"""
import sys
from pathlib import Path

# 直接运行脚本时 Python 只把 examples/ 放进搜索路径，这里补上 lab/ 以便导入 ems_lab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import SocPermissionGate, SocZones, soc_window_factors, soc_window_limits_kw  # noqa: E402

SOCS = [0.12, 0.099, 0.105, 0.115, 0.121, 0.13]


def main():
    zones = SocZones()                       # 默认阈值即正文的 [教学示例]
    gate = SocPermissionGate(zones, band=0.02)
    plain, gated = [], []
    for soc in SOCS:
        k = soc_window_factors(soc, zones)[1]                       # 只有降额
        _, p_dis = soc_window_limits_kw(soc, zones, 2500, 2500, gate)  # 降额 × 滞回许可
        plain.append(round(k * 2500))
        gated.append(round(p_dis))
        print(f"SOC {soc:5.1%}  k_放 {k:.2f}  只有降额 {k * 2500:6.0f} kW  降额+滞回 {p_dis:6.0f} kW")
    assert plain == [1000, 0, 250, 750, 1050, 1500]
    assert gated == [1000, 0, 0, 0, 1050, 1500]
    print("自检通过")

if __name__ == "__main__":
    main()

