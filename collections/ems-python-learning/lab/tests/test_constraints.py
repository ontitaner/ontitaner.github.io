import math

import pytest

from ems_lab.constraints import (
    BoundCorrector,
    Interval,
    Layer,
    LowSocRecharge,
    SocZoneConfig,
    device_interval,
    export_limit_interval,
    import_limit_interval,
    intersect,
    no_grid_charge_interval,
    permission_interval,
    project,
    soc_interval,
)
from ems_lab.power import pcc_injection_kw


# ---------------- 区间与交集
def test_intersection_of_intervals():
    a = Interval(-500, 800, "BMS", Layer.DEVICE)
    b = Interval(-1000, 1000, "PCS", Layer.DEVICE)
    c = Interval(-math.inf, 240, "防倒送", Layer.SITE)
    assert intersect([a, b, c]) == (-500, 240)
    assert intersect([]) == (-math.inf, math.inf)
    assert Interval(1, 0, "x", Layer.SITE).is_empty
    with pytest.raises(ValueError):
        Interval(math.nan, 0, "x", Layer.SITE)


def test_layer_relaxable():
    assert not Layer.HARD_SAFETY.relaxable
    assert not Layer.DEVICE.relaxable
    assert Layer.SITE.relaxable and Layer.STRATEGY.relaxable


# ---------------- 防倒送：第 12 章手算
def test_export_limit_hand_calc():
    # 负荷 600、辅助 30、损耗 10、光伏 400、零倒送 → 放电上限 240
    c = export_limit_interval(p_load_kw=600, p_pv_kw=400, p_export_limit_kw=0, p_aux_kw=30, p_loss_kw=10)
    assert c.upper_kw == pytest.approx(240)
    assert c.lower_kw == -math.inf
    # 回代功率平衡：放电 240 时并网点正好为 0
    assert pcc_injection_kw(240, 600, 30, 10, p_pv_kw=400) == pytest.approx(0)
    # 允许倒送 100 kW 时上限随之放宽
    assert export_limit_interval(600, 400, 100, 30, 10).upper_kw == pytest.approx(340)
    with pytest.raises(ValueError):
        export_limit_interval(600, 400, -1)


def test_export_limit_can_force_charging():
    # 中午光伏 1500 > 负荷：上限为负，储能必须至少充 860 kW 才不倒送
    c = export_limit_interval(600, 1500, 0, 30, 10)
    assert c.upper_kw == pytest.approx(-860)


# ---------------- 进口上限：第 12 章手算，与第 00 章 ② 呼应
def test_import_limit_hand_calc():
    # 负荷 1500、辅助 30、损耗 10、无光伏、进口上限 1800 → 充电最多 260
    c = import_limit_interval(p_load_kw=1500, p_pv_kw=0, p_import_limit_kw=1800, p_aux_kw=30, p_loss_kw=10)
    assert c.lower_kw == pytest.approx(-260)
    r = project(-600, [c])
    assert r.final_kw == pytest.approx(-260)
    assert r.binding == "进口上限"
    # 回代：进口功率 = −P_PCC = 1800
    assert -pcc_injection_kw(-260, 1500, 30, 10) == pytest.approx(1800)


def test_import_limit_can_force_discharge():
    # 负荷 2100 已超过进口上限 1800：储能必须至少放 300
    assert import_limit_interval(2100, 0, 1800).lower_kw == pytest.approx(300)


def test_no_grid_charge_differs_from_zero_import_limit():
    # 没有光伏富余：防非计划充电只禁止充电（下限 0），不会强迫放电
    assert no_grid_charge_interval(600, 400).lower_kw == 0.0
    assert import_limit_interval(600, 400, 0).lower_kw == pytest.approx(200)  # 这会强迫放电
    # 有光伏富余 300：允许充电吸收富余
    assert no_grid_charge_interval(600, 900).lower_kw == pytest.approx(-300)


# ---------------- 硬安全许可与设备能力
def test_permission_interval_only_obey():
    r = project(500, [permission_interval(allow_charge=True, allow_discharge=False),
                      device_interval(500, 800)])
    assert r.final_kw == 0.0
    assert r.binding == "安全许可"
    assert project(-300, [permission_interval(False, False)]).final_kw == 0.0
    with pytest.raises(ValueError):
        device_interval(-1, 100)


# ---------------- SOC 分区
@pytest.mark.parametrize(
    "soc, lower, upper",
    [
        (0.05, -1000, 0),  # 低于运行下限：禁止放电
        (0.10, -1000, 0),  # 边界：运行下限处放电比例为 0
        (0.125, -1000, 500),  # 10%～15% 线性降额：一半
        (0.50, -1000, 1000),  # 正常
        (0.875, -500, 1000),  # 85%～90% 充电线性降额
        (0.90, 0, 1000),  # 运行上限：禁止充电
    ],
)
def test_soc_zones(soc, lower, upper):
    c = soc_interval(soc, p_rated_kw=1000)
    assert (c.lower_kw, c.upper_kw) == (pytest.approx(lower), pytest.approx(upper))
    assert c.layer == Layer.DEVICE


def test_soc_zone_validation():
    with pytest.raises(ValueError):
        soc_interval(50, 1000)  # 用了百分数
    with pytest.raises(ValueError):
        SocZoneConfig(stop_discharge_at=0.3, full_discharge_from=0.2)


def test_low_soc_recharge_hysteresis():
    rc = LowSocRecharge(start_below=0.08, stop_above=0.15, p_charge_kw=200)
    seq = [0.10, 0.079, 0.10, 0.14, 0.151, 0.12]
    out = [rc.update(s) for s in seq]
    assert out == [None, -200, -200, -200, None, None]


