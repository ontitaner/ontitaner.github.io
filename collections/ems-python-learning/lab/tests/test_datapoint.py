"""第 10 章手算对应的测试：寄存器解码、缩放、方向、质量位、新鲜度、冻结。"""
import math

import pytest

from ems_lab.datapoint import (
    FrozenDetector,
    Measurement,
    PointDef,
    PointMonitor,
    Quality,
    check_freshness,
    clock_skew_suspect,
    from_engineering,
    is_usable,
    raw_to_registers,
    registers_from_bytes,
    registers_to_raw,
    substitute,
    to_engineering,
)


# ---------------- 10.5 手算：16 位
def test_int16_negative_power_hand_calc():
    # PCS 有功 0xFF38，int16，×0.1 kW：-200 × 0.1 = -20.0 kW（充电 20 kW）
    raw = registers_to_raw([0xFF38], "int16")
    assert raw == -200
    assert to_engineering(raw, 0.1) == pytest.approx(-20.0)


def test_int16_read_as_uint16_is_wrong():
    # 同一个寄存器按 uint16 读：65336 × 0.1 = 6533.6 kW，一个 1 MW 的 PCS 不可能输出这么多
    assert to_engineering(registers_to_raw([0xFF38], "uint16"), 0.1) == pytest.approx(6533.6)


def test_uint16_soc_hand_calc():
    # SOC 0x0307 = 775，×0.1 % = 77.5 %
    assert to_engineering(registers_to_raw([0x0307], "uint16"), 0.1) == pytest.approx(77.5)


def test_offset_temperature_hand_calc():
    # 温度 raw 650，×0.1 − 40 = 25.0 ℃
    assert to_engineering(650, 0.1, -40) == pytest.approx(25.0)


def test_bytes_to_registers():
    assert registers_from_bytes(b"\xff\x38\x03\x07") == [0xFF38, 0x0307]
    with pytest.raises(ValueError):
        registers_from_bytes(b"\x01")


def test_byte_swapped_int16():
    # 字节被交换的设备：0x38FF 按 BA 解读才是 0xFF38
    assert registers_to_raw([0x38FF], "int16", "BA") == -200


# ---------------- 10.5 手算：32 位与字序
def test_int32_abcd_hand_calc():
    # [0xFFFE, 0x7960] → 0xFFFE7960 → -100000 → ×0.01 = -1000.00 kW
    raw = registers_to_raw([0xFFFE, 0x7960], "int32", "ABCD")
    assert raw == -100000
    assert to_engineering(raw, 0.01) == pytest.approx(-1000.0)


def test_int32_word_order_mistake():
    # 设备低字在前，送来 [0x7960, 0xFFFE]
    assert registers_to_raw([0x7960, 0xFFFE], "int32", "CDAB") == -100000
    # 误按 ABCD 解读：0x7960FFFE = 2036400126 → ×0.01 ≈ 2036 万 kW，一眼越界
    wrong = registers_to_raw([0x7960, 0xFFFE], "int32", "ABCD")
    assert wrong == 2036400126
    assert to_engineering(wrong, 0.01) == pytest.approx(20364001.26)


def test_word_order_invisible_at_small_values():
    # 待机时功率为 0：字序错了也解出 0，调试时看不出来
    assert registers_to_raw([0, 0], "int32", "ABCD") == registers_to_raw([0, 0], "int32", "CDAB") == 0
    # 小正数 +500.00 kW（raw 50000 = 0x0000C350）：字序错了变成 0xC3500000，按 int32 是巨大负数
    regs = raw_to_registers(50000, "int32", "ABCD")
    assert regs == [0x0000, 0xC350]
    assert registers_to_raw(regs, "int32", "CDAB") == 0xC3500000 - (1 << 32)


def test_uint32_energy_hand_calc():
    # 累计放电量 [0x0012, 0xD687] = 1234567 → ×0.1 kWh = 123456.7 kWh
    raw = registers_to_raw([0x0012, 0xD687], "uint32")
    assert raw == 1234567
    assert to_engineering(raw, 0.1) == pytest.approx(123456.7)


