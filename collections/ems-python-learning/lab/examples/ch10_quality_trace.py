"""第 10 章最小闭环：原始寄存器→工程值→质量判定→控制许可。

输入：冻结的频率寄存器、点表缩放/合理范围/冻结参数
算法：解码→工程值→新鲜度/冻结判定→决定是否可用于控制
输出：GOOD/FROZEN 质量和控制许可
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.datapoint import PointDef, PointMonitor, Quality  # noqa: E402


def main():
    point = PointDef("pcc.f", 0x100, "int16", "Hz", scale=0.01,
                     valid_min=45, valid_max=55, stale_after_s=2,
                     frozen_after_s=5, frozen_tolerance=0.001)
    monitor = PointMonitor(point)
    regs = [4992]  # 4992 × 0.01 = 49.92 Hz
    qualities = []
    for now in range(0, 7):
        m = monitor.evaluate(regs, receive_time=now, now=now, sample_time=now)
        qualities.append(m.quality)
        print(f"t={now}s value={m.value:.2f} Hz quality={m.quality.name}")
    assert qualities[:5] == [Quality.GOOD] * 5
    assert qualities[5] is Quality.FROZEN
    assert not (qualities[5] is Quality.GOOD)
    print("控制许可：冻结后拒绝进入一次调频")
    print("自检通过")


if __name__ == "__main__":
    main()