def test_low_soc_recharge_is_still_cut_by_import_limit():
    # 自充请求 −200，但负荷 1700、进口上限 1800：最多充 100
    rc = LowSocRecharge(p_charge_kw=200)
    req = rc.update(0.05)
    r = project(req, [device_interval(500, 0), import_limit_interval(1700, 0, 1800)])
    assert r.final_kw == pytest.approx(-100)
    assert r.binding == "进口上限"


# ---------------- 投影、原因与冲突
def test_project_with_reason_hand_calc():
    cs = [
        device_interval(available_charge_kw=500, available_discharge_kw=800),
        soc_interval(0.5, 1000),
        export_limit_interval(600, 400, 0, 30, 10),
        import_limit_interval(600, 400, 1800, 30, 10),
    ]
    r = project(800, cs)
    assert (r.lower_kw, r.upper_kw) == (pytest.approx(-500), pytest.approx(240))
    assert r.final_kw == pytest.approx(240)
    assert r.binding == "防倒送"
    assert r.limited and not r.conflicts
    assert any("防倒送" in s for s in r.reasons())
    # 请求在可行域内：原样通过，没有 binding
    r2 = project(100, cs)
    assert r2.final_kw == 100 and r2.binding is None and not r2.limited


def test_empty_domain_relax_lower_priority_and_report():
    # 光伏 1500 富余，要求至少充 860；但 BMS 只允许充 500 → 冲突
    cs = [device_interval(500, 800), export_limit_interval(600, 1500, 0, 30, 10)]
    r = project(0, cs)
    assert r.final_kw == pytest.approx(-500)  # 设备能力优先：尽力充满 500
    assert len(r.conflicts) == 1
    c = r.conflicts[0]
    assert c.name == "防倒送" and c.shortfall_kw == pytest.approx(360)  # 需光伏限发 360
    assert any("缺口 360" in s for s in r.reasons())
    assert not r.safe_stop


def test_import_limit_conflicts_with_low_soc_device():
    # 负荷 2100 超过进口上限 1800（要求至少放 300），但 SOC 低，BMS 只允许放 200
    cs = [device_interval(500, 200), import_limit_interval(2100, 0, 1800)]
    r = project(0, cs)
    assert r.final_kw == pytest.approx(200)
    assert r.conflicts[0].name == "进口上限" and r.conflicts[0].shortfall_kw == pytest.approx(100)


def test_strategy_window_relaxed_before_site_constraint():
    # 策略窗口要求至少放 500，防倒送只允许放 240：放松策略（优先级低），站点约束保住
    cs = [
        device_interval(500, 800),
        export_limit_interval(600, 400, 0, 30, 10),
        Interval(500, math.inf, "计划最小放电", Layer.STRATEGY),
    ]
    r = project(800, cs)
    assert r.final_kw == pytest.approx(240)
    assert r.conflicts[0].name == "计划最小放电"
    assert r.conflicts[0].shortfall_kw == pytest.approx(260)


def test_export_and_import_limits_never_conflict_with_each_other():
    # 同一组测量推出的两个区间：上限 − 下限 = 出口上限 + 进口上限 ≥ 0
    for load, pv in [(0, 0), (600, 1500), (2100, 0), (300, 300)]:
        e = export_limit_interval(load, pv, 0)
        i = import_limit_interval(load, pv, 1800)
        lo, hi = intersect([e, i])
        assert hi - lo == pytest.approx(1800)


def test_non_relaxable_conflict_safe_stop():
    cs = [Interval(100, 200, "异常许可", Layer.HARD_SAFETY), device_interval(500, 50)]
    r = project(150, cs)
    assert r.safe_stop and r.final_kw == 0.0
    assert r.reasons()[0].startswith("不可放松")


def test_project_rejects_nan():
    with pytest.raises(ValueError):
        project(math.nan, [device_interval(1, 1)])


# ---------------- 闭环修正
def test_bound_corrector_tightens_on_violation_and_freezes_when_inactive():
    bc = BoundCorrector(kp=0.0, ki=1.0, max_correction_kw=200)
    # 约束不起作用、还有余量：不积分
    for _ in range(10):
        corr = bc.update(margin_kw=100, dt=1.0, active=False)
    assert corr == 0.0
    # 越限 30 kW：即使判定为 inactive 也要收紧
    corr = bc.update(margin_kw=-30, dt=1.0, active=False)
    assert corr == pytest.approx(-30)
    # 修正量有上限（抗饱和）
    for _ in range(20):
        corr = bc.update(margin_kw=-100, dt=1.0, active=True)
    assert corr == pytest.approx(-200)

# ---------------- 第 12 章自测答案
def test_chapter12_self_check_answers():
    assert export_limit_interval(800, 300, 0, 20, 10).upper_kw == pytest.approx(530)
    assert export_limit_interval(800, 300, 50, 20, 10).upper_kw == pytest.approx(580)
    assert export_limit_interval(400, 1200, 0).upper_kw == pytest.approx(-800)
    assert import_limit_interval(1600, 0, 1800).lower_kw == pytest.approx(-200)
    assert import_limit_interval(1950, 0, 1800).lower_kw == pytest.approx(150)
    assert no_grid_charge_interval(600, 400).lower_kw == 0.0
    assert import_limit_interval(600, 400, 0).lower_kw == pytest.approx(200)
    # 第 6 题：BMS 可充 300，防倒送要求至少充 450
    r = project(0, [device_interval(300, 500), Interval(-math.inf, -450, "防倒送", Layer.SITE)])
def test_ch12_constraints_trace_example():
    """12 章最小闭环：区间交集、请求投影和绑定原因。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch12_constraints_trace.py"
    runpy.run_path(str(script), run_name="__main__")

