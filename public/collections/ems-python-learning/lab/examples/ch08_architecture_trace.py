"""第 08 章最小闭环：延迟预算与主备 fencing。

输入：各通信/处理/执行环节的教学示例延迟、主备切换前状态
算法：逐段求和；新主从实测功率和连续序号恢复；旧序号拒绝
输出：端到端延迟、切换后的第一条有效命令
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.pipeline import MockPcs, PowerCommand  # noqa: E402


def main():
    hops_ms = {"远动转发": 50, "EMS 等待周期": 1000, "EMS 计算": 50,
               "通信管理机排队": 200, "PCS 接收": 20, "功率爬升": 300}
    total_ms = sum(hops_ms.values())
    print(f"EMS 路径延迟：{total_ms} ms")
    assert total_ms == 1620

    pcs = MockPcs(1000)
    pcs.last_seq = 5000
    pcs.p_actual_kw = 80.0
    new_cmd = PowerCommand(5001, 1, 80.0, created_at=0, expires_at=2, reason="备机恢复")
    assert pcs.apply(new_cmd, 0.1).accepted
    old_cmd = PowerCommand(5000, 1, 30.0, created_at=0, expires_at=2, reason="旧主复活")
    old_ack = pcs.apply(old_cmd, 0.2)
    print(f"切换第一条：seq={new_cmd.seq}，功率={new_cmd.target_kw:.0f} kW，接受={True}")
    print(f"旧主指令：seq={old_cmd.seq}，接受={old_ack.accepted}，原因={old_ack.note}")
    assert not old_ack.accepted
    print("自检通过")


if __name__ == "__main__":
    main()

