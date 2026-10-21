"""第 07 章手算例子的测试。效率、功率数值均为 [教学示例]。"""
import pytest

from ems_lab.site import (
    Stage,
    bess_command_for_pcc_target,
    chain_from_dc,
    chain_from_grid,
    check_direction,
    correct_ratio_kw,
    diagnose_balance,
    import_from_pcc,
    pcc_from_meter,
    round_trip_efficiency,
    site_pcc_kw,
    transformer_loss_kw,
)

# 7.5 工商业示例：PCS 放电 98%、充电 97.5%，变压器 99%
CI_CHAIN = [Stage("PCS", 0.98, 0.975), Stage("变压器", 0.99)]


# ---------------------------------------------------------------- 效率链
def test_discharge_chain_dc_1000():
    r = chain_from_dc(1000, CI_CHAIN)
    assert r.powers_kw == pytest.approx([1000, 980, 970.2])
    assert r.losses_kw == pytest.approx([20, 9.8])
    assert r.total_loss_kw == pytest.approx(29.8)


def test_charge_chain_grid_1000():
    # 从电网取 1000 kW 充电：过变压器剩 990，过 PCS 剩 965.25 进电池
    r = chain_from_grid(-1000, CI_CHAIN)
    assert r.powers_kw == pytest.approx([-965.25, -990, -1000])
    assert r.losses_kw == pytest.approx([24.75, 10])
    assert all(loss >= 0 for loss in r.losses_kw)


def test_charge_chain_dc_1000_needs_more_from_grid():
    # 想让电池直流侧充进 1000 kW，并网侧要取 1000 / 0.975 / 0.99 ≈ 1036.0 kW
    r = chain_from_dc(-1000, CI_CHAIN)
    assert r.powers_kw[-1] == pytest.approx(-1036.0, abs=0.05)


def test_chain_is_invertible():
    for p in (1000, -1000, 0, 350):
        fwd = chain_from_dc(p, CI_CHAIN)
        back = chain_from_grid(fwd.powers_kw[-1], CI_CHAIN)
        assert back.powers_kw == pytest.approx(fwd.powers_kw)


def test_round_trip_efficiency():
    # 0.98 × 0.975 × 0.99 × 0.99 ≈ 93.6%（不含电池本体损耗）
    assert round_trip_efficiency(CI_CHAIN) == pytest.approx(0.93649, abs=1e-5)


def test_stage_validation():
    with pytest.raises(ValueError):
        Stage("坏数据", 1.2)


def test_grid_side_station_chain():
    # 7.5 电网侧示例：PCS 交流侧合计 100 MW → 箱变 99% → 集电线 99.5% → 35 kV 母线，
    # 站用电 0.5 MW 从 35 kV 母线取 → 主变 99.5% → 110 kV 并网点
    feeder = [Stage("箱变", 0.99), Stage("集电线", 0.995)]
    main_tr = [Stage("主变", 0.995)]
    p_35kv = chain_from_dc(100_000, feeder).powers_kw[-1]
    assert p_35kv == pytest.approx(98_505)
    p_pcc = chain_from_dc(p_35kv - 500, main_tr).powers_kw[-1]
    assert p_pcc == pytest.approx(97_515, abs=1)
    # 反过来：要让并网点达到 100 MW，PCS 交流侧合计约 102.5 MW
    p_35kv_need = chain_from_grid(100_000, main_tr).powers_kw[0] + 500
    p_ac_need = chain_from_grid(p_35kv_need, feeder).powers_kw[0]
    assert p_ac_need == pytest.approx(102_535, abs=1)


def test_transformer_loss_not_constant():
    # 7.14 深入：2000 kVA，空载 2 kW，额定负载损耗 16 kW
    assert transformer_loss_kw(1000, 2000, 2, 16) == pytest.approx(6)  # 50% 负载 → 效率 99.4%
    assert transformer_loss_kw(200, 2000, 2, 16) == pytest.approx(2.16)  # 10% 负载 → 效率约 98.9%
    assert transformer_loss_kw(0, 2000, 2, 16) == pytest.approx(2)  # 空载仍有 2 kW


def test_quiz_chains():
    # 7.13 自测 1、2
    chain = [Stage("PCS", 0.97, 0.96), Stage("变压器", 0.985)]
    assert chain_from_dc(500, chain).powers_kw[-1] == pytest.approx(477.725)
    assert chain_from_grid(-500, chain).powers_kw[0] == pytest.approx(-472.8)


