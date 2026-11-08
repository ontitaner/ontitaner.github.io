# @AI_GENERATED
"""AVC 典型故障诊断引擎

对应章节：09 典型误区与故障诊断

五类典型误区（对齐 09.2 决策树）：
  1. 死区>合格范围 → 合规链断裂
  2. NTP 时间偏移 → 合格率虚低
  3. SVG 本地抢控 → 总 Q 失控
  4. 积分饱和 → 反向调节滞后
  5. 参数禁止上传 → 通讯阻塞
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class FaultCategory(Enum):
    DEADBAND_COMPLIANCE = "deadband_compliance"
    NTP_OFFSET = "ntp_offset"
    SVG_LOCAL_OVERRIDE = "svg_local_override"
    INTEGRAL_WINDUP = "integral_windup"
    PARAM_UPLOAD_BLOCK = "param_upload_block"


@dataclass
class FaultDiagnosis:
    category: FaultCategory
    root_cause: str
    evidence: str
    fix: str
    check_time_minutes: int = 15


DIAGNOSTIC_TREE = [
    FaultDiagnosis(
        category=FaultCategory.DEADBAND_COMPLIANCE,
        root_cause="死区宽度（0.5kV）> 合格范围一半——在合格范围边缘控制器不动作",
        evidence="自统计 VQR 99%+ 但调度判 94%；边缘越限点无 Q 调节记录",
        fix="缩小死区至合格范围的 60~80%（0.3~0.4 kV），或对齐死区=合格范围",
        check_time_minutes=3,
    ),
    FaultDiagnosis(
        category=FaultCategory.NTP_OFFSET,
        root_cause="EMS 时间与调度 DMS 偏差 >5s，同一越限点被调度记了两次",
        evidence="调度合格率报表中 23:14:58 和 23:15:02 各扣一次 → 实际只越限一次",
        fix="NTP 强制同步，偏差 ≤1s；手动校时后重算本月数据",
        check_time_minutes=2,
    ),
    FaultDiagnosis(
        category=FaultCategory.SVG_LOCAL_OVERRIDE,
        root_cause="SVG 本地模式独立控制电压，EMS 不知道 SVG 在发/吸 Q → 总 Q 失控",
        evidence="EMS 记录 Q_PCS=−2000，但关口表显示总 Q=−8000 → 差 6000 来自 SVG",
        fix="SVG 切换为远方模式，由 EMS 统一分配；EMS 增加 SVG 状态遥测量",
        check_time_minutes=3,
    ),
    FaultDiagnosis(
        category=FaultCategory.INTEGRAL_WINDUP,
        root_cause="电压持续偏高时积分负向饱和；电压反转偏低后积分排空滞后 → 长时间不响应",
        evidence="电压从偏高→偏低切换后，Q 符号反转滞后 60~120s",
        fix="加积分冻结逻辑：偏差归零时清零积分项；或加抗饱和反向复位",
        check_time_minutes=3,
    ),
    FaultDiagnosis(
        category=FaultCategory.PARAM_UPLOAD_BLOCK,
        root_cause="104 通道参数禁止上传位意外置位 → 调度以为 AVC 离线",
        evidence="调度侧投运率报表显示连续 3h AVC 未投运；EMS 自身日志 AVC 始终 RUNNING",
        fix="检查 104 点表 C_CS_NA_1 参数激活标志位，复位后确认调度侧上报恢复",
        check_time_minutes=4,
    ),
]


def diagnose(events: List[str]) -> List[FaultDiagnosis]:
    results = []
    events_lower = [e.lower() for e in events]
    for fault in DIAGNOSTIC_TREE:
        if any(keyword in " ".join(events_lower) for keyword in _keywords(fault.category)):
            results.append(fault)
    if not results:
        results.append(FaultDiagnosis(
            category=FaultCategory.DEADBAND_COMPLIANCE,
            root_cause="未知原因——从死区合规性开始排查",
            evidence="未匹配已知五类误区的诊断特征",
            fix="逐项检查：1)死区 vs 合格范围 2)NTP 同步 3)SVG 模式 4)PI 积分 5)104 参数上传",
            check_time_minutes=15,
        ))
    return results


def _keywords(category: FaultCategory) -> list:
    return {
        FaultCategory.DEADBAND_COMPLIANCE: ["死区", "deadband", "合格范围", "vqr", "合格率", "不动作"],
        FaultCategory.NTP_OFFSET: ["ntp", "时间", "对时", "偏差", "重复扣"],
        FaultCategory.SVG_LOCAL_OVERRIDE: ["svg", "本地", "远方", "抢控", "差", "不一致"],
        FaultCategory.INTEGRAL_WINDUP: ["积分", "饱和", "滞后", "符号", "反转", "integral"],
        FaultCategory.PARAM_UPLOAD_BLOCK: ["104", "上传", "禁止", "激活", "离线", "投运率"],
    }.get(category, ["unknown"])
# @AI_GENERATED: end