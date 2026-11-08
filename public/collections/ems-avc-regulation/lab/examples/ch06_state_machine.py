# @AI_GENERATED
"""ch06 示例：IEC104 链路驱动 AVC 状态机 —— 5 状态跳转演练

主线场景：50MW/100MWh 储能电站，EMS 通过 104 通道上行调度
"""
from lab.ems_lab.avc_state_machine import AVCStateMachine


def main():
    print("AVC 状态机：IEC104 链路驱动  [主线: 50MW 储能电站 EMS]\n")

    sm = AVCStateMachine(comm_timeout_limit=3, quality_timeout_limit=3)

    events = [
        ("avc_start", "调度下发 AVC 投入令"),
        ("comm_loss", "104 通道第一拍超时"),
        ("comm_loss", "104 通道第二拍超时"),
        ("comm_loss", "104 通道第三拍超时"),
        ("comm_loss", "104 通道第四拍超时 → 触发 FREEZE"),
        ("comm_restored", "104 通道恢复 → 返回 RUNNING"),
        ("protection_trip", "保护动作跳闸 → BLOCKED"),
        ("manual_reset", "人工复位 → STANDBY"),
    ]

    for evt, desc in events:
        prev = sm.state
        new_state = sm.dispatch(evt)
        arrow = "→" if prev != new_state else "—"
        print(f"  {prev:8s} {arrow} [{evt:15s}] {arrow} {new_state:8s}   ({desc})")

    print(f"\n  终态: {sm.state}")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end