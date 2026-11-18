#!/usr/bin/env python3
"""P1 + P2 fixes: ch03 unification, ch06 tracking table, ch08 note, section naming"""

import os

BASE = r'd:\ontitaner\ai-practice\sub_module\ontitaner.github.io\public\collections\ems-primary-frequency-regulation'

# ═══════════════════════════════════════════
# P1-1: ch03 — unify project reference
# ═══════════════════════════════════════════
for f in sorted(os.listdir(BASE)):
    if f.startswith('03'):
        path = os.path.join(BASE, f)
        with open(path, 'r', encoding='utf-8') as fh:
            c = fh.read()

        old = '你的项目是内蒙古一个 100 MW 风光储一体化场站（60 MW 光伏 + 40 MW 风电），一次调频功能刚完成部署。'
        new = '同一座华东 100 MW 储能电站还配套了 60 MW 光伏和 40 MW 风电——也就是说，一次调频要同时管三个资源。'
        c = c.replace(old, new)
        print('ch03 project ref:', 'changed' if new in c else 'FAILED')

        old2 = '### 储能放在哪个位置【必懂】'
        new2 = '### 储能在一次调频中的定位与角色【必懂】'
        c = c.replace(old2, new2)
        print('ch03 section rename:', 'changed' if new2 in c else 'FAILED')

        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(c)
        break

# ═══════════════════════════════════════════
# P1-2: ch06 — add numerical tracking table after code
# ═══════════════════════════════════════════
for f in sorted(os.listdir(BASE)):
    if f.startswith('06'):
        path = os.path.join(BASE, f)
        with open(path, 'r', encoding='utf-8') as fh:
            c = fh.read()

        # Find the target: after "三个实现细节" section, or after the code block at "return max(-down, min(delta_p, up))"
        old = (
            '    up, down = capability_window(p_now_mw, cfg, p_max_mw)\n'
            '    return max(-down, min(delta_p, up))\n'
            '```\n\n'
            '### 三个实现细节【必懂】'
        )
        if old in c:
            tracking = (
                '    up, down = capability_window(p_now_mw, cfg, p_max_mw)\n'
                '    return max(-down, min(delta_p, up))\n'
                '```\n\n'
                '### 数值跟踪：用贯穿式案例逐行验证【必懂】\n\n'
                '取贯穿式教学案例的参数 —— `Pn = 100 MW`、`δ = 3%`、死区 `±0.06 Hz`（截断型）、限幅 `±20 MW`、当前出力 `P_now = 30 MW`、可调上限 `P_max = 100 MW` —— 当 `f = 49.90 Hz` 时，下面是 `primary_freq_delta()` 每一步的中间值：\n\n'
                '| 步骤 | 变量 | 计算/值 | 说明 |\n'
                '|---|---|---|---|\n'
                '| ① 输入 | `f_hz` | 49.90 Hz | 实测电网频率 |\n'
                '| ② Δf 原始 | `delta_f` | 49.90 − 50.00 = −0.10 Hz | 频率偏差 |\n'
                '| ③ 死区裁剪 | `effective` | −0.10 Hz | 截断型：|Δf|>0.06，不削减 |\n'
                '| ④ K 计算 | `k` | 100/(0.03×50) = 66.67 MW/Hz | 下垂系数 |\n'
                '| ⑤ ΔP（取反） | `delta_p` | −66.67 × (−0.10) = +6.667 MW | 频率低→放电为正 |\n'
                '| ⑥ 限幅裁剪 | `delta_p` | max(−20, min(+6.667, +20)) = +6.667 MW | 未触及 ±20 MW 限幅 |\n'
                '| ⑦ 能力校验 | `up` | min(100−30, 20) = 20 MW | 可上调空间充足 |\n'
                '|  | `down` | min(30−10, 20) = 20 MW | 可下调空间充足 |\n'
                '| ⑧ 最终输出 | `result` | max(−20, min(+6.667, +20)) = **+6.667 MW** | 理论值 = 可执行值 |\n\n'
                '> **为什么记录两步值**：ΔP_theory = +6.667 MW（限幅后），ΔP_exec = +6.667 MW（能力校验后）。二者相等说明当前条件下没有物理限制。如果 P_now = 95 MW，则 up = min(5, 20) = 5 MW，ΔP_exec 会被裁剪到 5 MW——此时考核系统按理论值 6.667 MW 算，而实际只出了 5 MW，完成率骤降到 75%。这就是为什么 ch07 反复强调"只记录最终值无法证明算法正确"。\n\n'
                '### 三个实现细节【必懂】'
            )
            c = c.replace(old, tracking)
            print('[OK] ch06 numerical tracking table added')
        else:
            print('[FAIL] ch06: code ending not found')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(c)
        break

# ═══════════════════════════════════════════
# P1-3: ch08 — add deadband type consistency note
# ═══════════════════════════════════════════
for f in sorted(os.listdir(BASE)):
    if f.startswith('08'):
        path = os.path.join(BASE, f)
        with open(path, 'r', encoding='utf-8') as fh:
            c = fh.read()

        old = '以光伏 `Pn = 100 MW`、`δ = 3%`、死区 `±0.06 Hz`（截断型）、限幅 `±10 MW` 为例 `[教学示例]`：'
        new = '以光伏 `Pn = 100 MW`、`δ = 3%`、死区 `±0.06 Hz`（截断型——与 ch02 教学示例使用的连续型不同，此处特意切换为截断型以展示判据变化）、限幅 `±10 MW` 为例 `[教学示例]`：'
        c = c.replace(old, new)
        print('ch08 deadband note:', 'changed' if new in c else 'FAILED')

        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(c)
        break

# ═══════════════════════════════════════════
# P2: section naming fixes
# ═══════════════════════════════════════════

# P2-1: ch04 — fix ①②/③⑤ labels
for f in sorted(os.listdir(BASE)):
    if f.startswith('04'):
        path = os.path.join(BASE, f)
        with open(path, 'r', encoding='utf-8') as fh:
            c = fh.read()
        c = c.replace('## 指标①②：精度类【必懂】', '## 测频精度与调频控制偏差（指标①②）【必懂】')
        c = c.replace('## 指标③⑤：周期类【必懂】', '## 采样周期与控制周期（指标③⑤）【必懂】')
        c = c.replace('## 深入：频率动态的闭环视角【深入了解】', '## 频率动态的闭环视角【深入】')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(c)
        print('[OK] ch04 section labels fixed')
        break

# P2-2: ch02 — remove redundant 深入 prefix & downgrade RoCoF
for f in sorted(os.listdir(BASE)):
    if f.startswith('02'):
        path = os.path.join(BASE, f)
        with open(path, 'r', encoding='utf-8') as fh:
            c = fh.read()
        c = c.replace('### 频率变化率（RoCoF）死区【必懂】', '### 频率变化率（RoCoF）死区【参考】')
        c = c.replace('### 深入：死区与限幅的交互【深入】', '### 死区与限幅的交互【深入】')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(c)
        print('[OK] ch02 section labels fixed')
        break

# P2-3: ch01 — fix title
for f in sorted(os.listdir(BASE)):
    if f.startswith('01'):
        path = os.path.join(BASE, f)
        with open(path, 'r', encoding='utf-8') as fh:
            c = fh.read()
        c = c.replace(
            '# 01 一次调频的业务背景与标准沿革',
            '# 01 一次调频的功能定位与调控原理'
        )
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(c)
        print('[OK] ch01 title fixed')
        break

print('\nDone - P1+P2 edits complete.')