def test_float32_frequency():
    # 0x42480000 是 IEEE 754 单精度的 50.0
    assert registers_to_raw([0x4248, 0x0000], "float32") == 50.0
    assert registers_to_raw([0x0000, 0x4248], "float32", "CDAB") == 50.0


@pytest.mark.parametrize("layout", ["ABCD", "CDAB", "BADC", "DCBA"])
@pytest.mark.parametrize("raw", [-100000, -1, 0, 1, 50000, 2**31 - 1, -(2**31)])
def test_int32_roundtrip_all_layouts(layout, raw):
    assert registers_to_raw(raw_to_registers(raw, "int32", layout), "int32", layout) == raw


def test_dcba_is_fully_reversed_bytes():
    # 0x12345678 按 DCBA 在线上是 78 56 34 12
    regs = raw_to_registers(0x12345678, "uint32", "DCBA")
    assert registers_from_bytes(bytes.fromhex("78563412")) == regs


def test_register_length_and_range_checks():
    with pytest.raises(ValueError):
        registers_to_raw([1], "int32")
    with pytest.raises(ValueError):
        registers_to_raw([0x10000], "uint16")
    with pytest.raises(ValueError):
        registers_to_raw([1, 2], "int32", "AB")


# ---------------- 遥调：工程值 → 寄存器
def test_setpoint_encode_hand_calc():
    # 下发 −20.0 kW，int16，×0.1：raw = −200 → 0xFF38
    assert from_engineering(-20.0, "int16", 0.1) == -200
    p = PointDef("pcs.p_set", 0x3000, "int16", "kW", scale=0.1, access="RW")
    assert p.encode(-20.0) == [0xFF38]


def test_setpoint_out_of_register_range_raises():
    # int16 ×0.1 最多表示 ±3276.7 kW；下发 5000 kW 必须报错，而不是溢出变成负数
    with pytest.raises(ValueError, match="超出"):
        from_engineering(5000.0, "int16", 0.1)


# ---------------- 方向换算在接入层完成
def test_meter_import_positive_converted_to_pcc_export_positive():
    # 电表“进口为正”，读到 +1500 kW（从电网取电 1500 kW）；sign=-1 后 p_pcc_kw = -1500
    meter = PointDef("meter.p_pcc_kw", 0x0100, "int32", "kW", scale=0.01, sign=-1)
    regs = raw_to_registers(150000, "int32")
    _, value = meter.decode(regs)
    assert value == pytest.approx(-1500.0)


# ---------------- 质量位：新鲜度、时钟、冻结
def _m(sample_time, receive_time, value=1.0, quality=Quality.GOOD):
    return Measurement("x", value, "kW", quality, sample_time, receive_time)


def test_freshness_hand_calc():
    # 采样 100.0 s，现在 102.5 s，允许 2 s → 过期
    assert check_freshness(_m(100.0, 100.1), now=102.5, max_age_s=2.0) is Quality.STALE
    assert check_freshness(_m(101.0, 101.1), now=102.5, max_age_s=2.0) is Quality.GOOD
    # 采样时间比现在还晚 5 s：时钟有问题
    assert check_freshness(_m(107.5, 102.4), now=102.5, max_age_s=2.0) is Quality.INVALID


def test_clock_skew_makes_fresh_data_look_stale():
    # 设备时钟慢 300 s：数据 0.2 s 前刚收到，但按采样时间算“年龄” 300.2 s
    m = _m(sample_time=1000.0 - 300.0, receive_time=1000.0 - 0.2)
    assert check_freshness(m, now=1000.0, max_age_s=2.0) is Quality.STALE
    assert clock_skew_suspect(m, max_transport_s=1.0)  # 真正的问题是时钟，不是数据
    assert not clock_skew_suspect(_m(999.5, 999.8), max_transport_s=1.0)


def test_frozen_detector():
    d = FrozenDetector(frozen_after_s=5.0, tolerance=1e-6)
    # 频率冻结在 49.92 Hz
    flags = [d.update(49.92, t) for t in range(0, 11)]
    assert flags[:5] == [False] * 5
    assert flags[5] and flags[10]  # 第 5 s 起判冻结
    assert d.update(49.93, 11) is False  # 数值动了，重新计时


