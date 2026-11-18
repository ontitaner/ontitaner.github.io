# @AI_GENERATED
"""AVC 状态机（IEC104 链路驱动）

对应章节：06 IEC104链路与状态机

五种状态（对齐 06.3）：
  STANDBY → RUNNING → FREEZE → BLOCKED → OFFLINE

典型转换路径（对齐 06.3 逐拍追踪）：
  就绪─(AVC投入)─→调控─(通信连续超时)─→冻结─(通信恢复)─→调控
                                              └─(保护动作)─→闭锁─(人工复位)─→就绪
"""
from __future__ import annotations
from typing import Dict, Optional, Callable

TRANSITIONS: Dict[tuple, str] = {
    ("STANDBY", "avc_start"):       "RUNNING",
    ("STANDBY", "protection_trip"): "BLOCKED",
    ("RUNNING", "avc_exit"):        "STANDBY",
    ("RUNNING", "comm_loss"):       "FREEZE",
    ("RUNNING", "quality_invalid"): "FREEZE",
    ("RUNNING", "protection_trip"): "BLOCKED",
    ("RUNNING", "manual_block"):    "BLOCKED",
    ("FREEZE", "comm_restored"):    "RUNNING",
    ("FREEZE", "protection_trip"):  "BLOCKED",
    ("BLOCKED", "manual_reset"):    "STANDBY",
}


class AVCStateMachine:
    def __init__(
        self,
        comm_timeout_limit: int = 3,
        quality_timeout_limit: int = 3,
    ):
        self.state = "STANDBY"
        self.comm_timeout_count = 0
        self.quality_timeout_count = 0
        self.comm_timeout_limit = comm_timeout_limit
        self.quality_timeout_limit = quality_timeout_limit
        self.freeze_q_kvar: float = 0.0
        self._handlers: Dict[str, Callable] = {}

    def dispatch(self, event: str, context: Optional[dict] = None) -> str:
        handler = self._handlers.get((self.state, event))
        if handler:
            return handler(context or {})

        next_state = TRANSITIONS.get((self.state, event))
        if next_state is None:
            return self.state

        if event == "comm_loss":
            self.comm_timeout_count += 1
            if self.comm_timeout_count > self.comm_timeout_limit:
                self.state = next_state
            return self.state

        if event == "quality_invalid":
            self.quality_timeout_count += 1
            if self.quality_timeout_count > self.quality_timeout_limit:
                self.state = next_state
            return self.state

        if event == "comm_restored":
            self.comm_timeout_count = 0
            self.quality_timeout_count = 0
            self.state = next_state
            return self.state

        self.state = next_state

        if next_state == "STANDBY":
            self.comm_timeout_count = 0
            self.quality_timeout_count = 0

        return self.state

    def get_q_output(self, q_current_kvar: float) -> float:
        if self.state == "RUNNING":
            self.freeze_q_kvar = q_current_kvar
            return q_current_kvar
        elif self.state == "FREEZE":
            return self.freeze_q_kvar
        else:
            return 0.0
# @AI_GENERATED: end