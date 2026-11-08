# @AI_GENERATED
"""一致性测试：AVC 状态机 — 正文 06 章逐拍追踪验证"""
from lab.ems_lab.avc_state_machine import AVCStateMachine


def test_initial_stanby():
    sm = AVCStateMachine()
    assert sm.state == "STANDBY"


def test_stanby_to_running():
    sm = AVCStateMachine()
    assert sm.dispatch("avc_start") == "RUNNING"


def test_running_to_freeze():
    sm = AVCStateMachine()
    sm.dispatch("avc_start")
    for _ in range(5):
        sm.dispatch("comm_loss")
    assert sm.state == "FREEZE"


def test_freeze_to_running():
    sm = AVCStateMachine()
    sm.dispatch("avc_start")
    for _ in range(5):
        sm.dispatch("comm_loss")
    assert sm.state == "FREEZE"
    assert sm.dispatch("comm_restored") == "RUNNING"


def test_q_freeze_hold():
    sm = AVCStateMachine()
    sm.dispatch("avc_start")
    sm.get_q_output(-8000.0)
    for _ in range(5):
        sm.dispatch("comm_loss")
    assert sm.get_q_output(-3000.0) == -8000.0


def test_blocked_to_stanby():
    sm = AVCStateMachine()
    sm.dispatch("protection_trip")
    assert sm.state == "BLOCKED"
    sm.dispatch("manual_reset")
    assert sm.state == "STANDBY"
# @AI_GENERATED: end