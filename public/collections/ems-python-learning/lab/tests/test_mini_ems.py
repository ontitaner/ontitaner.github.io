"""第 21 章：综合项目验收测试。每条断言对应第 21 章 21.6 验收清单中的一项。"""
import pytest

from ems_lab.mini_ems import STEPS, StationConfig, baseline_no_storage, run_day


@pytest.fixture(scope="module")
def ems():
    return run_day()


@pytest.fixture(scope="module")
def plan_only():
    return run_day(use_constraints=False)


def test_a1_power_balance(ems):
    """A1 功率平衡：每个周期 P_PCC = P_PV(实际) + P_BESS − P_load − P_aux。"""
    assert len(ems.p_pcc) == STEPS
    assert ems.power_balance_residual_kw() <= 1e-6


def test_a2_no_backfeed_and_counterexample(ems, plan_only):
    """A2 零倒送：EMS 全天不倒送；对照组（只执行计划）会大量倒送。"""
    assert ems.max_backfeed_kw() <= 1e-6
    assert plan_only.max_backfeed_kw() > 1000


def test_a3_demand_within_goal(ems, plan_only):
    """A3 需量：15 分钟需量最大值不超过目标；对照组在谷时满功率充电，叠加夜间负荷后超需量。"""
    cfg = ems.cfg
    assert ems.max_demand_kw() <= cfg.demand_goal_kw - cfg.demand_margin_kw + 1e-6
    assert plan_only.max_demand_kw() > cfg.demand_goal_kw
    # 充电会推高需量：只执行计划的需量比“没有储能”还高
    assert plan_only.max_demand_kw() > baseline_no_storage().max_demand_kw


def test_a4_soc_within_operating_window(ems):
    """A4 SOC：始终在 EMS 运行窗口 [10%, 90%] 内。"""
    z = ems.cfg.soc_zones
    assert min(ems.soc) >= z.stop_discharge_at - 1e-9
    assert max(ems.soc) <= z.stop_charge_at + 1e-9


def test_a5_every_limited_decision_has_reason(ems):
    """A5 可追溯：凡是下发值 ≠ 请求值的周期，审计记录里都能找到起作用的约束。"""
    limited = [a for a in ems.audits if abs(a.final_kw - a.requested_kw) > 1e-9]
    assert limited, "这一天应当有约束动作"
    assert all(a.binding() for a in limited)
    counts = ems.binding_counts()
    assert counts["防倒送"] > 0 and counts["需量控制"] > 0 and counts["SOC 分区"] > 0


def test_a6_conflicts_reported_and_resolved_by_curtailment(ems):
    """A6 冲突上报：电池满了但光伏仍富余时，防倒送无法由储能满足 → 上报冲突，并由光伏限发兜底。"""
    assert ems.conflicts and {name for _, name, _ in ems.conflicts} == {"防倒送"}
    for k, _, shortfall in ems.conflicts:
        assert shortfall > 0
        assert ems.pv_used[k] < ems.pv[k]  # 这些周期都发生了光伏限发
    assert ems.pv_curtailed_kwh() > 0


def test_a7_plan_feasible_and_economics(ems):
    """A7 经济性：计划可执行，且购电电费低于“没有储能”的对照组。"""
    base = baseline_no_storage()
    assert ems.plan_expected_profit > 0
    assert ems.grid_energy_cost() < base.grid_energy_cost
    assert ems.pv_curtailed_kwh() < base.pv_curtailed_kwh  # 储能吸收了一部分原本要弃掉的光伏


def test_a8_deterministic():
    """A8 可重复：同样的配置和输入，结果逐点一致。"""
    a, b = run_day(), run_day()
    assert a.p_bess == b.p_bess and a.soc == b.soc


def test_a9_config_version_recorded(ems):
    """A9 配置版本写进每条审计记录。"""
    assert all(a.config_version == StationConfig().config_version for a in ems.audits)

def test_ch21_one_cycle_trace_example():
    """21 章最小闭环：参考实现单周期审计和全天验收。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch21_one_cycle_trace.py"
    runpy.run_path(str(script), run_name="__main__")

