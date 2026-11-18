"""第 21 章最小闭环：一天模型中的一个分钟周期追踪。

输入：参考 StationConfig 和默认日负荷/光伏/电价
算法：run_day 内的计划、约束投影、SOC、PCC、审计
输出：一个审计周期的请求、约束步骤、最终功率和反馈
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.mini_ems import run_day  # noqa: E402


def main():
    result = run_day()
    audit = result.audits[0]
    print(f"周期={audit.cycle_id}，请求={audit.requested_kw:.1f} kW，最终={audit.final_kw:.1f} kW")
    print(f"SOC={audit.soc:.4f}，质量={audit.data_quality}，审计步骤数={len(audit.steps)}")
    print(f"站点 KPI：最大需量={result.max_demand_kw():.1f} kW，最大倒送={result.max_backfeed_kw():.1f} kW")
    assert len(result.audits) > 0
    assert audit.config_version == result.cfg.config_version
    assert result.max_backfeed_kw() <= 1e-6
    assert result.max_demand_kw() <= result.cfg.demand_goal_kw - result.cfg.demand_margin_kw + 1e-6
    print("自检通过")


if __name__ == "__main__":
    main()

