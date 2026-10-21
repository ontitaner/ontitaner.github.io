# @AI_GENERATED
"""第 07 章配图：放电/充电效率链瀑布图、方向核对试验。

数值由 lab/ems_lab/site.py 计算，效率均为 [教学示例]。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, IMG_DIR, plt, save
from ems_lab.site import Stage, chain_from_dc, chain_from_grid, check_direction

CHAIN = [Stage("PCS", 0.98, 0.975), Stage("变压器", 0.99)]


def manifest(name: str, numbers: list[float]) -> None:
    """为正文图中标注对照表输出数字清单。"""
    payload = {
        "_comment": "@AI_GENERATED",
        "figure": f"{name}.png",
        "numbers": sorted(set(float(n) for n in numbers)),
        "_comment_end": "@AI_GENERATED: end",
    }
    (IMG_DIR / f"{name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _waterfall(ax, labels, levels, losses, color, title):
    """levels：各测量平面的功率幅值；losses：相邻平面之间的损耗。按“平面-损耗-平面……”交替画柱。"""
    xs, x = [], 0
    for i, lv in enumerate(levels):
        ax.bar(x, lv, color=color, width=0.62)
        ax.text(x, lv + 2, f"{lv:.2f}".rstrip("0").rstrip("."), ha="center", va="bottom", fontsize=10, fontweight="bold")
        xs.append((x, labels[2 * i]))
        x += 1
        if i < len(losses):
            top = lv
            ax.bar(x, -losses[i], bottom=top, color=C_LIMIT, alpha=0.75, width=0.62)
            ax.text(x, top + 2, f"−{losses[i]:.2f}".rstrip("0").rstrip("."), ha="center", va="bottom",
                    color=C_LIMIT, fontsize=10)
            ax.plot([x - 1 + 0.31, x - 0.31], [top, top], color=C_GRID, lw=0.8, ls=":")
            ax.plot([x + 0.31, x + 1 - 0.31], [top - losses[i]] * 2, color=C_GRID, lw=0.8, ls=":")
            xs.append((x, labels[2 * i + 1]))
            x += 1
    ax.set_xticks([p for p, _ in xs])
    ax.set_xticklabels([s for _, s in xs], fontsize=9)
    ax.set_ylim(900, 1020)
    ax.set_ylabel("功率幅值 (kW)，纵轴从 900 起")
    ax.set_title(title, loc="left", fontsize=10.5)


def fig_efficiency_chain():
    dis = chain_from_dc(1000, CHAIN)
    chg = chain_from_grid(-1000, CHAIN)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    _waterfall(
        axes[0],
        ["① 电池直流侧", "PCS 损耗\n(η放=98%)", "② PCS 交流侧", "变压器损耗\n(η=99%)", "③ 并网侧"],
        dis.powers_kw,
        dis.losses_kw,
        C_DIS,
        "放电：直流 1000 kW → 到并网侧剩 970.2 kW",
    )
    # 充电方向功率从电网流向电池，画图时按“电网 → 电池”的顺序排列幅值
    levels = [abs(p) for p in reversed(chg.powers_kw)]
    losses = list(reversed(chg.losses_kw))
    _waterfall(
        axes[1],
        ["③ 并网侧", "变压器损耗\n(η=99%)", "② PCS 交流侧", "PCS 损耗\n(η充=97.5%)", "① 电池直流侧"],
        levels,
        losses,
        C_CHG,
        "充电：从电网取 1000 kW → 进电池 965.25 kW",
    )
    fig.suptitle("同一条功率链，两个方向的损耗都“吃掉”功率：放电时并网侧变少，充电时电池侧变少  [教学示例效率]",
                 y=1.02, fontsize=11)
    save(fig, "ch07_efficiency_chain")
    manifest("ch07_efficiency_chain", [9.8, 10, 20, 24.75, 965.25, 970.2, 980, 990, 1000])


def fig_direction_test():
    t = np.arange(0, 181, 1.0)
    step = np.where((t >= 60) & (t < 120), 100.0, 0.0)  # 储能放电从 0 → +100 kW → 0
    base_pcc = -300.0  # 试验前站点从电网取电 300 kW（控制层方向）
    loss_ratio = 0.97  # 途经变压器、线路的损耗，使并网点变化略小于 100
    correct = base_pcc + step * loss_ratio
    reversed_dir = -correct  # “进口为正”的电表在接入层没有取反：取电看成送电，放电时读数反而下降
    wrong_ct = (base_pcc + step * loss_ratio) * 200 / 300  # CT 变比配错：整体缩小为 2/3

    fig, axes = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True, gridspec_kw={"height_ratios": [1, 2]})
    axes[0].step(t, step, where="post", color=C_DIS, lw=2.2)
    axes[0].set_ylabel("储能指令\nP_BESS (kW)")
    axes[0].set_ylim(-15, 130)
    axes[0].set_title("方向核对试验：储能小功率阶跃放电，看每个测点往哪边变、变多少", loc="left")
    axes[0].text(62, 108, "+100 kW 放电，保持 60 s", fontsize=9)

    cases = [
        (correct, C_OK, "正确：P_PCC 增加约 97"),
        (reversed_dir, C_LIMIT, "方向反了：取电被读成送电，放电时读数反而减少"),
        (wrong_ct, C_ACC, "CT 变比配错：变化只有约 65"),
    ]
    for y, c, label in cases:
        verdict = check_direction(100 * loss_ratio, y[90] - y[30], tol_ratio=0.2)
        axes[1].step(t, y, where="post", color=c, lw=2.2, label=f"{label}  → 判定：{verdict[:4]}")
    axes[1].axhline(0, color="k", lw=0.8)
    axes[1].text(2, -330, "试验前基线 −300 kW；CT 错配比例 2/3", fontsize=8.5)
    axes[1].set_ylabel("并网点 P_PCC (kW)\n向电网送电为正")
    axes[1].set_xlabel("时间 (s)")
    axes[1].set_ylim(-360, 360)
    axes[1].legend(loc="center right", fontsize=8.8, bbox_to_anchor=(1, 0.55))
    save(fig, "ch07_direction_test")
    manifest("ch07_direction_test", [-300, 2, 3, 60, 65, 97, 100])


def main():
    fig_efficiency_chain()
    fig_direction_test()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
