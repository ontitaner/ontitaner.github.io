"""第 16 章最小闭环：AGC 设点→延迟/Ramp/响应→性能指标。

输入：8000 kW AGC 阶跃、10 MW 机组模型
算法：simulate_tracking、evaluate_step、performance_index
输出：响应时间、调节速率、精度和综合指标
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.agc import StationModel, evaluate_step, performance_index, simulate_tracking  # noqa: E402


def main():
    model = StationModel(p_rated_kw=10_000, ramp_kw_per_s=1000, delay_s=2.0, tau_s=0.0, soc0=0.5)
    trace = simulate_tracking([(0.0, 0.0), (2.0, 8000.0)], model, t_end_s=15.0, dt=1.0)
    metrics = evaluate_step(trace.t, trace.p_act, 2.0, 15.0, 0.0, 8000.0, 200.0)
    index = performance_index(metrics, rate_std_kw_per_s=500, t_std_s=10, err_allow_kw=200)
    print(f"响应时间：{metrics.response_time_s} s")
    print(f"调节速率：{metrics.rate_kw_per_s} kW/s")
    print(f"调节精度：{metrics.accuracy_kw} kW")
    print(f"指标：k1={index['k1']:.2f}，k2={index['k2']:.2f}，k3={index['k3']:.2f}，kp={index['kp']:.2f}")
    assert metrics.response_time_s is not None and metrics.rate_kw_per_s is not None
    assert metrics.accuracy_kw is not None and index['kp'] >= 0
    print("自检通过")


if __name__ == "__main__":
    main()