def test_quiz_balance_and_target():
    # 7.13 自测 3、4、5
    assert pcc_from_meter(250) == -250
    assert site_pcc_kw(500, -300, 600, 15, 5) == pytest.approx(-420)
    assert bess_command_for_pcc_target(0, 900, 600, 15, 5) == pytest.approx(-280)
    # 自测 7：实测比计算多出 15 kW = P_aux
    assert any("重复统计" in h for h in diagnose_balance(-420, 500, -300, 615, 15, 5))


# ---------------------------------------------------------------- 方向与变比
def test_meter_direction_conversion():
    assert pcc_from_meter(70) == -70  # 进口为正的电表读 +70：从电网取电 70
    assert pcc_from_meter(-20) == 20  # 读 −20：倒送 20
    assert pcc_from_meter(15, meter_import_positive=False) == 15
    assert import_from_pcc(-122) == 122


def test_ct_ratio_correction():
    # CT 实际 1500/5，配置成 1000/5：真实 600 kW 只报 400 kW
    assert correct_ratio_kw(400, ratio_configured=200, ratio_actual=300) == pytest.approx(600)
    with pytest.raises(ValueError):
        correct_ratio_kw(1, 0, 1)


# ---------------------------------------------------------------- 功率平衡手算表
@pytest.mark.parametrize(
    "pv, bess, expected",
    [
        (300, 400, -122),  # 基准工况：取电 122
        (700, 400, 278),  # 光伏升高：倒送 278
        (700, -200, -322),  # 储能改为充电 200
        (0, 0, -822),  # 夜间、储能停机
    ],
)
def test_site_balance_table(pv, bess, expected):
    assert site_pcc_kw(pv, bess, p_load_kw=800, p_aux_kw=20, p_loss_kw=2) == pytest.approx(expected)


def test_load_includes_aux_not_double_counted():
    # 负荷测点读数 820 已含辅助 20：声明 load_includes_aux 后结果与基准工况一致
    assert site_pcc_kw(300, 400, 820, 20, 2, load_includes_aux=True) == pytest.approx(-122)
    # 不声明就会重复扣一次，结果偏差 20 kW
    assert site_pcc_kw(300, 400, 820, 20, 2) == pytest.approx(-142)


def test_bess_command_for_zero_export():
    # 光伏 700：要让 P_PCC = 0，储能放电只能到 122
    assert bess_command_for_pcc_target(0, 700, 800, 20, 2) == pytest.approx(122)
    # 光伏 1000：需要充电 178；可充只有 100 时被限幅
    assert bess_command_for_pcc_target(0, 1000, 800, 20, 2) == pytest.approx(-178)
    assert bess_command_for_pcc_target(0, 1000, 800, 20, 2, 100, 500) == pytest.approx(-100)
    # 负荷测点已包含辅助 20 kW 时，目标反算不能再次加辅助
    assert bess_command_for_pcc_target(0, 700, 820, 20, 2, load_includes_aux=True) == pytest.approx(122)


# ---------------------------------------------------------------- 故障诊断
def test_diagnose_consistent():
    assert diagnose_balance(-122, 300, 400, 800, 20, 2) == []


def test_diagnose_aux_double_counted():
    hints = diagnose_balance(-122, 300, 400, 820, 20, 2)
    assert any("重复统计" in h for h in hints)


def test_diagnose_bess_direction_reversed():
    hints = diagnose_balance(-122, 300, -400, 800, 20, 2)
    assert any("储能功率方向" in h for h in hints)


def test_diagnose_meter_reversed():
    hints = diagnose_balance(122, 300, 400, 800, 20, 2)
    assert any("电表方向" in h for h in hints)


def test_diagnose_ct_ratio():
    hints = diagnose_balance(-122 * 200 / 300, 300, 400, 800, 20, 2)
    assert any("0.67 倍" in h for h in hints)


# ---------------------------------------------------------------- 方向核对试验
def test_direction_check():
    assert check_direction(100, 98) == "OK"  # 储能多放 100，P_PCC 增加约 98（含损耗）
    assert check_direction(100, -100).startswith("方向相反")
    assert check_direction(100, 50).startswith("幅值偏差")
    assert check_direction(100, 3).startswith("无响应")
    # 进口为正的电表：储能多放 100，读数应该减少 100
    assert check_direction(-100, -99) == "OK"
    with pytest.raises(ValueError):
        check_direction(0, 1)
def test_ch07_minimal_example():
    """07 章最小闭环：效率换算 → PCC 平衡 → 残差诊断。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch07_site_balance.py"
    runpy.run_path(str(script), run_name="__main__")

