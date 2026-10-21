"""第 18 章最小闭环：请求→仲裁→约束→分配→校验。

输入：AGC +500、一次调频 -50、经济充电 -200；全站能力和防倒送约束
算法：优先级覆盖/叠加→统一投影→按 PCS 能力分配
输出：全站最终功率、未满足量、各 PCS 设定值
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.allocation import Unit, allocate_by_capability, check_allocation  # noqa: E402
from ems_lab.arbitration import Priority, Request, arbitrate, device_limit, export_limit  # noqa: E402

P = Priority


def main():
    requests = [Request("AGC", P.P3_DISPATCH, 500),
                Request("一次调频", P.P3_DISPATCH, -50, "delta"),
                Request("经济", P.P5_ECONOMIC, -200)]
    limits = [device_limit(500, 600), export_limit(300, 0, 0, hard=True)]
    arb = arbitrate(requests, limits)
    units = [Unit("PCS1", 250, 250), Unit("PCS2", 250, 250), Unit("PCS3", 100, 100)]
    alloc = allocate_by_capability(arb.final_kw, units)
    issues = check_allocation(alloc, units)
    print(f"合成请求：{arb.composed_kw:.0f} kW；约束后：{arb.final_kw:.0f} kW")
    print(f"未满足：{arb.unserved_kw:.0f} kW；限制：{arb.limiting}")
    print(f"分配：{alloc.setpoints}；校验：{issues or '通过'}")
    assert arb.composed_kw == 450 and arb.final_kw == 300 and arb.unserved_kw == 150
    assert alloc.setpoints == {"PCS1": 125.0, "PCS2": 125.0, "PCS3": 50.0}
    assert issues == []
    print("自检通过")


if __name__ == "__main__":
    main()