def test_substituted_not_usable_by_default():
    m = substitute(_m(1.0, 1.0), 0.0, "人工置数")
    assert m.quality is Quality.SUBSTITUTED and "人工置数" in m.note
    assert not is_usable(m)
    assert is_usable(m, allow_substituted=True)
    assert not is_usable(_m(1.0, 1.0, value=None))


# ---------------- 单点质量判定流程
FREQ = PointDef("meter.f_hz", 0x0200, "uint16", "Hz", scale=0.01, valid_min=45.0, valid_max=55.0,
                stale_after_s=2.0, frozen_after_s=5.0, frozen_tolerance=1e-9)


def test_monitor_good_and_out_of_range():
    mon = PointMonitor(FREQ)
    m = mon.evaluate([4992], receive_time=0.0, now=0.1)
    assert m.quality is Quality.GOOD and m.value == pytest.approx(49.92)
    # 缩放系数配错成 0.1：499.2 Hz，越界
    wrong = PointMonitor(PointDef("f", 0, "uint16", "Hz", scale=0.1, valid_min=45, valid_max=55))
    assert wrong.evaluate([4992], 0.0, 0.1).quality is Quality.OUT_OF_RANGE


def test_monitor_comm_failed_stale_invalid():
    mon = PointMonitor(FREQ)
    assert mon.evaluate(None, 0.0, 0.1).quality is Quality.COMM_FAILED
    m = mon.evaluate([5000], receive_time=10.0, now=13.0)
    assert m.quality is Quality.STALE and m.value == pytest.approx(50.0)  # 保留数值供显示
    assert mon.evaluate([5000], receive_time=20.0, now=15.0).quality is Quality.INVALID  # 未来
    assert mon.evaluate([5000], receive_time=9.0, now=9.5).quality is Quality.INVALID  # 倒退


def test_monitor_frozen_after_5s():
    mon = PointMonitor(FREQ)
    q = [mon.evaluate([4992], receive_time=float(t), now=t + 0.1).quality for t in range(8)]
    assert q[:5] == [Quality.GOOD] * 5
    assert q[5:] == [Quality.FROZEN] * 3


def test_monitor_nan_float_is_invalid():
    p = PointDef("f", 0, "float32", "Hz")
    assert PointMonitor(p).evaluate([0x7FC0, 0x0000], 0.0, 0.1).quality is Quality.INVALID
    assert math.isnan(registers_to_raw([0x7FC0, 0x0000], "float32"))

# ---------------- 10.14 自测题的手算
def test_self_check_answers():
    # 1. 0xFE0C int16 ×0.1 → −50.0 kW；误按 uint16 → 6503.6 kW
    assert to_engineering(registers_to_raw([0xFE0C], "int16"), 0.1) == pytest.approx(-50.0)
    assert to_engineering(registers_to_raw([0xFE0C], "uint16"), 0.1) == pytest.approx(6503.6)
    # 2. [0x0001, 0x86A0] 高字在前 ×0.01 → 1000.00 kWh；设备低字在前被误读 → 约 2258 万 kWh
    assert to_engineering(registers_to_raw([0x0001, 0x86A0], "uint32"), 0.01) == pytest.approx(1000.0)
    assert registers_to_raw([0x86A0, 0x0001], "uint32", "ABCD") == 2258632705
    # 3. 0x0258 ×0.1 −40 → 20.0 ℃
    assert to_engineering(registers_to_raw([0x0258], "uint16"), 0.1, -40) == pytest.approx(20.0)
    # 5. 采样 50.0、接收 349.8、现在 350.0：判过期，但真正原因是时钟
    m = _m(sample_time=50.0, receive_time=349.8)
    assert check_freshness(m, now=350.0, max_age_s=2.0) is Quality.STALE
    assert clock_skew_suspect(m, max_transport_s=1.0)


def test_twos_complement_addition_example():
    # 深入：−200 + 300 按无符号相加后只保留低 16 位 = 100
    assert (0xFF38 + 0x012C) & 0xFFFF == 100


def test_ch10_quality_trace_example():
    """10 章最小闭环：寄存器解码、冻结判定、控制许可。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch10_quality_trace.py"
    runpy.run_path(str(script), run_name="__main__")

