# @AI_GENERATED
"""ch01 ACE 与 TBC/FFC/FTC 控制模式 lab。

全篇唯一业务对象：华东某 100 MW / 200 MWh 储能电站（PN=100 MW）。
唯一业务事件：某日上午 11:00 邻省一台 600 MW 机组跳闸。

    本区联络线被迫向邻省多送 ΔP_tie = +50 MW（送出为正）
    系统频率跌至 49.90 Hz，Δf = -0.10 Hz
    ACE = ΔP_tie + B×Δf = +50 + 1000×(-0.10) = -50 MW → 需增出力

同一事件下三种控制模式给出的控制量：
    FFC（只看频率）    = B×Δf = -100 MW（量偏大）
    FTC（只看联络线）  = ΔP_tie = +50 MW（方向错）
    TBC（频率+联络线） = -50 MW（正确）

省调按 TBC 得到 ACE = -50 MW，向本储能电站下发 AGC「上调 50 MW」指令——
这正是本课程业务对象（100 MW / 200 MWh 储能电站）每次 AGC 指令的源头。

运行方式: python lab/examples/ch01_ace.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ems_lab.agc_core import ace, PN  # noqa: E402

# 区域频率偏差系数 B（教学示例，正文 01 章）
B = 1000.0  # MW/Hz

# ── 全篇唯一业务事件：邻省机组跳闸 ─────────────────────
EVENT = {
    "name": "邻省 600 MW 机组跳闸",
    "dp_tie_mw": 50.0,   # 本区联络线被迫多送（送出为正）
    "df_hz": -0.10,      # 系统频率跌到 49.90 Hz（Δf = f - 50）
}


def control_quantities(dp_tie: float, df: float) -> dict:
    """同一事件下三种控制模式的控制量（正文 01 章「三种控制模式」）。"""
    return {
        "FFC（只看频率）": B * df,
        "FTC（只看联络线）": dp_tie,
        "TBC（频率+联络线）": ace(dp_tie, B, df),
    }


def test():
    dp_tie, df = EVENT["dp_tie_mw"], EVENT["df_hz"]
    # ACE 分量手算：+50 + 1000×(-0.10) = -50
    assert ace(dp_tie, B, df) == -50.0, "ACE 应等于 -50 MW"
    # 三模式对比：TBC 正确、FTC 方向错、FFC 量偏大
    q = control_quantities(dp_tie, df)
    assert q["TBC（频率+联络线）"] == -50.0, "TBC 应增出力"
    assert q["FTC（只看联络线）"] == 50.0, "FTC 只看联络线，方向会错"
    assert q["FFC（只看频率）"] == -100.0, "FFC 只看频率，量会偏大"
    print("  ✓ ch01 ACE 手算自测通过")


def main():
    dp_tie, df = EVENT["dp_tie_mw"], EVENT["df_hz"]
    print("=" * 66)
    print(f"ch01 ACE = ΔP_tie + B×Δf（业务对象：{PN:.0f} MW / 200 MWh 储能电站）")
    print("=" * 66)

    print(f"\n【① 业务事件】{EVENT['name']}")
    print(f"  联络线偏差 ΔP_tie = {dp_tie:+.0f} MW（本区被迫向邻省多送，送出为正）")
    print(f"  频率偏差     Δf   = {df:+.2f} Hz（系统频率 49.90 Hz）")

    print("\n【② ACE 手算】")
    b_df = B * df
    ace_val = ace(dp_tie, B, df)
    print(f"  ACE = ΔP_tie + B×Δf = {dp_tie:+.0f} + {B:.0f}×({df:+.2f})")
    print(f"      = {dp_tie:+.0f} + ({b_df:+.0f}) = {ace_val:+.0f} MW")
    print(f"  → ACE < 0，本区缺电，需「增出力」{abs(ace_val):.0f} MW")

    print("\n【③ 同一事件下三种控制模式的控制量】")
    for mode, val in control_quantities(dp_tie, df).items():
        action = "增出力" if val < 0 else "减出力"
        flag = "  ← 方向错误！" if mode.startswith("FTC") else ""
        print(f"  {mode:<16} {val:>8.1f} MW  → {action}{flag}")

    print("\n【④ 结论 → 落到业务对象】")
    print(f"  省调按 TBC 得到 ACE = -50 MW，向本储能电站下发 AGC「上调 {abs(ace_val):.0f} MW」指令；")
    print("  若误用 FTC，会得到 +50 MW 的「下调」指令，反而加剧缺电。")
    print(f"  这就是本课程业务对象（{PN:.0f} MW / 200 MWh 储能电站）每次 AGC 指令的源头。")


if __name__ == "__main__":
    test()
    main()