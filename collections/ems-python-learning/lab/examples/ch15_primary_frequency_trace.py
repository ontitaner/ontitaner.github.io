"""第 15 章最小闭环：频率序列→死区/下垂→功率序列。

输入：频率逐拍变化、100 MW 额定功率、2% 调差率
算法：primary_frequency_power
输出：每拍调频功率和累计放电电量
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.frequency import PrimaryFrequencyConfig, primary_frequency_power  # noqa: E402


def main():
    cfg = PrimaryFrequencyConfig(p_rated_kw=100_000, droop_ratio=0.02, deadband_hz=0.03, limit_ratio=0.10)
    freqs = [50.00, 49.95, 49.90, 49.85, 50.05]
    powers = [primary_frequency_power(f, cfg) for f in freqs]
    for f, p in zip(freqs, powers):
        print(f"频率 {f:.2f} Hz → 调频功率 {p:+.1f} kW")
    energy_kwh = sum(max(0.0, p) for p in powers) * 0.2 / 3600
    print(f"0.2 s 采样下放电电量：{energy_kwh:.3f} kWh")
    assert all(abs(a - b) < 1e-9 for a, b in zip(powers, [0.0, 2000.0, 7000.0, 10000.0, -2000.0]))
    assert abs(energy_kwh - (2000 + 7000 + 10000) * 0.2 / 3600) < 1e-9
    print("自检通过")


if __name__ == "__main__":
    main()

