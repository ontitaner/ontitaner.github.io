"""第 06 章最小闭环：PCS 能力计算与 P-Q 投影。

输入：电压 621 V、温度 50 °C、请求 P=800 kW、Q=300 kvar
算法：计算可用视在容量 → 有功优先投影
输出：实际 P/Q、未满足无功和原因

运行：python examples/ch06_pcs_projection.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.pcs import PcsRating, apply_pcs_limits  # noqa: E402


def main():
    rating = PcsRating(
        s_rated_kva=1000,
        u_rated_v=690,
        p_discharge_max_kw=1000,
        p_charge_max_kw=750,
    )
    result = apply_pcs_limits(800, 300, rating, u_line_v=621, temp_c=50, priority="P")
    print(f"请求：P=800 kW，Q=300 kvar")
    print(f"输出：P={result.p_kw:.1f} kW，Q={result.q_kvar:.1f} kvar")
    print(f"未满足：P={result.p_unserved_kw:.1f} kW，Q={result.q_unserved_kvar:.1f} kvar")
    print(f"原因：{'；'.join(result.reasons)}")
    assert abs(result.p_kw - 800) < 1e-9
    assert abs(result.q_kvar - 126.9) < 0.1
    assert abs(result.q_unserved_kvar - 173.1) < 0.1
    print("自检通过")


if __name__ == "__main__":
    main()

