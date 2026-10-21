"""第 10 章：点表、寄存器解码与数据质量。

职责边界：本模块属于“接入层 + 校验层”，把设备寄存器变成带质量位和时间戳的工程值。
控制算法只应看到 Measurement，而不应看到寄存器地址、字序、缩放系数。

约定：
- 一个 Modbus 寄存器 16 bit，寄存器内部按协议规定为大端（高字节在前）；
- 32 位数据的四个字节记作 A B C D（A 为最高字节），layout 描述它们在两个寄存器里的排列：
  ABCD：高字在前（最常见）；CDAB：低字在前（字交换）；
  BADC：字内字节交换；DCBA：完全小端；
- 工程值 = (原始整数 × scale + offset) × sign，sign 用来在接入层统一功率方向（附录 B）。
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, replace
from enum import Enum
from typing import Sequence

# 数据类型 → (寄存器个数, 是否有符号, 是否浮点)
DATA_TYPES: dict[str, tuple[int, bool, bool]] = {
    "uint16": (1, False, False),
    "int16": (1, True, False),
    "uint32": (2, False, False),
    "int32": (2, True, False),
    "float32": (2, False, True),
}
LAYOUTS_16 = ("AB", "BA")
LAYOUTS_32 = ("ABCD", "CDAB", "BADC", "DCBA")


# ---------------------------------------------------------------- 寄存器 ⇄ 原始值
def _swap16(reg: int) -> int:
    return ((reg & 0xFF) << 8) | (reg >> 8)


def registers_from_bytes(data: bytes) -> list[int]:
    """把 Modbus 响应里的数据字节（每寄存器 2 字节、大端）切成寄存器列表。"""
    if len(data) % 2:
        raise ValueError("字节数必须是偶数（每个寄存器 2 字节）")
    return [int.from_bytes(data[i : i + 2], "big") for i in range(0, len(data), 2)]


def registers_to_raw(regs: Sequence[int], data_type: str, layout: str | None = None) -> int | float:
    """按数据类型和字节排列，把 1～2 个寄存器还原成原始整数（或 float32）。"""
    if data_type not in DATA_TYPES:
        raise ValueError(f"不支持的数据类型：{data_type}")
    n_regs, signed, is_float = DATA_TYPES[data_type]
    if len(regs) != n_regs:
        raise ValueError(f"{data_type} 需要 {n_regs} 个寄存器，实际 {len(regs)} 个")
    if any(not 0 <= r <= 0xFFFF for r in regs):
        raise ValueError("寄存器值必须在 0～0xFFFF 之间")

    if n_regs == 1:
        layout = layout or "AB"
        if layout not in LAYOUTS_16:
            raise ValueError(f"16 位数据的 layout 只能是 {LAYOUTS_16}")
        u = _swap16(regs[0]) if layout == "BA" else regs[0]
        bits = 16
    else:
        layout = layout or "ABCD"
        if layout not in LAYOUTS_32:
            raise ValueError(f"32 位数据的 layout 只能是 {LAYOUTS_32}")
        r0, r1 = regs
        if layout in ("BADC", "DCBA"):  # 寄存器内部字节被交换过
            r0, r1 = _swap16(r0), _swap16(r1)
        hi, lo = (r1, r0) if layout in ("CDAB", "DCBA") else (r0, r1)  # 低字在前时交换
        u = (hi << 16) | lo
        bits = 32

    if is_float:
        return struct.unpack(">f", u.to_bytes(4, "big"))[0]
    if signed and u >= 1 << (bits - 1):  # 二进制补码：最高位为 1 表示负数
        u -= 1 << bits
    return u


def raw_to_registers(raw: int | float, data_type: str, layout: str | None = None) -> list[int]:
    """registers_to_raw 的逆运算，用于遥调（写设定值）。超出类型范围直接报错，不截断。"""
    if data_type not in DATA_TYPES:
        raise ValueError(f"不支持的数据类型：{data_type}")
    n_regs, signed, is_float = DATA_TYPES[data_type]
    bits = 16 * n_regs
    if is_float:
        u = int.from_bytes(struct.pack(">f", float(raw)), "big")
    else:
        lo_lim, hi_lim = (-(1 << (bits - 1)), (1 << (bits - 1)) - 1) if signed else (0, (1 << bits) - 1)
        if not lo_lim <= raw <= hi_lim:
            raise ValueError(f"{raw} 超出 {data_type} 可表示范围 [{lo_lim}, {hi_lim}]")
        u = int(raw) & ((1 << bits) - 1)
    if n_regs == 1:
        layout = layout or "AB"
        if layout not in LAYOUTS_16:
            raise ValueError(f"16 位数据的 layout 只能是 {LAYOUTS_16}")
        return [_swap16(u) if layout == "BA" else u]
    layout = layout or "ABCD"
    if layout not in LAYOUTS_32:
        raise ValueError(f"32 位数据的 layout 只能是 {LAYOUTS_32}")
    hi, lo = u >> 16, u & 0xFFFF
    r0, r1 = (lo, hi) if layout in ("CDAB", "DCBA") else (hi, lo)
    if layout in ("BADC", "DCBA"):
        r0, r1 = _swap16(r0), _swap16(r1)
    return [r0, r1]


# ---------------------------------------------------------------- 原始值 ⇄ 工程值
def to_engineering(raw: int | float, scale: float = 1.0, offset: float = 0.0, sign: int = 1) -> float:
    """工程值 = (原始值 × scale + offset) × sign。"""
    if sign not in (1, -1):
        raise ValueError("sign 只能是 +1 或 −1")
    return (raw * scale + offset) * sign


def from_engineering(value: float, data_type: str, scale: float = 1.0, offset: float = 0.0, sign: int = 1) -> int | float:
    """工程值 → 原始值（遥调下发用）。整数类型四舍五入，并检查是否超出寄存器范围。"""
    if scale == 0:
        raise ValueError("scale 不能为 0")
    raw = (value * sign - offset) / scale
    if DATA_TYPES[data_type][2]:
        return raw
    raw_int = round(raw)
    raw_to_registers(raw_int, data_type)  # 只做范围校验
    return raw_int


# ---------------------------------------------------------------- 质量位与测量值
class Quality(str, Enum):
    GOOD = "GOOD"  # 可用于控制
    STALE = "STALE"  # 过期：采样时间距今太久
    FROZEN = "FROZEN"  # 冻结：本应变化的量长时间不变
    OUT_OF_RANGE = "OUT_OF_RANGE"  # 越界：超出物理合理范围
    COMM_FAILED = "COMM_FAILED"  # 通信失败：本次没读到
    SUBSTITUTED = "SUBSTITUTED"  # 替代值：人工置数或按规则估算，不是真实测量
    INVALID = "INVALID"  # 无效：时间戳倒退/在未来、NaN 等


@dataclass(frozen=True)
class Measurement:
    """带质量位和两个时间戳的测量值。value 为 None 表示没有可用数值。"""

    name: str
    value: float | None
    unit: str
    quality: Quality
    sample_time: float | None  # 设备采样时间（设备不提供时由网关用轮询时间代替，并在点表中注明）
    receive_time: float  # 网关收到数据的时间（EMS 时钟）
    raw: int | float | None = None
    note: str = ""

    def age_s(self, now: float) -> float:
        """数据年龄：按采样时间计算，而不是按接收时间。"""
        t = self.sample_time if self.sample_time is not None else self.receive_time
        return now - t


def is_usable(m: Measurement, allow_substituted: bool = False) -> bool:
    """控制可用性：默认只接受 GOOD；替代值必须由调用方显式允许。"""
    if m.value is None:
        return False
    return m.quality is Quality.GOOD or (allow_substituted and m.quality is Quality.SUBSTITUTED)


def substitute(m: Measurement, value: float, reason: str) -> Measurement:
    """人工置数或估算替代：保留原测点身份，质量位改为 SUBSTITUTED 并记下原因。"""
    return replace(m, value=value, quality=Quality.SUBSTITUTED, note=f"替代：{reason}")


def check_freshness(m: Measurement, now: float, max_age_s: float, future_tolerance_s: float = 1.0) -> Quality:
    """新鲜度判定：采样时间在未来（超过容差）→ INVALID；年龄超过 max_age_s → STALE；否则 GOOD。"""
    age = m.age_s(now)
    if age < -future_tolerance_s:
        return Quality.INVALID
    if age > max_age_s:
        return Quality.STALE
    return Quality.GOOD


def clock_skew_suspect(m: Measurement, max_transport_s: float) -> bool:
    """设备时钟可疑：接收时间与采样时间之差明显超过正常传输延迟，或采样时间晚于接收时间。

    这种情况下“过期”可能是假的（设备时钟慢了），应告警时钟问题，而不是只报数据过期。
    """
    if m.sample_time is None:
        return False
    delay = m.receive_time - m.sample_time
    return delay > max_transport_s or delay < 0


class FrozenDetector:
    """冻结检测：数值在 frozen_after_s 秒内变化不超过 tolerance，判为冻结。

    只适用于物理上一定会波动的量（频率、有功、电压）；开关状态、定值类测点不能用。
    """

    def __init__(self, frozen_after_s: float, tolerance: float = 0.0):
        if frozen_after_s <= 0 or tolerance < 0:
            raise ValueError("冻结判定时间必须为正，容差必须非负")
        self.frozen_after_s = frozen_after_s
        self.tolerance = tolerance
        self.ref_value: float | None = None
        self.ref_time: float | None = None

    def update(self, value: float, t: float) -> bool:
        if self.ref_value is None or abs(value - self.ref_value) > self.tolerance:
            self.ref_value, self.ref_time = value, t  # 数值动了：重新计时
            return False
        return t - self.ref_time >= self.frozen_after_s


# ---------------------------------------------------------------- 点表定义与单点监视
@dataclass(frozen=True)
class PointDef:
    """点表中的一行。地址、字序、缩放都属于接入层配置，算法层不应感知。"""

    name: str
    address: int  # 协议地址（0 基）。厂家文档写 40001 时，协议地址通常是 0，务必核对
    data_type: str
    unit: str
    scale: float = 1.0
    offset: float = 0.0
    layout: str | None = None
    sign: int = 1  # −1：在接入层把厂家方向换成课程方向，例如电表“进口为正”→ P_PCC“送电为正”
    valid_min: float | None = None  # 物理合理范围（不是控制限值）
    valid_max: float | None = None
    stale_after_s: float = 5.0
    frozen_after_s: float | None = None  # None 表示不做冻结检测
    frozen_tolerance: float = 0.0
    access: str = "R"  # R 只读（遥测）/ RW 可写（遥调）

    def decode(self, regs: Sequence[int]) -> tuple[int | float, float]:
        raw = registers_to_raw(regs, self.data_type, self.layout)
        return raw, to_engineering(raw, self.scale, self.offset, self.sign)

    def encode(self, value: float) -> list[int]:
        raw = from_engineering(value, self.data_type, self.scale, self.offset, self.sign)
        return raw_to_registers(raw, self.data_type, self.layout)


class PointMonitor:
    """单个测点的质量判定流水线（第 10 章 10.7 的流程图）。有状态：记住冻结计时和上次采样时间。

    判定顺序（先判断“数据能不能信”，再判断“数值合不合理”）：
    通信失败 → 时间戳无效 → 过期 → 解码/NaN → 越界 → 冻结 → GOOD
    """

    def __init__(self, point: PointDef, future_tolerance_s: float = 1.0):
        self.point = point
        self.future_tolerance_s = future_tolerance_s
        self.last_sample_time: float | None = None
        self.frozen = (
            FrozenDetector(point.frozen_after_s, point.frozen_tolerance) if point.frozen_after_s else None
        )

    def evaluate(
        self, regs: Sequence[int] | None, receive_time: float, now: float, sample_time: float | None = None
    ) -> Measurement:
        p = self.point
        ts = receive_time if sample_time is None else sample_time

        def make(value, quality, raw=None, note=""):
            return Measurement(p.name, value, p.unit, quality, ts, receive_time, raw, note)

        if regs is None:
            return make(None, Quality.COMM_FAILED, note="本次读取失败")
        if now - ts < -self.future_tolerance_s:
            return make(None, Quality.INVALID, note="采样时间在未来，检查时钟同步")
        if self.last_sample_time is not None and ts < self.last_sample_time:
            return make(None, Quality.INVALID, note="采样时间倒退")
        self.last_sample_time = ts

        raw, value = p.decode(regs)
        if now - ts > p.stale_after_s:
            return make(value, Quality.STALE, raw, f"数据年龄 {now - ts:.1f} s")
        if math.isnan(value) or math.isinf(value):
            return make(None, Quality.INVALID, raw, "非数")
        if (p.valid_min is not None and value < p.valid_min) or (p.valid_max is not None and value > p.valid_max):
            return make(value, Quality.OUT_OF_RANGE, raw, f"超出合理范围 [{p.valid_min}, {p.valid_max}]")
        if self.frozen is not None and self.frozen.update(value, ts):
            return make(value, Quality.FROZEN, raw, f"{p.frozen_after_s} s 内未变化")
        return make(value, Quality.GOOD, raw)

