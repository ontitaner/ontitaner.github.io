<!-- @AI_GENERATED -->
# 20 可用能量 SOE 估计

**一句话**：SOE 回答"在指定测量平面还剩多少 kWh"。它要扣估计余量和最低簇差，再乘有效容量和路径效率，而不是直接用 SOC 乘额定能量。

## 20.1 运行场景

17:30，状态估计和在线诊断已完成。EMS 得到 SOC=30%、估计余量 3%、最低簇差 2%、容量 SOH=92%，并确认当前数据质量可用于能力计算。调度任务要求 18:00–18:30 在 PCC 交付能量，值班员需要把这些状态量转换成交流侧可用 kWh。

若直接用 30% 乘 5.016 MWh，得到的名义余量几乎刚好覆盖 1 MWh 目标；但这个数还没有扣最低簇、运行下限、容量衰减和 DC→AC 损耗。任务能否执行取决于保守口径下的能量，而不是堆级点值。

## 20.2 关键术语

- **SOE（State of Energy）**：当前运行窗口内可用能量，以 kWh 或比例表示。
- **估计余量 `m_est`**：由 `k_risk·σ_SOC` 风险口径得到的 SOC 保守扣减。
- **最低簇差 `ΔSOC_cluster`**：最低簇相对站级估计的保守差值。

## 20.3 决策困难与算法需求

17:30 的状态数据已经齐备：SOC=30%、估计余量 3%、最低簇差 2%、容量 SOH=92%。但 SOC 是电荷比例，调度要求的是交流侧 kWh。在中间隔着有效容量、运行窗口、簇差不均和 DC→AC 效率的情况下，把点值 SOC 直接用于功率计划，会把可用能量高估到恰好覆盖 1 MWh——而实际上 644.4 kWh 才是保守结果。

因此需要 SOE 估计：把 SOC 下界（扣除估计余量和簇差后）、有效能量和路径效率放进同一条公式。SOE 的输出为 30 min SOP 计算提供能量约束——如果能量都不够，设备限值和并网限值再高也没用。

## 20.4 SOE 公式

```text
SOC_low = max(0, SOC − m_est − ΔSOC_cluster)
E_eff = C_site × SOH_capacity
SOE_AC = max(0, SOC_low − SOC_min) × E_eff × η_DC→AC
```

| 变量 | 含义 |
|---|---|
| `m_est` | 估计风险余量，单位 SOC |
| `ΔSOC_cluster` | 最低簇差，单位 SOC |
| `E_eff` | 有效站级能量，单位 kWh |
| `η_DC→AC` | 直流到交流效率，只乘一次 |
| `SOC_min` | 放电运行下限 |

## 20.5 手算示例

统一站：`C_site=5015.96 kWh`、`SOC=30%`、`m_est=3%`、`ΔSOC_cluster=2%`、`SOH=92%`、`SOC_min=10%`、`η=0.931`。

**第 1 步：收窄 SOC 并计算站级有效能量。**

```text
SOC_low = 30% − 3% − 2% = 25%
E_eff = 5015.96 × 0.92 = 4614.68 kWh
```

**第 2 步：转换为交流侧 SOE。**

```text
SOE_AC = (25% − 10%) × 4614.68 × 0.931 = 644.44 kWh ≈ 644.4 kWh
```

这 644.4 kWh 已是交流侧、放电方向、到 10% 下限的保守能量，不能再次乘效率。后续功率换算保留未取整值 `644.44 kWh`，以免四舍五入在除法后放大。

## 20.6 核心实现

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SoeResult:
    conservative_soc: float
    effective_energy_kwh: float
    soe_ac_kwh: float


def available_energy(soc: float, estimate_margin: float, cluster_gap: float,
                     nominal_energy_kwh: float = 5015.96,
                     capacity_soh: float = 0.92, minimum_soc: float = 0.10,
                     dc_to_ac_efficiency: float = 0.931) -> SoeResult:
    """计算放电方向、交流侧口径的保守 SOE。"""
    if not 0.0 <= soc <= 1.0 or estimate_margin < 0 or cluster_gap < 0:
        raise ValueError("SOC 与余量必须有效")
    if not 0.0 < capacity_soh <= 1.0 or not 0.0 <= minimum_soc < 1.0:
        raise ValueError("SOH 或运行下限无效")
    if not 0.0 < dc_to_ac_efficiency <= 1.0:
        raise ValueError("效率必须在 0–1")

    conservative_soc = max(0.0, soc - estimate_margin - cluster_gap)
    effective_energy_kwh = nominal_energy_kwh * capacity_soh
    soe_ac_kwh = max(0.0, conservative_soc - minimum_soc) * effective_energy_kwh * dc_to_ac_efficiency
    return SoeResult(conservative_soc, effective_energy_kwh, soe_ac_kwh)


if __name__ == "__main__":
    result = available_energy(0.30, 0.03, 0.02)
    print(f"保守 SOC={result.conservative_soc:.0%}")
    print(f"有效容量={result.effective_energy_kwh:.1f} kWh")
    print(f"交流侧 SOE={result.soe_ac_kwh:.1f} kWh")
    assert round(result.soe_ac_kwh, 1) == 644.4
```

## 20.7 诊断状态

| 诊断状态 | SOE 动作 |
|---|---|
| `normal` | 使用已记录的 `m_est` |
| `degraded` | 放大 `m_est`，SOE 更保守 |
| `invalid` | 不发布新的 SOE，等待新鲜数据 |

## 20.8 自测

1. 为什么 SOE 必须写明交流侧还是直流侧？
2. SOC 直接乘额定能量会漏掉哪些因素？
3. `degraded` 状态下 SOE 会更大还是更小？

<details>
<summary>参考答案</summary>

1. 效率依附测量平面；不写平面会重复或遗漏损耗。
2. 漏掉估计余量、最低簇差、运行下限、容量 SOH 和 DC→AC 效率。
3. 更小；估计余量放大后，保守 SOC 与 SOE 都下降。

</details>

<!-- @AI_GENERATED: end -->