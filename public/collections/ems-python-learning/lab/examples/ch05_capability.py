"""第 05 章 5.11 最小闭环：用 ems_lab 的能力模型函数重跑一上午三个时刻的瓶颈。

输入：各时刻 SOC、BMS 直流能力、负荷
算法：ac_limits_from_dc + soc_window_limits_kw + combine_capability
输出：可充/可放和各自瓶颈

运行（在 lab 目录下）：
    python examples/ch05_capability.py
"""
import sys
from pathlib import Path

# 直接运行脚本时 Python 只把 examples/ 放进搜索路径，这里补上 lab/ 以便导入 ems_lab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import SocZones, ac_limits_from_dc, combine_capability, soc_window_limits_kw  # noqa: E402

P_PCS, P_DEMAND, P_AUX, ETA_PCS = 2500.0, 4000.0, 50.0, 0.98
SNAPSHOTS = [("07:00", 0.80, 1470, 2500, 2000),
             ("10:00", 0.84, 2400, 2500, 2600),
             ("12:00", 0.88, 2400, 2500, 800)]


def main():
    zones = SocZones()
    got = []
    for when, soc, chg_dc, dis_dc, load in SNAPSHOTS:
        bms_chg, bms_dis = ac_limits_from_dc(chg_dc, dis_dc, ETA_PCS)       # 直流 → 交流
        win_chg, win_dis = soc_window_limits_kw(soc, zones, P_PCS, P_PCS)   # SOC 窗口
        cap = combine_capability(
            {"BMS": bms_chg, "PCS": P_PCS, "SOC窗口": win_chg, "需量": P_DEMAND - load - P_AUX},
            {"BMS": bms_dis, "PCS": P_PCS, "SOC窗口": win_dis, "防倒送": load + P_AUX})
        got.append((round(cap.available_charge_kw), cap.charge_limited_by,
                    round(cap.available_discharge_kw), cap.discharge_limited_by))
        print(f"{when}  可充 {cap.available_charge_kw:6.0f}（{cap.charge_limited_by}）"
              f"  可放 {cap.available_discharge_kw:6.0f}（{cap.discharge_limited_by}）")
    assert got == [(1500, "BMS", 2050, "防倒送"), (1350, "需量", 2450, "BMS"), (1000, "SOC窗口", 850, "防倒送")]
    print("自检通过")

if __name__ == "__main__":
    main()

