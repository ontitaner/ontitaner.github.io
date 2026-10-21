"""第 17 章最小闭环：电压→Q-U 下垂→电压反馈。

输入：母线电压序列、Q-U 下垂参数和简化电压灵敏度
算法：qu_droop_kvar 计算无功；下一拍用 ΔU = sensitivity × Q 更新电压
输出：每拍电压、无功和电压误差
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.reactive import QuDroopConfig, qu_droop_kvar  # noqa: E402


def main():
    cfg = QuDroopConfig(u_ref_pu=1.0, deadband_pu=0.01, slope_kvar_per_pu=10000, q_max_kvar=500)
    voltage = 0.96
    sensitivity = 0.00004  # 每 kvar 对母线电压的教学示例影响
    rows = []
    for k in range(5):
        q = qu_droop_kvar(voltage, cfg)
        rows.append((voltage, q))
        print(f"拍{k}：U={voltage:.4f} pu，Q={q:+.1f} kvar")
        voltage += sensitivity * q
    assert abs(rows[0][0] - 0.96) < 1e-9 and abs(rows[0][1] - 300.0) < 1e-9
    assert rows[-1][0] > rows[0][0]
    assert rows[-1][1] < rows[0][1]
    print("自检通过")


if __name__ == "__main__":
    main()

